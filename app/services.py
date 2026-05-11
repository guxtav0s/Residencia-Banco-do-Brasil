from .repositories import TransacaoRepository

def analisar_anomalias():
    linhas = TransacaoRepository.buscar_recentes_para_analise(limite=1000)
    transacoes_suspeitas = []
    
    # Truque de Sênior (Cache): Guarda as médias já calculadas para não sobrecarregar o banco
    medias_por_conta = {}
    
    for linha in linhas:
        transacao = dict(linha)
        motivos = []
        conta_cliente = transacao["conta"]
        
        # --- BUSCA DA MÉDIA HISTÓRICA ---
        # Se ainda não calculamos a média dessa conta, vamos no Repository buscar
        if conta_cliente not in medias_por_conta:
            media = TransacaoRepository.calcular_media_historica_conta(conta_cliente)
            medias_por_conta[conta_cliente] = media
            
        media_historica = medias_por_conta[conta_cliente]
        transacao["media_conta"] = media_historica
        
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
            
        # REGRA 4: (NOVA) Desvio da Média Histórica
        # Se a transação for 3 vezes maior que a média histórica E o valor for maior que 500 reais
        if media_historica > 0 and transacao["valor"] > (media_historica * 3) and transacao["valor"] > 500:
            motivos.append(f"Valor 3x maior que a média histórica da conta (Média: R$ {media_historica:.2f})")
            
        # --- CLASSIFICAÇÃO DE RISCO ---
        if motivos:
            if len(motivos) > 1 or transacao["valor"] > 10000 or transacao.get("tentativas", 0) >= 3:
                risco = "Alto"
            elif len(motivos) == 1:
                risco = "Médio"
            else:
                risco = "Baixo"

            transacao["motivo_suspeita"] = " | ".join(motivos)
            transacao["nivel_risco"] = risco
            
            transacoes_suspeitas.append(transacao)
            
    return transacoes_suspeitas

def criar_nova_transacao(transacao_data):
    return TransacaoRepository.salvar(transacao_data)