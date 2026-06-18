import sqlite3
import os

# Caminho para o banco de dados - Saindo de src/core para a raiz
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "banco.db")

def conectar_banco():
    """Cria uma conexão com o banco SQLite e retorna o objeto de conexão."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
