import sqlite3
import pandas as pd
import os

# Caminhos ajustados
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "banco.db")
JSON_PATH = os.path.join(BASE_DIR, "data", "transacoes.json")

def setup():
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))

    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY,
        valor REAL,
        data TEXT,
        hora TEXT,
        dia_semana TEXT,
        categoria TEXT,
        conta TEXT,
        cidade TEXT,
        estado TEXT,
        pais TEXT,
        latitude REAL,
        longitude REAL,
        tipo_transacao TEXT,
        dispositivo TEXT,
        estabelecimento TEXT,
        tentativas INTEGER,
        ip_origem TEXT,
        is_fraude INTEGER
    )""")

    if os.path.exists(JSON_PATH):
        df = pd.read_json(JSON_PATH)
        df.to_sql("transacoes", conexao, if_exists="append", index=False)
        print(f"Sucesso! {len(df)} linhas foram inseridas no banco de dados.")
    else:
        print(f"Aviso: Arquivo {JSON_PATH} não encontrado.")

    conexao.commit()
    conexao.close()

if __name__ == "__main__":
    setup()
