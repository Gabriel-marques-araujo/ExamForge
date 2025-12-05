import os
import json
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI
from fpdf import FPDF
from fastapi.responses import FileResponse

load_dotenv()

router = APIRouter(prefix="/rag", tags=["RAG Gemini MCQ"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = "./chroma"
COLLECTION_NAME = "exame_docs"

GEMINI_KEY = os.getenv("GOOGLE_GEMINI_KEY")
if not GEMINI_KEY:
    raise ValueError("GOOGLE_GEMINI_KEY não encontrada no arquivo .env")

os.environ["GOOGLE_API_KEY"] = GEMINI_KEY

chat_model = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    temperature = 0.5,
    api_key=GEMINI_KEY
)

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

dict_questions={}

# Funções auxiliares
def format_docs(docs):
    """Formata documentos recuperados do banco vetorial."""
    return "\n\n".join([
        f"Fonte: {doc.metadata.get('source', 'Desconhecida')}\nConteúdo: {doc.page_content}"
        for doc in docs
    ])

def get_gemini_response(prompt: str, temperature: float = 0.5):
    """Gera resposta textual com o modelo Gemini via LangChain ChatGoogleGenerativeAI."""
    try:
        if not isinstance(prompt, str):
            prompt = str(prompt)

        messages = [
            ("system", "Você é um assistente técnico especializado em gerar questões de múltipla escolha."),
            ("user", prompt)
        ]

        
        ai_msg = chat_model.invoke(messages, temperature=temperature)

        # Retorna apenas o conteúdo da resposta
        return ai_msg.content.strip()

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
def generate_mcq_from_context(context: str, topic: str, qnt_questoes: int = 2, temperature: float = 0.5):
    prompt = f"""
Você é um especialista altamente competente no(s) tema(s): {topic}.
Sua tarefa é gerar {qnt_questoes} questões de múltipla escolha de alta qualidade.

📘 **Uso do contexto**
- O contexto serve como apoio, não como limite.
- As questões devem ser baseadas nos documentos, mas utilizando toda a sua capacidade de linguagem para gerar perguntas profundas e relevantes sobre o tópico — sem se limitar a copiar ou depender literalmente de trechos dos documentos.
- Use os documentos apenas como referência conceitual.
- NÃO cite, mencione ou faça alusão a “documento”, “contexto”, “texto fornecido” ou variações.
- NÃO introduza temas que não estejam presentes nos documentos fornecidos.

🎯 **Regras de elaboração das questões**
- Cada questão deve ter exatamente 4 alternativas (A, B, C, D).
- Apenas UMA alternativa deve ser correta.
- Varia a posição da resposta correta de forma equilibrada.
- NÃO crie cenários fictícios, histórias ou situações inventadas.
- Os enunciados devem ser diretos, técnicos e objetivos.
- Cada alternativa deve conter explicação objetiva e técnica.

⚠️ **Formato obrigatório**
Responda APENAS com um JSON válido, sem qualquer texto fora do JSON, seguindo exatamente esta estrutura:

{{
    "question 1": {{
        "text": "Texto da questão",
        "options": [
            {{"option": "Alternativa 1", "is_correct": true, "explanation": "Explicação da correta"}},
            {{"option": "Alternativa 2", "is_correct": false, "explanation": "Explicação da incorreta"}},
            {{"option": "Alternativa 3", "is_correct": false, "explanation": "Explicação da incorreta"}},
            {{"option": "Alternativa 4", "is_correct": false, "explanation": "Explicação da incorreta"}}
        ],
        "resolution": "Resumo da resolução e raciocínio da questão"
    }}
}}

📚 **Documentos de apoio:**
{context}
"""

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

        # Atualiza dict_questions global
        global dict_questions
        dict_questions = {}
        for i, question_key in enumerate(mcq.keys(), 1):
            if question_key == "sources":
                continue

            question = mcq[question_key]
            correct_opt = None
            for opt in question.get("options", []):
                if opt.get("is_correct", False):
                    correct_opt = opt["option"]
                    break

            dict_questions[question_key] = {
                "text": question["text"],
                "correct_option": correct_opt,
                "chosen_option": "",
                "is_correct": False
            }

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
Você é um especialista altamente competente no tema: {topic}.

Sua tarefa é gerar uma NOVA questão de múltipla escolha de alta qualidade para substituir a questão existente, mantendo o mesmo padrão de profundidade e qualidade das demais questões.

⚠️ **REGRA CRÍTICA DE DIFERENCIAÇÃO**
- A nova questão deve ser DIFERENTE e ORIGINAL em relação a todas as questões já existentes.
- NÃO repita o mesmo tema, enfoque, estrutura ou abordagem das questões listadas abaixo.
- Crie uma questão sobre um aspecto diferente do tópico ou com um ângulo distinto de análise.

📘 **Uso do contexto**
- O contexto serve como apoio, não como limite.
- A questão deve ser baseada nos documentos, mas utilizando toda a sua capacidade de linguagem para gerar uma pergunta profunda e relevante sobre o tópico — sem se limitar a copiar ou depender literalmente de trechos dos documentos.
- Use os documentos apenas como referência conceitual.
- NÃO cite, mencione ou faça alusão a “documento”, “contexto”, “texto fornecido” ou variações.
- NÃO introduza temas que não estejam presentes nos documentos fornecidos.

🎯 **Regras de elaboração da questão**
- A questão deve ter exatamente 4 alternativas (A, B, C, D).
- Apenas UMA alternativa deve ser correta.
- Varia a posição da resposta correta em relação às outras questões (evite padrões previsíveis).
- NÃO crie cenários fictícios, histórias, personagens, empresas imaginárias ou situações inventadas.
- O enunciado deve ser direto, técnico e objetivo, sem contextualizações narrativas.
- Cada alternativa deve:
  - ser autossuficiente e específica;
  - indicar claramente se é correta ou incorreta;
  - conter explicação objetiva e técnica do motivo.
- A questão deve avaliar raciocínio, interpretação e aplicação prática — não apenas memorização.

⚠️ **Formato obrigatório**
Responda APENAS com um JSON válido, sem qualquer texto fora do JSON, seguindo exatamente esta estrutura:

{{
    "{question_number}": {{
        "text": "Texto da nova questão (deve ser completamente diferente da questão original e das outras existentes)",
        "options": [
            {{"option": "Alternativa 1", "is_correct": true/false, "explanation": "Explicação técnica objetiva"}},
            {{"option": "Alternativa 2", "is_correct": true/false, "explanation": "Explicação técnica objetiva"}},
            {{"option": "Alternativa 3", "is_correct": true/false, "explanation": "Explicação técnica objetiva"}},
            {{"option": "Alternativa 4", "is_correct": true/false, "explanation": "Explicação técnica objetiva"}}
        ],
        "resolution": "Resumo da resolução e raciocínio da questão, explicando por que a alternativa correta é a melhor e como as incorretas se desviam do conceito correto"
    }}
}}

📋 **QUESTÃO ORIGINAL (que será substituída):**
{json.dumps(original_mcq.get(question_number, {}), ensure_ascii=False, indent=2)}

📚 **OUTRAS QUESTÕES EXISTENTES (evite repetir temas/abordagens):**
{json.dumps({k: v for k, v in original_mcq.items() if k != question_number}, ensure_ascii=False, indent=2)}

📖 **Documentos de apoio para criar a NOVA questão:**
{context}

IMPORTANTE: A nova questão deve ser tão rica, complexa e bem fundamentada quanto as questões existentes, mas abordando um aspecto diferente do tópico ou utilizando um ângulo de análise distinto.
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

# Feedback final do simulado
def generate_feedback(dict_responses: dict, temperature: float = 0.5):

    prompt = f"""
Você é um avaliador educacional IA. Analise o desempenho do aluno no exame e gere um feedback claro, direto e bem formatado, seguindo exatamente o formato abaixo.

**Dados do Exame:**
{json.dumps(dict_responses, ensure_ascii=False, indent=2)}

**Objetivo:**
Produzir um texto único que:
- Identifique claramente os conceitos/tópicos que o aluno domina
- Identifique claramente os conceitos/tópicos que o aluno precisa melhorar (quando houver)
- Traga recomendações diretas e objetivas com base nas dificuldades apresentadas
- Respeite rigorosamente a formatação e as quebras de linha solicitadas

**Estrutura EXATA que você deve seguir (incluindo quebras de linha):**

"Com base nas suas respostas, percebi que você precisa reforçar seus estudos em **<áreas que o aluno errou>**.\n
Você demonstrou dificuldade em **<conceitos ou tópicos específicos que o aluno errou>**.\n
**Sugestão**: <recomendação direta e prática do que estudar>.\n
Isso vai ajudar a melhorar seu desempenho nesses pontos."

Caso o aluno tenha acertado a maioria das questões e NÃO haja áreas reais de dificuldade, você DEVE adaptar a estrutura para evitar frases artificiais como “nenhuma área” ou “nenhum conceito”. Nesse caso, siga estas substituições obrigatórias:

- Troque:  
  "você precisa reforçar seus estudos em **<áreas>**"  
  por:  
  "No momento, você não precisa reforçar nenhuma área específica, pois demonstrou excelente domínio dos conteúdos avaliados."

- Troque:  
  "Você demonstrou dificuldade em **<tópicos>**"  
  por:  
  "Você não apresentou dificuldades relevantes neste exame."

- A recomendação deve ser positiva, como:  
  "**Sugestão**: continue aprofundando seus conhecimentos e explorando tópicos mais avançados para manter seu alto desempenho."

**Regras obrigatórias:**
- Sempre manter as quebras de linha usando exatamente `\\n`.
- NÃO transformar o texto em bloco único.
- NÃO usar listas, tópicos ou bullets.
- O texto final deve ser fluido, com as quebras de linha como separadores.
- Use apenas tópicos presentes nos dados do exame — nunca invente.
- Se o aluno acertar vários itens, incluir a frase:
  "Você demonstrou domínio em **<tópicos que acertou>**."  
  sempre com quebra de linha antes ou depois, seguindo o texto.
- A saída final deve conter apenas o texto formatado, nenhuma explicação adicional.

Agora gere o feedback formatado exatamente conforme instruído.
"""

    response_text = get_gemini_response(prompt, temperature)
    return response_text

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
    global dict_questions
    
    if not db:
        return JSONResponse(status_code=500, content={"error": "Banco vetorial não inicializado."})

    relevant_docs = db.similarity_search(data.topic, k=8)
    if not relevant_docs:
        return JSONResponse(status_code=404, content={"error": "Nenhum documento relevante encontrado."})

    context = format_docs(relevant_docs)
    
    # Reseta dict_questions para novo exame
    dict_questions = {}
    
    mcq = generate_mcq_from_context(
        context=context,
        topic=data.topic,
        qnt_questoes=data.qnt_questoes, 
        temperature=0.5
    )

    # Inicializa dict_questions com a estrutura correta
    for i, question_key in enumerate(mcq.keys(), 1):
        if question_key == "sources":
            continue
            
        question = mcq[question_key]
        correct_opt = None
        
        for opt in question.get("options", []):
            if opt.get("is_correct", False):
                correct_opt = opt["option"]
                break
        
        dict_questions[question_key] = {
            "text": question["text"],
            "correct_option": correct_opt,
            "chosen_option": "",
            "is_correct": False
        }
    
    # Adiciona fontes ao JSON retornado
    mcq["sources"] = [doc.metadata.get("source", "Desconhecida") for doc in relevant_docs]

    return mcq

@router.post("/check_answer/")
def check_answer(data: CheckAnswerRequest):
    """Verifica se a resposta do aluno está correta."""
    global dict_questions
    
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
    
    is_correct = chosen.lower() == (correct_option or "").lower() if correct_option else False

    # Atualiza dict_questions com a resposta do aluno
    for key in dict_questions:
        if dict_questions[key]["text"] == question_data.get("text"):
            dict_questions[key]["chosen_option"] = chosen
            dict_questions[key]["is_correct"] = is_correct
            break

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
    """Substitui uma questão específica por uma nova e salva no questions.json."""
    global dict_questions
    
    updated = substitute_question(
        original_mcq=data.original_mcq,
        question_number=data.question_number,
        topic=data.topic,
    )
    
    # Salva no arquivo JSON
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    QUESTIONS_PATH = os.path.join(CURRENT_DIR, "questions.json")
    
    with open(QUESTIONS_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(updated, arquivo, ensure_ascii=False, indent=4)
    
    # Atualiza o dict_questions com a nova questão
    new_question_data = updated[data.question_number]
    
    # Encontra a alternativa correta
    correct_opt = None
    for opt in new_question_data.get("options", []):
        if opt.get("is_correct", False):
            correct_opt = opt["option"]
            break
    
    # Atualiza o dicionário global
    dict_questions[data.question_number] = {
        "text": new_question_data["text"],
        "correct_option": correct_opt,
        "chosen_option": "",
        "is_correct": False
    }
    
    return updated

@router.post("/generate_PDF/")
async def generate_PDF():
    """Gera PDF com as questões do exame."""
    try:
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        QUESTIONS_PATH = os.path.join(CURRENT_DIR, "questions.json")

        if not os.path.exists(QUESTIONS_PATH):
            return JSONResponse(
                status_code=404, 
                content={"status": "error", "message": "Arquivo questions.json não encontrado"}
            )

        with open(QUESTIONS_PATH, "r", encoding="utf-8") as arquivo:
            exame = json.load(arquivo)

        result = create_PDF(exame)

        return FileResponse(result, media_type='application/pdf', filename="ExamForge.pdf")

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Erro ao gerar PDF: {str(e)}"}
        )

@router.post("/final_evaluation")
def final_evaluation():
    """Gera feedback final baseado nas respostas do aluno."""
    if not dict_questions:
        return JSONResponse(
            status_code=400,
            content={"error": "Nenhum exame foi respondido ainda"}
        )
    
    feedback = generate_feedback(dict_questions)
    return {
        "feedback": feedback,
        "respostas": dict_questions
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