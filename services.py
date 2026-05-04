from .database import conectar_banco

def analisar_anomalias():
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
        
        # --- MOTOR DE REGRAS ---
        
        # REGRA 1: Valor alto durante a madrugada
        if "00:00" <= transacao["hora"] <= "06:00" and transacao["valor"] > 3000:
            motivos.append("Valor anormalmente alto durante a madrugada")
            
        # REGRA 2: Força bruta / Múltiplas tentativas
        if transacao["tentativas"] >= 3:
            motivos.append(f"Múltiplas tentativas de erro ({transacao['tentativas']} tentativas)")
            
        # REGRA 3: Transação Internacional
        if transacao["pais"] != "Brasil" and transacao["valor"] > 1000:
            motivos.append(f"Transação internacional de alto valor no país: {transacao['pais']}")
            
        # --- CLASSIFICAÇÃO DE RISCO ---
        if motivos:
            # Definindo a lógica de risco:
            # ALTO: Mais de um motivo detectado OU valor muito elevado (> 10.000) OU muitas tentativas (> 5)
            if len(motivos) > 1 or transacao["valor"] > 10000 or transacao.get("tentativas", 0) >= 3:
                risco = "Alto"
            # MÉDIO: Apenas um motivo detectado (mas não crítico)
            elif len(motivos) == 1:
                risco = "Médio"
            # BAIXO: Outros casos (opcional, aqui como já filtramos anomalias, o mínimo é Médio)
            else:
                risco = "Baixo"

            # Adicionando os novos campos ao dicionário da transação
            transacao["motivo_suspeita"] = " | ".join(motivos)
            transacao["nivel_risco"] = risco
            
            transacoes_suspeitas.append(transacao)
            
    return transacoes_suspeitas