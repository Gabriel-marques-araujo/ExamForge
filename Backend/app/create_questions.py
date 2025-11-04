import os
import json
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import google.generativeai as genai

router = APIRouter(prefix="/create", tags=["RAG Gemini MCQ"])

# 🔑 Carrega a chave da API do Gemini
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY não encontrada no .env")

genai.configure(api_key=api_key)
genai_model = genai.GenerativeModel("gemini-2.5-flash")

# 🧩 Configura embeddings e banco vetorial existente
embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    encode_kwargs={'normalize_embeddings': False}
)

db = Chroma(
    persist_directory="./chroma",
    embedding_function=embedding_function,
    collection_name="examforge_docs"
)

# 🔹 Função para formatar documentos
def format_docs(docs):
    return "\n\n".join([
        f"Fonte: {doc.metadata.get('source', 'Desconhecida')}\nConteúdo: {doc.page_content}"
        for doc in docs
    ])

# 🔹 Função para gerar resposta com o Gemini
def get_gemini_response(prompt: str, temperature: float = 0.5):
    try:
        response = genai_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )
        return response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resposta: {str(e)}")

# 🧠 Gera questão de múltipla escolha com base no banco
def generate_mcq_from_context(context: str, topic: str, temperature: float = 0.5):
    prompt = f"""
Você é um especialista no tema: {topic}.
Com base EXCLUSIVA no contexto abaixo, gere **uma questão de múltipla escolha** com 4 alternativas (A, B, C, D),
sendo **somente uma correta**.

⚠️ Responda em JSON válido, sem texto adicional, sem explicação antes ou depois.
Apenas retorne algo como este exemplo:

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
    # 🔍 Tenta encontrar apenas o trecho JSON da resposta
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        json_text = response_text[start:end]
        mcq = json.loads(json_text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao decodificar JSON da resposta do Gemini: {str(e)}\nResposta bruta:\n{response_text}"
        )
    return mcq


# 🧩 Gera explicação se a resposta está certa ou errada (com RAG)
def explain_answer(topic: str, question: str, chosen_option: str, correct_option: str):
    relevant_docs = db.similarity_search(topic, k=5)
    context = format_docs(relevant_docs)

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

# 🔸 MODELOS DE REQUISIÇÃO
class MCQRequest(BaseModel):
    topic: str


class CheckAnswerRequest(BaseModel):
    topic: str
    question: str
    chosen_option: str
    correct_option: str

# 🔹 Endpoint para gerar questão
@router.post("/generate_mcq/")
def generate_mcq(data: MCQRequest):
    relevant_docs = db.similarity_search(data.topic, k=8)
    if not relevant_docs:
        raise HTTPException(status_code=404, detail="Nenhum documento relevante encontrado no banco de dados.")

    context = format_docs(relevant_docs)
    mcq = generate_mcq_from_context(context, data.topic, temperature =0.5)
    mcq["sources"] = [doc.metadata.get("source", "Desconhecida") for doc in relevant_docs]
    return mcq

# 🔹 Endpoint para verificar resposta e explicar
@router.post("/check_answer/")
def check_answer(data: CheckAnswerRequest):
    is_correct = data.chosen_option.strip().lower() == data.correct_option.strip().lower()
    explanation = explain_answer(data.topic, data.question, data.chosen_option, data.correct_option)
    return {"is_correct": is_correct, "explanation": explanation}

# 🔹 Endpoint de status
@router.get("/status/")
def status():
    try:
        num_docs = len(db.get()['ids'])
    except Exception:
        num_docs = 0
    return {"status": "ok", "docs": num_docs, "model": "gemini-2.5-flash"}
