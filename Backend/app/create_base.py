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
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    file_path = os.path.join(DOCUMENTS_PATH, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": f"Arquivo {file.filename} enviado com sucesso!"}


@router.post("/create/")
def create_vector_database():
    if not os.path.exists(DOCUMENTS_PATH):
        return JSONResponse(status_code=400, content={"error": "Nenhum diretório 'documentos' encontrado."})

    docs = []
    for root, _, files in os.walk(DOCUMENTS_PATH):
        for filename in files:
            file_path = os.path.join(root, filename)
            ext = filename.lower().split(".")[-1]
            try:
                if ext in ["md", "markdown"]:
                    loader = UnstructuredMarkdownLoader(file_path, languages=["por"])
                elif ext in ["txt", "csv", "json"]:
                    loader = TextLoader(file_path)
                elif ext in ["docx", "doc"]:
                    loader = UnstructuredWordDocumentLoader(file_path,languages=["por"])
                elif ext in ["pdf"]:
                    loader = UnstructuredPDFLoader(file_path,languages=["por"])
                else:
                    loader = UnstructuredFileLoader(file_path,languages=["por"])
                docs.extend(loader.load())
            except Exception as e:
                print(f"⚠️ Erro ao carregar {filename}: {e}")

    if not docs:
        return JSONResponse(status_code=400, content={"error": "Nenhum documento válido encontrado."})

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True
    )
    documents = text_splitter.split_documents(docs)

    print(f"Total de chunks criados: {len(documents)}")

   
    embedding = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        api_key=GEMINI_KEY
      
    )

    
    db = Chroma.from_documents(
        documents,
        embedding,
        persist_directory=CHROMA_PATH,
        collection_name=COLLECTION_NAME
    )
    print("Banco de dados vetorial criado com sucesso.")

    return {"message": f"Banco de dados vetorial criado com {len(documents)} chunks."}


@router.get("/status/")
def status():
    total_docs = len(os.listdir(DOCUMENTS_PATH)) if os.path.exists(DOCUMENTS_PATH) else 0
    return {
        "status": "ok",
        "docs": total_docs,
        "collection": COLLECTION_NAME
    }
