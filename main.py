#CRIAÇÂO DO BANCO
import sqlite3
import pandas as pd

conexao = sqlite3.connect("banco.db")
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

df = pd.read_json("transacoes.json")
df.to_sql("transacoes", conexao, if_exists="append", index=False)

conexao.commit()
conexao.close()

print(f"Sucesso! {len(df)} linhas foram inseridas no banco de dados.")
