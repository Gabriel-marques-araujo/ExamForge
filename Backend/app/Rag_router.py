import os
import json
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai

load_dotenv()

router = APIRouter(prefix="/rag", tags=["RAG Gemini MCQ"])

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

# Geração de questões de múltipla escolha (RAG)
def generate_mcq_from_context(context: str, topic: str, qnt_questoes=2, temperature: float = 0.5):
    
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

    # Extrai JSON do texto retornado
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        json_text = response_text[start:end]
        mcq = json.loads(json_text)
        return mcq
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao decodificar JSON da resposta do Gemini: {str(e)}\nResposta bruta:\n{response_text}"
        )

# Modelos de requisição
class MCQRequest(BaseModel):
    topic: str
    qnt_questoes: int

class CheckAnswerRequest(BaseModel):
    question_data: dict  # JSON da questão gerada pelo /generate_mcq/
    chosen_option: str

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
    mcq = generate_mcq_from_context(context, data.topic, data.qnt_questoes, temperature=0.5)
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
