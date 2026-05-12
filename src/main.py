from fastapi import FastAPI
from .api.routes import router

app = FastAPI(title="API de Transações Financeiras - Refatorado")

# Incluindo as rotas a partir do módulo api
app.include_router(router)

@app.get("/")
def home():
    return {"mensagem": "Bem-vindo à API de Transações Financeiras. Acesse /docs para a documentação."}
