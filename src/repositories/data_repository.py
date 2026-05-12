import sqlite3
from ..core.config import conectar_banco

class TransacaoRepository:
    @staticmethod
    def buscar_todas(filtros: dict):
        conexao = conectar_banco()
        cursor = conexao.cursor()

        query = """
            SELECT *, 
            (SELECT AVG(valor) FROM transacoes t2 WHERE t2.conta = t1.conta) as media_conta
            FROM transacoes t1 
            WHERE 1=1
        """
        parametros = []

        if filtros.get("categoria"):
            query += " AND categoria = ?"
            parametros.append(filtros["categoria"])
        if filtros.get("cidade"):
            query += " AND cidade = ?"
            parametros.append(filtros["cidade"])
        if filtros.get("valor_min"):
            query += " AND valor >= ?"
            parametros.append(filtros["valor_min"])
        if filtros.get("valor_max"):
            query += " AND valor <= ?"
            parametros.append(filtros["valor_max"])

        query += " LIMIT 100"
        cursor.execute(query, parametros)
        linhas = cursor.fetchall()
        conexao.close()
        
        return [dict(linha) for linha in linhas]
    
    @staticmethod
    def salvar(t):
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        cursor.execute("""
            INSERT INTO transacoes (
                id, valor, data, hora, dia_semana, categoria, conta, 
                cidade, estado, pais, latitude, longitude, tipo_transacao, 
                dispositivo, estabelecimento, tentativas, ip_origem, is_fraude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (t.id, t.valor, t.data, t.hora, t.dia_semana, t.categoria, t.conta, 
              t.cidade, t.estado, t.pais, t.latitude, t.longitude, t.tipo_transacao, 
              t.dispositivo, t.estabelecimento, t.tentativas, t.ip_origem, t.is_fraude))
        conexao.commit()
        conexao.close()

    @staticmethod
    def deletar(id: int):
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM transacoes WHERE id = ?", (id,))
        conexao.commit()
        conexao.close()

    @staticmethod
    def buscar_recentes_para_analise(limite=1000):
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM transacoes ORDER BY data DESC, hora DESC LIMIT ?", (limite,))
        linhas = cursor.fetchall()
        conexao.close()
        return linhas
    
    @staticmethod
    def calcular_media_historica_conta(conta: str):
        conexao = conectar_banco()
        cursor = conexao.cursor()
        cursor.execute("SELECT AVG(valor) FROM transacoes WHERE conta = ?", (conta,))
        resultado = cursor.fetchone()
        conexao.close()
        
        if resultado[0] is not None:
            return float(resultado[0])
        return 0.0
