from fastapi import FastAPI
from .routes import router

app = FastAPI(title="API de Transações Financeiras")

# Incluindo as rotas modularizadas
app.include_router(router)

@app.get("/")
def home():
    return {"mensagem": "Bem-vindo à API de Transações Financeiras. Acesse /docs para a documentação."}
