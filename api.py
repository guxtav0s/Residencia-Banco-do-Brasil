from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Modelo de dados que o POST vai receber
class Transacao(BaseModel):
    id: int
    valor: float
    data: str
    hora: str
    dia_semana: str
    categoria: str
    conta: str
    cidade: str
    estado: str
    pais: str
    latitude: float
    longitude: float
    tipo_transacao: str
    dispositivo: str
    estabelecimento: str
    tentativas: int
    ip_origem: str
    is_fraude: int

# Função auxiliar para conectar no banco de dados
def conectar_banco():
    conexao = sqlite3.connect("banco.db")
    # Isso faz com que os resultados do banco venham como dicionários em vez de tuplas
    conexao.row_factory = sqlite3.Row 
    return conexao

# 1. GET /transactions - Lista transações do banco
@app.get("/transactions")
def listar_transacoes():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    # Adicionei um LIMIT 100 para não travar sua API ao puxar os 30k de dados de vez
    cursor.execute("SELECT * FROM transacoes LIMIT 100")
    linhas = cursor.fetchall()
    conexao.close()
    
    return [dict(linha) for linha in linhas]

# 2. GET /transactions/{id} - Busca uma transação específica
@app.get("/transactions/{id}")
def buscar_transacao(id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM transacoes WHERE id = ?", (id,))
    linha = cursor.fetchone()
    conexao.close()
    
    if linha is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada no banco")
        
    return dict(linha)

# 3. POST /transactions - Insere no banco (Persistência)
@app.post("/transactions")
def criar_transacao(t: Transacao):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO transacoes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (t.id, t.valor, t.data, t.hora, t.dia_semana, t.categoria, t.conta, 
              t.cidade, t.estado, t.pais, t.latitude, t.longitude, t.tipo_transacao, 
              t.dispositivo, t.estabelecimento, t.tentativas, t.ip_origem, t.is_fraude))
        conexao.commit()
    except sqlite3.IntegrityError:
        conexao.close()
        raise HTTPException(status_code=400, detail="Erro: ID da transação já existe.")
        
    conexao.close()
    return {"mensagem": "Transação salva com sucesso no banco de dados!"}