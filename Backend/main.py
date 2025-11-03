from typing import Union

from fastapi import FastAPI

from app.create_base import router as base_router
from app.Rag_router import router as Rag_router

app = FastAPI()

@app.get("/")
def read_root():
    return {"Projeto ExameForg"}

app.include_router(base_router)
app.include_router(Rag_router)

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
