import sqlite3
import os

# Caminho para o banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "banco.db")

def conectar_banco():
    conexao = sqlite3.connect(DB_PATH)
    # Isso faz com que os resultados do banco venham como dicionários em vez de tuplas
    conexao.row_factory = sqlite3.Row 
    return conexao
