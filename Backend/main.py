from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.create_base import router as base_router
from app.create_questions import router as create_router


app = FastAPI(
    title="ExamForge",
    description="Teste de FastAPI",
    version="1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(base_router)
app.include_router(create_router)


@app.get("/")
def root():
    return {"message": "Bem-vindo ao ExamForg!"}
