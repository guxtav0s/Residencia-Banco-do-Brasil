from fastapi import APIRouter, HTTPException
from typing import List, Optional
import sqlite3

from .models import Transacao, TransacaoAnomalia
from .database import conectar_banco
from .services import analisar_anomalias

router = APIRouter()

@router.get("/transactions")
def listar_transacoes(
    categoria: Optional[str] = None,
    cidade: Optional[str] = None,
    tipo_transacao: Optional[str] = None,
    valor_min: Optional[float] = None,
    valor_max: Optional[float] = None
):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    query = "SELECT * FROM transacoes WHERE 1=1"
    parametros = []

    if categoria:
        query += " AND categoria = ?"
        parametros.append(categoria)
    
    if cidade:
        query += " AND cidade = ?"
        parametros.append(cidade)
        
    if tipo_transacao:
        query += " AND tipo_transacao = ?"
        parametros.append(tipo_transacao)
        
    if valor_min is not None:
        query += " AND valor >= ?"
        parametros.append(valor_min)
        
    if valor_max is not None:
        query += " AND valor <= ?"
        parametros.append(valor_max)

    query += " LIMIT 100"

    cursor.execute(query, parametros)
    linhas = cursor.fetchall()
    conexao.close()
    
    return [dict(linha) for linha in linhas]

@router.get("/transactions/{id}")
def buscar_transacao(id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM transacoes WHERE id = ?", (id,))
    linha = cursor.fetchone()
    conexao.close()
    
    if linha is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada no banco")
        
    return dict(linha)

@router.post("/transactions")
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

@router.get("/anomalies", response_model=list[TransacaoAnomalia])
def detectar_anomalias():
    return analisar_anomalias()

@router.delete("/transactions/{id}")
def deletar_transacao(id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    cursor.execute("SELECT id FROM transacoes WHERE id = ?", (id,))
    linha = cursor.fetchone()
    
    if linha is None:
        conexao.close()
        raise HTTPException(status_code=404, detail="Transação não encontrada para exclusão")
        
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()
    
    return {"mensagem": f"Transação de ID {id} deletada com sucesso!"}
