from ..repositories.data_repository import TransacaoRepository
import pandas as pd
import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Cache em memória do modelo treinado (evita re-treinar a cada requisição)
_MODELO_FRAUDE = None


def _montar_features(df):
    """Constroi as features numericas usadas para estimar a probabilidade de fraude.
    NAO altera os dados originais: apenas le e deriva colunas auxiliares."""
    df = df.copy()
    df['hora_num'] = df['hora'].apply(
        lambda x: int(x.split(':')[0]) + int(x.split(':')[1]) / 60
        if isinstance(x, str) and ':' in x else 12.0
    )
    df['is_internacional'] = (df['pais'] != 'Brasil').astype(int)
    df['is_madrugada'] = (df['hora_num'] <= 6).astype(int)
    df['valor_vs_media'] = df.apply(
        lambda r: r['valor'] / r['media_conta']
        if r.get('media_conta') and r['media_conta'] > 0 else 1.0,
        axis=1
    )
    features = ['valor', 'hora_num', 'tentativas', 'is_internacional',
                'is_madrugada', 'valor_vs_media']
    return df[features].fillna(0)


def _treinar_modelo_fraude():
    """Treina (uma unica vez) um modelo de Regressao Logistica usando a coluna
    is_fraude que JA EXISTE na base. Os dados sao apenas lidos, nunca alterados."""
    global _MODELO_FRAUDE
    if _MODELO_FRAUDE is not None:
        return _MODELO_FRAUDE
    if not SKLEARN_AVAILABLE:
        return None

    linhas = TransacaoRepository.buscar_recentes_para_analise(limite=30000)
    if not linhas or len(linhas) < 50:
        return None

    df = pd.DataFrame([dict(l) for l in linhas])
    if 'is_fraude' not in df.columns or df['is_fraude'].nunique() < 2:
        return None

    # Preenche media_conta para o calculo de valor_vs_media
    if 'media_conta' not in df.columns:
        df['media_conta'] = df.groupby('conta')['valor'].transform('mean')

    X = _montar_features(df)
    y = df['is_fraude'].astype(int)

    modelo = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, class_weight='balanced')),
    ])
    modelo.fit(X, y)
    _MODELO_FRAUDE = modelo
    return modelo


def calcular_probabilidade_fraude(transacao: dict):
    """Recebe uma transacao (dict) e retorna a probabilidade (%) de ser fraude,
    junto com o nivel de risco. Nao grava nada no banco."""
    modelo = _treinar_modelo_fraude()
    if modelo is None:
        return {
            "probabilidade_fraude": None,
            "nivel_risco": "Indisponivel",
            "mensagem": "Modelo indisponivel (sklearn ausente ou dados insuficientes).",
        }

    # Garante media_conta da conta informada (apenas leitura)
    conta = str(transacao.get('conta', ''))
    if not transacao.get('media_conta'):
        transacao['media_conta'] = TransacaoRepository.calcular_media_historica_conta(conta)

    df = pd.DataFrame([transacao])
    X = _montar_features(df)
    prob = float(modelo.predict_proba(X)[0][1]) * 100

    if prob >= 70:
        risco = "Alto"
    elif prob >= 40:
        risco = "Medio"
    else:
        risco = "Baixo"

    return {
        "probabilidade_fraude": round(prob, 2),
        "nivel_risco": risco,
        "media_conta": round(float(transacao['media_conta']), 2),
    }

def analisar_anomalias():
    linhas = TransacaoRepository.buscar_recentes_para_analise(limite=1000)
    transacoes_suspeitas = []
    
    medias_por_conta = {}
    
    for linha in linhas:
        transacao = dict(linha)
        motivos = []
        conta_cliente = transacao["conta"]
        
        if conta_cliente not in medias_por_conta:
            media = TransacaoRepository.calcular_media_historica_conta(conta_cliente)
            medias_por_conta[conta_cliente] = media
            
        media_historica = medias_por_conta[conta_cliente]
        transacao["media_conta"] = media_historica
        
        if "00:00" <= transacao["hora"] <= "06:00" and transacao["valor"] > 1500:
            motivos.append("Valor anormalmente alto durante a madrugada")
            
        if transacao["tentativas"] >= 2:
            motivos.append(f"Múltiplas tentativas de erro ({transacao['tentativas']} tentativas)")
            
        if transacao["pais"] != "Brasil" and transacao["valor"] > 500:
            motivos.append(f"Transação internacional de alto valor no país: {transacao['pais']}")
            
        if media_historica > 0 and transacao["valor"] > (media_historica * 2) and transacao["valor"] > 300:
            motivos.append(f"Valor 2x maior que a média histórica da conta (Média: R$ {media_historica:.2f})")
            
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
    if not SKLEARN_AVAILABLE:
        return []

    linhas = TransacaoRepository.buscar_recentes_para_analise(limite=2000)
    if not linhas or len(linhas) < 10: 
        return []

    try:
        df = pd.DataFrame([dict(l) for l in linhas])

        # Feature 1: hora como número (já existia)
        df['hora_num'] = df['hora'].apply(
            lambda x: int(x.split(':')[0]) + int(x.split(':')[1])/60
            if isinstance(x, str) and ':' in x else 12.0
        )

        # Feature 2: transação internacional?
        df['is_internacional'] = (df['pais'] != 'Brasil').astype(int)

        # Feature 3: valor relativo à média histórica da conta
        df['valor_vs_media'] = df.apply(
            lambda r: r['valor'] / r['media_conta']
            if r.get('media_conta') and r['media_conta'] > 0 else 1.0,
            axis=1
        )

        # Feature 4: é fim de semana?
        df['is_fds'] = pd.to_datetime(df['data'], errors='coerce').dt.dayofweek.isin([5, 6]).astype(int)

        features = ['valor', 'hora_num', 'tentativas', 'is_internacional', 'valor_vs_media', 'is_fds']
        X = df[features].fillna(0)
        
        if X.empty:
            return []

        model = IsolationForest(contamination=0.10, random_state=42)
        df['anomaly_score'] = model.fit_predict(X)
        
        anomalias_ia = df[df['anomaly_score'] == -1].copy()
        
        resultados = []
        for _, row in anomalias_ia.iterrows():
            t = row.to_dict()

            # Motivo detalhado baseado no contexto
            razoes = ["Padrão atípico detectado por IA"]
            if t.get('pais', 'Brasil') != 'Brasil':
                razoes.append(f"País estrangeiro: {t['pais']}")
            media = t.get('media_conta', 0)
            if media > 0 and t['valor'] > media * 2:
                razoes.append(f"Valor {t['valor']/media:.1f}x acima da média da conta")
            if t.get('tentativas', 0) >= 3:
                razoes.append(f"{t['tentativas']} tentativas")
            hora = t.get('hora', '12:00')
            if hora <= '06:00':
                razoes.append("Horário suspeito (madrugada)")
            t['motivo_suspeita'] = " | ".join(razoes)

            # Nível de risco baseado em score contextual
            score_risco = 0
            if t['valor'] > 5000:                                    score_risco += 2
            if t.get('tentativas', 0) >= 3:                          score_risco += 2
            if t.get('pais', 'Brasil') != 'Brasil':                  score_risco += 1
            if media > 0 and t['valor'] > media * 3:                 score_risco += 2
            t['nivel_risco'] = "Alto" if score_risco >= 3 else "Médio" if score_risco >= 1 else "Baixo"

            for extra in ['hora_num', 'anomaly_score', 'is_internacional', 'valor_vs_media', 'is_fds']:
                if extra in t:
                    del t[extra]

            # Garante media_conta preenchida
            media_val = t.get('media_conta')
            if not media_val or media_val == 0.0:
                media_val = TransacaoRepository.calcular_media_historica_conta(str(t.get('conta', '')))
            t['media_conta'] = round(float(media_val), 2) if media_val else 0.0

            resultados.append(t)
            
        return resultados
    except Exception as e:
        print(f"Erro no processamento de IA: {e}")
        return []

def criar_nova_transacao(transacao_data):
    return TransacaoRepository.salvar(transacao_data)