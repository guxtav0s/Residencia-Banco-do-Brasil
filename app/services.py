from .repositories import TransacaoRepository
import pandas as pd
import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

def analisar_anomalias():
    # ... (código anterior mantido para compatibilidade)
    linhas = TransacaoRepository.buscar_recentes_para_analise(limite=1000)
    transacoes_suspeitas = []
    
    # Truque de Sênior (Cache): Guarda as médias já calculadas para não sobrecarregar o banco
    medias_por_conta = {}
    
    for linha in linhas:
        transacao = dict(linha)
        motivos = []
        conta_cliente = transacao["conta"]
        
        # --- BUSCA DA MÉDIA HISTÓRICA ---
        if conta_cliente not in medias_por_conta:
            media = TransacaoRepository.calcular_media_historica_conta(conta_cliente)
            medias_por_conta[conta_cliente] = media
            
        media_historica = medias_por_conta[conta_cliente]
        transacao["media_conta"] = media_historica
        
        # --- MOTOR DE REGRAS ---
        if "00:00" <= transacao["hora"] <= "06:00" and transacao["valor"] > 3000:
            motivos.append("Valor anormalmente alto durante a madrugada")
            
        if transacao["tentativas"] >= 3:
            motivos.append(f"Múltiplas tentativas de erro ({transacao['tentativas']} tentativas)")
            
        if transacao["pais"] != "Brasil" and transacao["valor"] > 1000:
            motivos.append(f"Transação internacional de alto valor no país: {transacao['pais']}")
            
        if media_historica > 0 and transacao["valor"] > (media_historica * 3) and transacao["valor"] > 500:
            motivos.append(f"Valor 3x maior que a média histórica da conta (Média: R$ {media_historica:.2f})")
            
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

def analisar_anomalias_ia():
    """Analisa anomalias usando Machine Learning (Isolation Forest)"""
    if not SKLEARN_AVAILABLE:
        return []

    # Busca todas as transações para treinar o modelo
    linhas = TransacaoRepository.buscar_recentes_para_analise(limite=2000)
    if not linhas or len(linhas) < 10: 
        return []

    try:
        df = pd.DataFrame([dict(l) for l in linhas])
        
        # Preparação de Features para a IA
        # Converte hora (HH:MM) para valor numérico (0 a 23.9)
        df['hora_num'] = df['hora'].apply(lambda x: int(x.split(':')[0]) + int(x.split(':')[1])/60 if isinstance(x, str) and ':' in x else 12.0)
        
        # Seleciona features numéricas para o modelo
        features = ['valor', 'hora_num', 'tentativas']
        
        # Garante que não há valores nulos
        X = df[features].fillna(0)
        
        if X.empty:
            return []

        # Inicializa e treina o Isolation Forest
        # contamination=0.03 (reduzido para ser mais seletivo que a regra estatística básica)
        model = IsolationForest(contamination=0.03, random_state=42)
        df['anomaly_score'] = model.fit_predict(X)
        
        # No Isolation Forest, -1 indica anomalia
        anomalias_ia = df[df['anomaly_score'] == -1].copy()
        
        # Formata para retorno
        resultados = []
        for _, row in anomalias_ia.iterrows():
            t = row.to_dict()
            t['motivo_suspeita'] = "🤖 Inteligência Artificial: Comportamento Atípico (Outlier)"
            t['nivel_risco'] = "Médio" if t['valor'] < 5000 else "Alto"
            
            # Remove campos auxiliares da IA antes de enviar para a API/Frontend
            for extra in ['hora_num', 'anomaly_score']:
                if extra in t: del t[extra]
            
            # Garante que campos obrigatórios de anomalia existam
            if 'media_conta' not in t:
                t['media_conta'] = 0.0
                
            resultados.append(t)
            
        return resultados
    except Exception as e:
        print(f"Erro no processamento de IA: {e}")
        return []

def criar_nova_transacao(transacao_data):
    return TransacaoRepository.salvar(transacao_data)