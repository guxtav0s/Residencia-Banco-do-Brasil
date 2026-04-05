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
# Substitua APENAS a rota GET /transactions atual por esta:

@app.get("/transactions")
def listar_transacoes(
    categoria: str = None,
    cidade: str = None,
    tipo_transacao: str = None,
    valor_min: float = None,
    valor_max: float = None
):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Começamos com uma query base (O 'WHERE 1=1' é um truque para facilitar a adição de vários 'AND' depois)
    query = "SELECT * FROM transacoes WHERE 1=1"
    parametros = []

    # Verificamos quais filtros o usuário enviou e montamos a query dinamicamente
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

    # Mantemos o limite para não travar a API
    query += " LIMIT 100"

    # Executamos a query passando a lista de parâmetros que foram preenchidos
    cursor.execute(query, parametros)
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

# 4. GET /anomalies - Detecção de anomalias com base em regras de negócio
@app.get("/anomalies")
def detectar_anomalias():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    # Buscamos as últimas 1000 transações para análise
    cursor.execute("SELECT * FROM transacoes ORDER BY id DESC LIMIT 1000")
    linhas = cursor.fetchall()
    conexao.close()
    
    transacoes_suspeitas = []
    
    for linha in linhas:
        transacao = dict(linha)
        motivos = []
        
        # ---------------------------------------------------------
        # REGRA 1: Valor alto durante a madrugada (Comportamento)
        # ---------------------------------------------------------
        # Transações acima de R$ 3.000 entre meia-noite e 6 da manhã
        if "00:00" <= transacao["hora"] <= "06:00" and transacao["valor"] > 3000:
            motivos.append("Valor anormalmente alto durante a madrugada")
            
        # ---------------------------------------------------------
        # REGRA 2: Força bruta / Múltiplas tentativas (Contexto)
        # ---------------------------------------------------------
        # 3 ou mais tentativas de senha/validação
        if transacao["tentativas"] >= 3:
            motivos.append(f"Múltiplas tentativas de erro ({transacao['tentativas']} tentativas)")
            
        # ---------------------------------------------------------
        # REGRA 3: Transação Internacional (Contexto)
        # ---------------------------------------------------------
        # Qualquer transação fora do Brasil acima de R$ 1.000
        if transacao["pais"] != "Brasil" and transacao["valor"] > 1000:
            motivos.append(f"Transação internacional de alto valor no país: {transacao['pais']}")
            
        # Se a transação disparou pelo menos um "motivo", ela é uma anomalia!
        if motivos:
            # Juntamos os motivos (caso ela caia em mais de uma regra)
            transacao["motivo_suspeita"] = " | ".join(motivos)
            transacoes_suspeitas.append(transacao)
            
    return transacoes_suspeitas

# 5. DELETE /transactions/{id} - Deleta uma transação específica
@app.delete("/transactions/{id}")
def deletar_transacao(id: int):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    # 1. Verifica se a transação existe no banco antes de deletar
    cursor.execute("SELECT id FROM transacoes WHERE id = ?", (id,))
    linha = cursor.fetchone()
    
    if linha is None:
        conexao.close()
        # Retorna erro 404 (Not Found) se o ID não existir
        raise HTTPException(status_code=404, detail="Transação não encontrada para exclusão")
        
    # 2. Se existir, executa o comando SQL para deletar
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()
    
    return {"mensagem": f"Transação de ID {id} deletada com sucesso!"}