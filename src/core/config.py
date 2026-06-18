import os

# Caminho para o banco de dados - Saindo de src/core para a raiz
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "banco.db")
