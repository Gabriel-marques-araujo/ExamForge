import os
import json
import re
import random
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from fpdf import FPDF

load_dotenv()

router = APIRouter(prefix="/rag", tags=["RAG Ollama MCQ"])

# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------
# Por padrão mantém o comportamento original (arquivos ao lado deste módulo e ./chroma).
# Para empacotar em executável, defina EXAMFORGE_DATA com uma pasta gravável.
_data_env = os.getenv("EXAMFORGE_DATA")
if _data_env:
    DATA_DIR = Path(_data_env)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_DIR = str(DATA_DIR)
    CHROMA_PATH = str(DATA_DIR / "chroma")
else:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    CHROMA_PATH = "./chroma"

QUESTIONS_PATH = os.path.join(CURRENT_DIR, "questions.json")
COLLECTION_NAME = "exame_docs"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")   # alternativas: qwen3:4b-instruct, gemma3:4b, llama3.2:3b
MCQ_WORKERS = int(os.getenv("MCQ_WORKERS", "1"))         # em CPU, 1 é o melhor
OLLAMA_NUM_THREAD = int(os.getenv("OLLAMA_NUM_THREAD", "0"))  # 0 = automático; teste o nº de núcleos físicos
CHUNKS_PER_QUESTION = 2
CHUNK_MAX_CHARS = 800
MCQ_NUM_PREDICT = 500
MAX_RETRIES = 2

ANGULOS = [
    "definição e conceito central",
    "aplicação prática",
    "comparação entre conceitos relacionados",
    "identificar a afirmação incorreta ou exceção",
    "causa e consequência",
    "funcionamento interno / mecanismo",
]

embedding_function = OllamaEmbeddings(model="nomic-embed-text", keep_alive=1800)  # segundos

try:
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_function,
        collection_name=COLLECTION_NAME,
    )
except Exception as e:
    print(f"⚠️ Erro ao carregar banco vetorial: {e}")
    db = None

dict_questions = {}


# ----------------------------------------------------------------------------
# Ollama
# ----------------------------------------------------------------------------
@lru_cache(maxsize=16)
def criar_modelo(temperature: float, num_predict: int, json_mode: bool):
    """Cliente Ollama cacheado. Thinking desligado e saída JSON forçada quando pedido."""
    kwargs = dict(
        model=OLLAMA_MODEL,
        temperature=temperature,
        num_ctx=3072,
        num_predict=num_predict,
        keep_alive="30m",
    )
    if OLLAMA_NUM_THREAD > 0:
        kwargs["num_thread"] = OLLAMA_NUM_THREAD
    if json_mode:
        kwargs["format"] = "json"
    try:
        return ChatOllama(**kwargs, reasoning=False)
    except Exception:
        return ChatOllama(**kwargs)


def get_ollama_response(
    prompt: str,
    temperature: float = 0.3,
    num_predict: int = MCQ_NUM_PREDICT,
    json_mode: bool = False,
) -> str:
    """Gera resposta textual usando o Ollama local."""
    try:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("O prompt está vazio ou não é texto.")

        messages = [
            (
                "system",
                "/no_think Você é um assistente educacional. Responda em português brasileiro. "
                "Quando solicitado, retorne somente JSON válido.",
            ),
            ("user", prompt),
        ]

        response = criar_modelo(temperature, num_predict, json_mode).invoke(messages)
        content = response.content

        if not isinstance(content, str):
            raise ValueError("Resposta do Ollama em formato inesperado.")

        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        if not content:
            raise ValueError("O Ollama retornou uma resposta vazia.")

        return content

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao consultar Ollama ({type(e).__name__}): {e}. "
                   f"Verifique se o Ollama está ativo e se {OLLAMA_MODEL} está instalado.",
        )


def _warmup():
    """Carrega os modelos na memória para a primeira requisição não pagar o cold start."""
    try:
        if db:
            db.similarity_search("warmup", k=1)
        criar_modelo(0.1, 8, False).invoke([("user", "/no_think ok")])
    except Exception as e:
        print(f"⚠️ Warmup falhou (ignorado): {e}")


threading.Thread(target=_warmup, daemon=True).start()


# ----------------------------------------------------------------------------
# Utilitários
# ----------------------------------------------------------------------------
def format_docs(docs):
    """Formata documentos recuperados do banco vetorial."""
    return "\n\n".join(
        f"Fonte: {doc.metadata.get('source', 'Desconhecida')}\n"
        f"Conteúdo: {doc.page_content[:CHUNK_MAX_CHARS]}"
        for doc in docs
    )


def parse_json_object(response_text: str) -> dict:
    """Extrai um objeto JSON mesmo com cercas Markdown ou texto extra."""
    if not isinstance(response_text, str) or not response_text.strip():
        raise ValueError("A resposta do modelo está vazia.")

    cleaned = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char == "{":
            try:
                value, _ = decoder.raw_decode(cleaned[index:])
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                continue

    raise ValueError(f"O modelo não retornou um objeto JSON válido. Início: {cleaned[:500]}")


def validar_questao(questao: dict, nome: str = "questão") -> None:
    """Valida o formato mínimo esperado."""
    if not isinstance(questao, dict):
        raise ValueError(f"{nome}: o conteúdo não é um objeto.")
    if not isinstance(questao.get("text"), str) or not questao["text"].strip():
        raise ValueError(f"{nome}: campo 'text' ausente ou inválido.")
    options = questao.get("options")
    if not isinstance(options, list) or len(options) != 4:
        raise ValueError(f"{nome}: deve conter exatamente 4 alternativas.")
    correct_count = 0
    for i, option in enumerate(options, 1):
        if not isinstance(option, dict) or not isinstance(option.get("option"), str):
            raise ValueError(f"{nome}: alternativa {i} inválida.")
        if not isinstance(option.get("explanation"), str):
            raise ValueError(f"{nome}: explicação da alternativa {i} inválida.")
        if option.get("is_correct") is True:
            correct_count += 1
        elif option.get("is_correct") is not False:
            raise ValueError(f"{nome}: 'is_correct' deve ser true ou false.")
    if correct_count != 1:
        raise ValueError(f"{nome}: deve haver exatamente uma alternativa correta.")
    if not isinstance(questao.get("resolution"), str):
        raise ValueError(f"{nome}: campo 'resolution' ausente ou inválido.")


def substituir_caracteres_unicode(texto):
    """Substitui caracteres Unicode por equivalentes ASCII."""
    substituicoes = {
        '≤': '<=', '≥': '>=', '≠': '!=', '≈': '~',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
        'ã': 'a', 'õ': 'o', 'ç': 'c', 'ü': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'À': 'A', 'È': 'E', 'Ì': 'I', 'Ò': 'O', 'Ù': 'U',
        'Â': 'A', 'Ê': 'E', 'Î': 'I', 'Ô': 'O', 'Û': 'U',
        'Ã': 'A', 'Õ': 'O', 'Ç': 'C', 'Ü': 'U',
    }
    for char, replacement in substituicoes.items():
        texto = texto.replace(char, replacement)
    return texto


def obter_letra_enumeração(indice):
    return ['A', 'B', 'C', 'D'][indice % 4]


def salvar_questoes(mcq: dict) -> None:
    with open(QUESTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(mcq, f, ensure_ascii=False, indent=4)


def _entrada_dict_questions(question: dict) -> dict:
    correct_opt = next(
        (o["option"] for o in question.get("options", []) if o.get("is_correct") is True),
        None,
    )
    return {
        "text": question.get("text", ""),
        "correct_option": correct_opt,
        "chosen_option": "",
        "is_correct": False,
    }


def registrar_questoes(mcq: dict) -> None:
    """Reconstrói o dict_questions global a partir do MCQ."""
    global dict_questions
    dict_questions = {
        key: _entrada_dict_questions(q)
        for key, q in mcq.items()
        if key != "sources" and isinstance(q, dict)
    }


# ----------------------------------------------------------------------------
# Geração de questões (uma chamada por questão)
# ----------------------------------------------------------------------------
def _prompt_questao(context: str, topic: str, angulo: str, evitar: list) -> str:
    evitar_txt = ""
    if evitar:
        lista = "\n".join(f"- {t[:200]}" for t in evitar)
        evitar_txt = f"\nNão repita o tema/abordagem destes enunciados:\n{lista}\n"

    return f"""Gere 1 questão de múltipla escolha técnica sobre: {topic}.
Foco desta questão: {angulo}.

Regras:
- Use o material abaixo só como referência conceitual; não cite "documento", "contexto" ou "texto".
- Não invente temas fora do material. Sem cenários fictícios; enunciado direto e objetivo.
- Exatamente 4 alternativas, apenas 1 correta (coloque a correta como a primeira da lista).
- Explicação de cada alternativa: no máximo 10 palavras.
- "resolution": no máximo 15 palavras.
{evitar_txt}
Responda SOMENTE com JSON neste formato:
{{"text": "enunciado", "options": [
{{"option": "...", "is_correct": true, "explanation": "..."}},
{{"option": "...", "is_correct": false, "explanation": "..."}},
{{"option": "...", "is_correct": false, "explanation": "..."}},
{{"option": "...", "is_correct": false, "explanation": "..."}}],
"resolution": "..."}}

Material:
{context}
"""


def gerar_questao(context: str, topic: str, angulo: str, evitar=None,
                  temperature: float = 0.5, nome: str = "questão") -> dict:
    """Gera, valida e embaralha uma questão, com retry."""
    prompt = _prompt_questao(context, topic, angulo, evitar or [])
    ultimo_erro = None

    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            raw = get_ollama_response(
                prompt, temperature, num_predict=MCQ_NUM_PREDICT, json_mode=True
            )
            obj = parse_json_object(raw)

            # Aceita {"text": ...} ou {"question 1": {...}}
            if "text" not in obj:
                dicts = [v for v in obj.values() if isinstance(v, dict)]
                if len(dicts) == 1:
                    obj = dicts[0]

            validar_questao(obj, nome)
            random.shuffle(obj["options"])  # posição da correta balanceada
            return obj
        except HTTPException:
            raise
        except Exception as e:
            ultimo_erro = e
            print(f"⚠️ {nome}: tentativa {tentativa} falhou: {e}")

    raise HTTPException(
        status_code=502,
        detail=f"{nome}: não foi possível gerar uma questão válida "
               f"({type(ultimo_erro).__name__}: {ultimo_erro})",
    )


def _contexto_para_questao(docs: list, i: int) -> str:
    """Seleciona chunks rotativos para cada questão, gerando diversidade."""
    n = len(docs)
    k = min(CHUNKS_PER_QUESTION, n)
    return format_docs([docs[(i * k + j) % n] for j in range(k)])


def _buscar_docs(topic: str, qnt_questoes: int) -> list:
    if db is None:
        raise HTTPException(status_code=500, detail="Banco vetorial não inicializado.")
    k = min(12, max(4, qnt_questoes * CHUNKS_PER_QUESTION))
    docs = db.similarity_search(topic, k=k)
    if not docs:
        raise HTTPException(status_code=404, detail="Nenhum documento relevante encontrado.")
    return docs


def _tarefa_questao(docs: list, topic: str, i: int, temperature: float):
    nome = f"question {i + 1}"
    q = gerar_questao(
        context=_contexto_para_questao(docs, i),
        topic=topic,
        angulo=ANGULOS[i % len(ANGULOS)],
        temperature=temperature,
        nome=nome,
    )
    return nome, q


def generate_mcq_from_docs(docs: list, topic: str, qnt_questoes: int,
                           temperature: float = 0.5) -> dict:
    """Gera N questões e devolve {"question 1": {...}, ...}."""
    workers = max(1, min(MCQ_WORKERS, qnt_questoes))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        resultados = list(pool.map(
            lambda i: _tarefa_questao(docs, topic, i, temperature),
            range(qnt_questoes),
        ))
    return dict(resultados)


def substitute_question(original_mcq: dict, question_number: str, topic: str,
                        temperature: float = 0.6):
    """Substitui a questão escolhida por uma nova."""
    if not db:
        raise HTTPException(status_code=500, detail="Banco vetorial não inicializado.")

    docs = db.similarity_search(topic, k=8)
    if not docs:
        raise HTTPException(status_code=404, detail="Nenhum documento relevante encontrado.")

    random.shuffle(docs)

    evitar = [
        q["text"] for q in original_mcq.values()
        if isinstance(q, dict) and isinstance(q.get("text"), str)  # inclui a original
    ]

    nova = gerar_questao(
        context=format_docs(docs[:CHUNKS_PER_QUESTION]),
        topic=topic,
        angulo=random.choice(ANGULOS),
        evitar=evitar,
        temperature=temperature,
        nome=question_number,
    )

    original_mcq[question_number] = nova
    return original_mcq


# ----------------------------------------------------------------------------
# PDF
# ----------------------------------------------------------------------------
def create_PDF(exame):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf_path = os.path.join(CURRENT_DIR, "prova_ExamForge.pdf")

    questoes = [q for k, q in exame.items() if k != "sources" and isinstance(q, dict)]

    for i, question in enumerate(questoes, 1):
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 0, 128)
        pdf.cell(0, 15, f"Questão {i}:", 0, 1)

        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 8, substituir_caracteres_unicode(question['text']), 0, 1)
        pdf.ln(5)

        pdf.set_font("Arial", size=11)
        for j, option in enumerate(question['options']):
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


# ----------------------------------------------------------------------------
# Feedback final
# ----------------------------------------------------------------------------
def generate_feedback(dict_responses: dict, temperature: float = 0.5):
    resumo = [
        {"questao": v["text"], "acertou": v["is_correct"]}
        for v in dict_responses.values()
    ]

    prompt = f"""Você é um avaliador educacional. Analise o desempenho do aluno e gere um feedback curto.

Dados:
{json.dumps(resumo, ensure_ascii=False)}

Formato EXATO (use a sequência literal \\n entre as linhas, sem listas ou bullets):

Com base nas suas respostas, percebi que você precisa reforçar seus estudos em **<áreas que errou>**.\\nVocê demonstrou dificuldade em **<conceitos específicos que errou>**.\\n**Sugestão**: <recomendação prática>.\\nIsso vai ajudar a melhorar seu desempenho nesses pontos.

Se o aluno acertou a maioria e não há dificuldades reais, use:
"No momento, você não precisa reforçar nenhuma área específica, pois demonstrou excelente domínio dos conteúdos avaliados.\\nVocê não apresentou dificuldades relevantes neste exame.\\n**Sugestão**: continue aprofundando seus conhecimentos e explorando tópicos mais avançados.\\nIsso vai ajudar a manter seu alto desempenho."

Se acertou vários itens, inclua antes da sugestão: "Você demonstrou domínio em **<tópicos que acertou>**.\\n"
Use apenas tópicos presentes nos dados. Responda só com o texto final.
"""
    return get_ollama_response(prompt, temperature, num_predict=400)


# ----------------------------------------------------------------------------
# Modelos de requisição
# ----------------------------------------------------------------------------
class MCQRequest(BaseModel):
    topic: str
    qnt_questoes: int


class CheckAnswerRequest(BaseModel):
    question_data: dict
    chosen_option: str


class SubstituteQuestionRequest(BaseModel):
    original_mcq: dict
    question_number: str
    topic: str


# ----------------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------------
def _validar_qnt(qnt: int):
    if qnt < 1 or qnt > 10:
        raise HTTPException(
            status_code=400,
            detail="A quantidade de questões deve estar entre 1 e 10.",
        )


@router.post("/generate_mcq/")
def generate_mcq(data: MCQRequest):
    """Gera questões de múltipla escolha (resposta única, ao final)."""
    try:
        _validar_qnt(data.qnt_questoes)
        relevant_docs = _buscar_docs(data.topic, data.qnt_questoes)

        mcq = generate_mcq_from_docs(
            docs=relevant_docs,
            topic=data.topic,
            qnt_questoes=data.qnt_questoes,
            temperature=0.5,
        )

        salvar_questoes(mcq)
        registrar_questoes(mcq)

        mcq["sources"] = list(dict.fromkeys(
            doc.metadata.get("source", "Desconhecida") for doc in relevant_docs
        ))
        return mcq

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar questões: {type(e).__name__}: {e}",
        )


@router.post("/generate_mcq_stream/")
def generate_mcq_stream(data: MCQRequest):
    """Gera questões e envia cada uma (NDJSON) assim que fica pronta.

    Cada linha é um JSON: {"question N": {...}}, {"error": "..."} ou, por último,
    {"sources": [...]}.
    """
    _validar_qnt(data.qnt_questoes)
    docs = _buscar_docs(data.topic, data.qnt_questoes)
    fontes = list(dict.fromkeys(d.metadata.get("source", "Desconhecida") for d in docs))

    def linha(obj: dict) -> str:
        return json.dumps(obj, ensure_ascii=False) + "\n"

    def stream():
        coletadas = {}
        workers = max(1, min(MCQ_WORKERS, data.qnt_questoes))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futuros = {
                pool.submit(_tarefa_questao, docs, data.topic, i, 0.5): f"question {i + 1}"
                for i in range(data.qnt_questoes)
            }
            for fut in as_completed(futuros):
                nome = futuros[fut]
                try:
                    _, q = fut.result()
                    coletadas[nome] = q
                    yield linha({nome: q})
                except Exception as e:
                    detalhe = getattr(e, "detail", str(e))
                    yield linha({"error": f"{nome}: {detalhe}"})

        if coletadas:
            ordenado = dict(sorted(coletadas.items(), key=lambda kv: int(kv[0].split()[1])))
            salvar_questoes(ordenado)
            registrar_questoes(ordenado)
        yield linha({"sources": fontes})

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.post("/check_answer/")
def check_answer(data: CheckAnswerRequest):
    """Verifica se a resposta do aluno está correta."""
    question_data = data.question_data
    chosen = data.chosen_option.strip()

    correct_option = None
    explanation_correct = ""
    explanation_chosen = ""

    for opt in question_data.get("options", []):
        opt_text = opt["option"].strip()
        if opt.get("is_correct", False):
            correct_option = opt_text
            explanation_correct = opt.get("explanation", "Explicação não disponível.")
        if opt_text.lower() == chosen.lower():
            explanation_chosen = opt.get("explanation", "Explicação não disponível.")

    is_correct = bool(correct_option) and chosen.lower() == correct_option.lower()

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
            "explanation": explanation_chosen,
        }
    return {
        "is_correct": False,
        "chosen_option": chosen,
        "message": "❌ Está incorreto.",
        "explanation_chosen": explanation_chosen,
        "correct_option": correct_option,
        "explanation_correct": explanation_correct,
    }


@router.post("/substitute_question/")
def substitute_question_endpoint(data: SubstituteQuestionRequest):
    """Substitui uma questão específica por uma nova e salva no questions.json."""
    updated = substitute_question(
        original_mcq=data.original_mcq,
        question_number=data.question_number,
        topic=data.topic,
    )

    salvar_questoes(updated)
    dict_questions[data.question_number] = _entrada_dict_questions(updated[data.question_number])

    return updated


@router.post("/generate_PDF/")
async def generate_PDF():
    """Gera PDF com as questões do exame."""
    try:
        if not os.path.exists(QUESTIONS_PATH):
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Arquivo questions.json não encontrado"},
            )

        with open(QUESTIONS_PATH, "r", encoding="utf-8") as arquivo:
            exame = json.load(arquivo)

        result = create_PDF(exame)
        return FileResponse(result, media_type='application/pdf', filename="ExamForge.pdf")

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Erro ao gerar PDF: {e}"},
        )


@router.post("/final_evaluation")
def final_evaluation():
    """Gera feedback final baseado nas respostas do aluno."""
    if not dict_questions:
        return JSONResponse(status_code=400, content={"error": "Nenhum exame foi respondido ainda"})

    feedback = generate_feedback(dict_questions)
    return {"feedback": feedback, "respostas": dict_questions}


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
        "model": f"{OLLAMA_MODEL} (Ollama local)",
    }