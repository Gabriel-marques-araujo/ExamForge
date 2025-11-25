import os
import shutil
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from langchain_community.document_loaders import (
    UnstructuredFileLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv


load_dotenv()

router = APIRouter(prefix="/base", tags=["Criação de Base Vetorial"])

DOCUMENTS_PATH = "./Documentos"
CHROMA_PATH = "./chroma"
COLLECTION_NAME = "exame_docs"

GEMINI_KEY = os.getenv("GOOGLE_GEMINI_KEY")

if not GEMINI_KEY:
    raise ValueError("GOOGLE_GEMINI_KEY não encontrada no arquivo .env")


os.environ["GOOGLE_API_KEY"] = GEMINI_KEY



@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):

    """Recebe um arquivo e salva localmente em ./Documentos"""


    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    file_path = os.path.join(DOCUMENTS_PATH, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": f"Arquivo {file.filename} enviado com sucesso!"}

@router.get("/list/")
def list_upload_files():
    """Lista todos os arquivos enviados para a pasta Documentos"""

    if not os.path.exists(DOCUMENTS_PATH):
        return{"files": []}
    files = os.listdir(DOCUMENTS_PATH)
    return {"files": files}

@router.post("/create/")
def create_vector_database():

    """Cria/atualiza a base vetorial com novos arquivos em ./Documentos"""

    if not os.path.exists(DOCUMENTS_PATH):
        return JSONResponse(
            status_code=400,
            content={"error": "Nenhum diretório 'Documentos' encontrado."}
        )

    # Embeddings
    embedding = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        api_key=GEMINI_KEY
    )

    # Carregar OU criar banco Chroma
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding,
        collection_name=COLLECTION_NAME
    )

    # Buscar documentos já vetorizados
    existing_docs = set()
    try:
        stored = db.get(include=["metadatas"])
        for meta in stored["metadatas"]:
            if meta and "source" in meta:
                existing_docs.add(meta["source"])
    except:
        pass

    print("Documentos já vetorizados:", existing_docs)


    new_files = []
    docs = []

    for root, _, files in os.walk(DOCUMENTS_PATH):
        for filename in files:
            file_path = os.path.join(root, filename)

            # Ignorar arquivos já vetorizados
            if file_path in existing_docs:
                continue

            new_files.append(filename)

            ext = filename.lower().split(".")[-1]
            try:
                if ext in ["md", "markdown"]:
                    loader = UnstructuredMarkdownLoader(file_path, languages=["por"])
                elif ext in ["txt", "csv", "json"]:
                    loader = TextLoader(file_path)
                elif ext in ["docx", "doc"]:
                    loader = UnstructuredWordDocumentLoader(file_path, languages=["por"])
                elif ext in ["pdf"]:
                    loader = UnstructuredPDFLoader(file_path, languages=["por"])
                else:
                    loader = UnstructuredFileLoader(file_path, languages=["por"])

                loaded_docs = loader.load()

                
                for d in loaded_docs:
                    d.metadata["source"] = file_path

                docs.extend(loaded_docs)

            except Exception as e:
                print(f"⚠️ Erro ao carregar {filename}: {e}")

    # Se tudo já foi vetorizado
    if not docs:
        return {
            "message": "Nenhum novo documento para vetorizar.",
            "documents_existing": list(existing_docs),
            "chunks_added": 0,
            "chunks_total": len(db.get()["ids"])
        }


    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True
    )

    documents = text_splitter.split_documents(docs)

    print(f"NOVOS CHUNKS GERADOS: {len(documents)}")

    db.add_documents(documents)

    # Contar total final
    total_chunks = len(db.get()["ids"])

    return {
        "message": "Vetorização concluída!",
        "documents_new": new_files,
        "documents_existing": list(existing_docs),
        "chunks_added": len(documents),
        "chunks_total": total_chunks
    }


@router.get("/status/")
def status():
    
    """Status do ./Documentos"""

    total_docs = len(os.listdir(DOCUMENTS_PATH)) if os.path.exists(DOCUMENTS_PATH) else 0
    return {
        "status": "ok",
        "docs": total_docs,
        "collection": COLLECTION_NAME
    }