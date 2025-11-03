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



#  CONFIGURAÇÃO DE EMBEDDINGS E BASE VETORIAL


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


#  FUNÇÕES AUXILIARES


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


# GERAÇÃO DE QUESTÕES DE MÚLTIPLA ESCOLHA (RAG)


def generate_mcq_from_context(context: str, topic: str, temperature: float = 0.5):
    """Gera uma questão de múltipla escolha com base no contexto."""
    prompt = f"""
    Você é um especialista no tema: {topic}.
    Com base EXCLUSIVA no contexto abaixo, gere uma questão de múltipla escolha com 4 alternativas (A, B, C, D),
    sendo somente uma correta.

    ⚠️ Responda em JSON válido, sem texto adicional, sem explicação antes ou depois.
    Exemplo:
    {{
    "question": "Texto da questão",
    "options": [
        {{"option": "Alternativa 1", "is_correct": true/false}},
        {{"option": "Alternativa 2", "is_correct": true/false}},
        {{"option": "Alternativa 3", "is_correct": true/false}},
        {{"option": "Alternativa 4", "is_correct": true/false}}
    ]
    }}

    Se o contexto não contiver informação suficiente, retorne:
    {{"question": "Não há dados suficientes para gerar questão.", "options": []}}

    Contexto:
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


def explain_answer(topic: str, question: str, chosen_option: str, correct_option: str):
    """Gera explicação da resposta baseada no contexto recuperado."""
    relevant_docs = db.similarity_search(topic, k=5) if db else []
    context = format_docs(relevant_docs) if relevant_docs else "Sem contexto disponível."

    prompt = f"""
    Você é um avaliador. O aluno respondeu a seguinte questão:

    Pergunta: {question}
    Resposta escolhida: {chosen_option}
    Resposta correta: {correct_option}

    Baseando-se APENAS nas informações do contexto abaixo, explique:
    - Se a resposta escolhida está correta ou incorreta.
    - E dê uma explicação clara e objetiva com base no conteúdo do contexto.

    Contexto:
    {context}
    """

    return get_gemini_response(prompt, temperature=0.5)



#  MODELOS DE REQUISIÇÃO


class MCQRequest(BaseModel):
    topic: str


class CheckAnswerRequest(BaseModel):
    topic: str
    question: str
    chosen_option: str
    correct_option: str



#  ENDPOINTS


@router.post("/generate_mcq/")
def generate_mcq(data: MCQRequest):
    """Gera uma questão de múltipla escolha baseada no tema informado."""
    if not db:
        return JSONResponse(status_code=500, content={"error": "Banco vetorial não inicializado."})

    relevant_docs = db.similarity_search(data.topic, k=8)
    if not relevant_docs:
        return JSONResponse(status_code=404, content={"error": "Nenhum documento relevante encontrado."})

    context = format_docs(relevant_docs)
    mcq = generate_mcq_from_context(context, data.topic, temperature=0.5)
    mcq["sources"] = [doc.metadata.get("source", "Desconhecida") for doc in relevant_docs]
    return mcq


@router.post("/check_answer/")
def check_answer(data: CheckAnswerRequest):
    """Verifica se a resposta está correta e gera explicação baseada nos documentos."""
    is_correct = data.chosen_option.strip().lower() == data.correct_option.strip().lower()
    explanation = explain_answer(data.topic, data.question, data.chosen_option, data.correct_option)
    return {"is_correct": is_correct, "explanation": explanation}


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
