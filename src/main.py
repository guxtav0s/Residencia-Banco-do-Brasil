from fastapi import FastAPI
from dotenv import load_dotenv
from .api.routes import router

load_dotenv()

app = FastAPI(title="API de Transações Financeiras - Residência BB")

app.include_router(router)

@app.get("/")
def home():
    return {"mensagem": "Bem-vindo à API de Transações Financeiras. Acesse /docs para a documentação."}
