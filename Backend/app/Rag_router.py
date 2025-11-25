import os
import json
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
import json
from fpdf import FPDF

load_dotenv()

router = APIRouter(prefix="/rag", tags=["RAG Gemini MCQ"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = "./chroma"
COLLECTION_NAME = "exame_docs"

GEMINI_KEY = os.getenv("GOOGLE_GEMINI_KEY")
if not GEMINI_KEY:
    raise ValueError("GOOGLE_GEMINI_KEY não encontrada no arquivo .env")

os.environ["GOOGLE_API_KEY"] = GEMINI_KEY
genai.configure(api_key=GEMINI_KEY)
genai_model = genai.GenerativeModel("gemini-2.5-flash")

# Configuração de embeddings e banco vetorial
embedding_function = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    api_key=GEMINI_KEY
)

try:
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_function,
        collection_name=COLLECTION_NAME
    )
except Exception as e:
    print(f"⚠️ Erro ao carregar banco vetorial: {e}")
    db = None

# Funções auxiliares
def format_docs(docs):
    """Formata documentos recuperados do banco vetorial."""
    return "\n\n".join([
        f"Fonte: {doc.metadata.get('source', 'Desconhecida')}\nConteúdo: {doc.page_content}"
        for doc in docs
    ])

def get_gemini_response(prompt: str, temperature: float = 0.5):
    """Gera resposta textual com o modelo Gemini."""
    try:
        response = genai_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )
        return response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resposta: {str(e)}")

def substituir_caracteres_unicode(texto):
    """Substitui caracteres Unicode por equivalentes ASCII"""
    substituicoes = {
        '≤': '<=', '≥': '>=', '≠': '!=', '≈': '≈',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
        'ã': 'a', 'õ': 'o', 'ç': 'c', 'ü': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'À': 'A', 'È': 'E', 'Ì': 'I', 'Ò': 'O', 'Ù': 'U',
        'Â': 'A', 'Ê': 'E', 'Î': 'I', 'Ô': 'O', 'Û': 'U',
        'Ã': 'A', 'Õ': 'O', 'Ç': 'C', 'Ü': 'U'
    }
    
    for char, replacement in substituicoes.items():
        texto = texto.replace(char, replacement)
    
    return texto

def obter_letra_enumeração(indice):
    vogais = ['a', 'b', 'c', 'd']
    return vogais[indice % len(vogais)]

# Geração de questões de múltipla escolha (RAG)
def generate_mcq_from_context(context: str, topic: str, questions, qnt_questoes=2, temperature: float = 0.5):
    
    prompt = f"""
Você é especialista no(s) tema(s): {topic}.
Gere {qnt_questoes} questões de múltipla escolha com 4 alternativas (A, B, C, D), apenas uma correta.

Para cada alternativa:
- Indique se é correta ou incorreta.
- Explique detalhadamente POR QUE está correta ou incorreta.

⚠️ Responda apenas em JSON válido, no formato abaixo, sem texto adicional:
{{
    "question 1": {{
        "text": "Texto da questão",
        "options": [
            {{"option": "Alternativa 1", "is_correct": true, "explanation": "Explicação da correta"}},
            {{"option": "Alternativa 2", "is_correct": false, "explanation": "Explicação da incorreta"}},
            {{"option": "Alternativa 3", "is_correct": false, "explanation": "Explicação da incorreta"}},
            {{"option": "Alternativa 4", "is_correct": false, "explanation": "Explicação da incorreta"}}
        ],
        "resolution": "Resumo geral da resolução da questão"
    }}
}}

Use apenas as informações necessárias dos documentos para criar as questões e explicações.

Documentos:
{context}
"""
    response_text = get_gemini_response(prompt, temperature)

    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        json_text = response_text[start:end]
        mcq = json.loads(json_text)

        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        QUESTIONS_PATH = os.path.join(CURRENT_DIR, "questions.json")


        with open(QUESTIONS_PATH, "w", encoding="utf-8") as arquivo:
            json.dump(mcq, arquivo, ensure_ascii=False, indent=4)

        return mcq

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao decodificar JSON do Gemini: {str(e)}\nResposta bruta:\n{response_text}"
        )

def substitute_question(original_mcq: dict, question_number: str, topic: str, temperature: float = 0.5):
    """Substitui a questão escolhida por uma nova questão gerada."""
    
    if not db:
        raise HTTPException(status_code=500, detail="Banco vetorial não inicializado.")
    
    relevant_docs = db.similarity_search(topic, k=8)
    if not relevant_docs:
        raise HTTPException(status_code=404, detail="Nenhum documento relevante encontrado.")
    
    context = format_docs(relevant_docs)

    prompt = f"""
Você é especialista no tema: {topic}.

Gere uma NOVA questão de múltipla escolha para substituir a questão existente.
⚠️ A nova questão deve ser diferente das demais questões já geradas.

Questão atual que deve ser substituída:
{json.dumps(original_mcq.get(question_number, {}), ensure_ascii=False)}

Liste também as outras questões já existentes para evitar repetição:
{json.dumps(original_mcq, ensure_ascii=False)}

Formato OBRIGATÓRIO:
{{
    "{question_number}": {{
        "text": "...",
        "options": [
            {{"option": "...", "is_correct": true/false, "explanation": "..."}},
            {{"option": "...", "is_correct": true/false, "explanation": "..."}},
            {{"option": "...", "is_correct": true/false, "explanation": "..."}},
            {{"option": "...", "is_correct": true/false, "explanation": "..."}}
        ],
        "resolution": "..."
    }}
}}

Documentos:
{context}
"""

    response_text = get_gemini_response(prompt, temperature)

    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        json_text = response_text[start:end]
        new_question = json.loads(json_text)
    except:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao decodificar JSON da nova questão.\nResposta bruta:\n{response_text}"
        )
    
    # substitui somente a questão escolhida
    original_mcq[question_number] = new_question[question_number]

    return original_mcq

# Criação do pdf
def create_PDF(exame):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_auto_page_break(auto=True, margin=15)

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(CURRENT_DIR, "prova_ExamForge.pdf")

    for i, question_key in enumerate(exame.keys(), 1):
        question = exame[question_key]
        
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 0, 128)
        pdf.cell(0, 15, f"Questão {i}:", 0, 1)

        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        text = substituir_caracteres_unicode(question['text'])
        pdf.multi_cell(0, 8, text, 0, 1)
        pdf.ln(5)

        pdf.set_font("Arial", size=11)
        options = question['options']
        
        for j, option in enumerate(options):
            letra = obter_letra_enumeração(j)
            text = substituir_caracteres_unicode(option['option'])
            pdf.cell(10, 10, f"({letra})", 0, 0)
            pdf.multi_cell(0, 10, f" {text}", 0, 1)

        pdf.ln(10)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

    pdf.output(pdf_path)
    return pdf_path


# Modelos de requisição
class MCQRequest(BaseModel):
    topic: str
    qnt_questoes: int

class CheckAnswerRequest(BaseModel):
    question_data: dict  # JSON da questão gerada pelo /generate_mcq/
    chosen_option: str

class SubstituteQuestionRequest(BaseModel):
    original_mcq: dict
    question_number: str
    topic: str
    

# Endpoints
@router.post("/generate_mcq/")
def generate_mcq(data: MCQRequest):
    """Gera questões de múltipla escolha baseadas no tema informado."""
    if not db:
        return JSONResponse(status_code=500, content={"error": "Banco vetorial não inicializado."})

    relevant_docs = db.similarity_search(data.topic, k=8)
    if not relevant_docs:
        return JSONResponse(status_code=404, content={"error": "Nenhum documento relevante encontrado."})

    context = format_docs(relevant_docs)
    questions = []
    mcq = generate_mcq_from_context(context, data.topic, questions, data.qnt_questoes, temperature=0.5)
    
    # Adiciona fontes ao JSON retornado
    mcq["sources"] = [doc.metadata.get("source", "Desconhecida") for doc in relevant_docs]
    return mcq

@router.post("/check_answer/")
def check_answer(data: CheckAnswerRequest):
    
    question_data = data.question_data
    chosen = data.chosen_option.strip()
    
    correct_option = None
    explanation_correct = ""
    explanation_chosen = ""

    # Procura a alternativa correta e a escolhida
    for opt in question_data.get("options", []):
        opt_text = opt["option"].strip()
        if opt.get("is_correct", False):
            correct_option = opt_text
            explanation_correct = opt.get("explanation", "Explicação não disponível.")
        if opt_text.lower() == chosen.lower():
            explanation_chosen = opt.get("explanation", "Explicação não disponível.")
    
    is_correct = chosen.lower() == (correct_option or "").lower()

    if is_correct:
        return {
            "is_correct": True,
            "chosen_option": chosen,
            "message": "✅ Está correto!",
            "explanation": explanation_chosen
        }
    else:
        return {
            "is_correct": False,
            "chosen_option": chosen,
            "message": "❌ Está incorreto.",
            "explanation_chosen": explanation_chosen,
            "correct_option": correct_option,
            "explanation_correct": explanation_correct
        }

@router.post("/substitute_question/")
def substitute_question_endpoint(data: SubstituteQuestionRequest):
    updated = substitute_question(
        original_mcq=data.original_mcq,
        question_number=data.question_number,
        topic=data.topic,

    )
    return updated

@router.post("/generate_PDF/")
async def generate_PDF():
    try:
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        QUESTIONS_PATH = os.path.join(CURRENT_DIR, "questions.json")


        if not os.path.exists(QUESTIONS_PATH):
            return {"status": "error", "message": "Arquivo questions.json não encontrado"}

        with open(QUESTIONS_PATH, "r", encoding="utf-8") as arquivo:
            exame = json.load(arquivo)

        result = create_PDF(exame)

        return {
            "status": "success",
            "message": "PDF gerado com sucesso",
            "file_path": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao gerar PDF: {str(e)}"
        }

@router.get("/status/")
def status():
    """Verifica status da coleção vetorial."""
    try:
        num_docs = len(db.get()['ids']) if db else 0
    except Exception:
        num_docs = 0

    return {
        "status": "ok",
        "docs": num_docs,
        "collection": COLLECTION_NAME,
        "model": "gemini-2.5-flash"
    }
