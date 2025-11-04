from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredFileLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
import shutil

router = APIRouter(prefix="/base", tags=["Criação de Base Vetorial"])

DOCUMENTS_PATH = "./documentos"
CHROMA_PATH = "./chroma"
COLLECTION_NAME = "examforge_docs"


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
                    loader = UnstructuredMarkdownLoader(file_path)
                elif ext in ["txt", "csv", "json"]:
                    loader = TextLoader(file_path)
                elif ext in ["docx", "doc"]:
                    loader = UnstructuredWordDocumentLoader(file_path)
                elif ext in ["pdf"]:
                    loader = UnstructuredPDFLoader(file_path)
                else:
                    
                    loader = UnstructuredFileLoader(file_path)

                docs.extend(loader.load())

            except Exception as e:
                print(f"⚠️ Erro ao carregar {filename}: {e}")

    if not docs:
        return JSONResponse(status_code=400, content={"error": "Nenhum documento válido encontrado."})

    # Divide em chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0,
        length_function=len,
        add_start_index=True
    )

    documents = text_splitter.split_documents(docs)

    # Cria embeddings
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        encode_kwargs={'normalize_embeddings': False}
    )

    # Cria base vetorial
    db = Chroma.from_documents(
        documents,
        embedding,
        persist_directory=CHROMA_PATH,
        collection_name=COLLECTION_NAME
    )

    return {"message": f"Banco de dados vetorial criado com {len(documents)} chunks."}


@router.get("/status/")
def status():
    total_docs = len(os.listdir(DOCUMENTS_PATH)) if os.path.exists(DOCUMENTS_PATH) else 0
    return {
        "status": "ok",
        "docs": total_docs,
        "collection": COLLECTION_NAME
    }
