import streamlit as st
import requests
import pandas as pd
import statistics as _s
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(
    page_title="FinanceGuard - Dashboard de Transações",
    layout="wide",
    
)

API_URL = "http://127.0.0.1:8000"


def get_transactions(params=None):
    try:
        r = requests.get(f"{API_URL}/transactions", params=params)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return None

def get_anomalies():
    try:
        r = requests.get(f"{API_URL}/anomalies")
        return r.json() if r.status_code == 200 else []
    except Exception:
        return None

def get_anomalies_ia():
    try:
        r = requests.get(f"{API_URL}/anomalies/ai")
        return r.json() if r.status_code == 200 else []
    except Exception:
        return None

def get_anomalies_ia_explained(apenas_alto_risco: bool = True):
    try:
        r = requests.get(
            f"{API_URL}/anomalies/ai-explained",
            params={"apenas_alto_risco": str(apenas_alto_risco).lower()},
            timeout=130,
        )
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            return "429"
        else:
            return []
    except requests.exceptions.Timeout:
        return "timeout"
    except Exception:
        return None

def chat_com_ia(transacao: dict, historico: list, pergunta: str) -> str:
    try:
        r = requests.post(
            f"{API_URL}/anomalies/chat",
            json={"transacao": transacao, "historico": historico, "pergunta": pergunta},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json().get("resposta", "Sem resposta.")
        return f"Erro {r.status_code} ao consultar a IA."
    except Exception as e:
        return f"Erro de conexão: {e}"

def validar_fraude(data):
    try:
        r = requests.post(f"{API_URL}/validacao/fraude", json=data, timeout=60)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def create_transaction(data):
    try:
        r = requests.post(f"{API_URL}/transactions", json=data)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"detail": str(e)}

def delete_transaction(transaction_id):
    try:
        r = requests.delete(f"{API_URL}/transactions/{transaction_id}")
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"detail": str(e)}


def get_motives():
    try:
        r = requests.get(f"{API_URL}/motives")
        return r.json() if r.status_code == 200 else []
    except Exception:
        return None

def save_motive(data):
    try:
        r = requests.post(f"{API_URL}/motives", json=data)
        return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Sidebar / Navegação
# ---------------------------------------------------------------------------
st.sidebar.title("Finance - BB")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação",
    ["Visão Geral", "Explorador de Transações", "Detecção de Anomalias", "Registro de Motivos", "Testes de Validação", "Validação do Cliente"],
    key="nav_menu",
)

api_status = get_transactions({"limit": 1})
if api_status is None:
    st.error(" Não foi possível conectar à API FastAPI. Certifique-se de que ela está rodando em http://127.0.0.1:8000")
    st.stop()


# ---------------------------------------------------------------------------
# ABA: VISÃO GERAL
# ---------------------------------------------------------------------------
if menu == "Visão Geral":
    st.title("Visão Geral do Sistema")
    transactions = get_transactions()
    anomalies = get_anomalies()
    if transactions:
        df = pd.DataFrame(transactions)
        _v = df["valor"].tolist()
        if len(_v) >= 2:
            _med = _s.median(_v)
            _lim = _med + 2.5 * _s.stdev(_v)
            _n   = int((df["valor"] > _lim).sum())
        else:
            _med, _lim, _n = 0, 0, 0
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total de Transações", len(df))
        col2.metric("Volume Total", f"R$ {df['valor'].sum():,.2f}")
        col3.metric("Anomalias Detectadas", len(anomalies) if anomalies else 0)
        col4.metric("Cidades Atendidas", df["cidade"].nunique())
        col5.metric(
            "Valores Anômalos", _n,
            delta=f"Acima de R$ {_lim:,.2f}" if _lim > 0 else "Nenhum alerta",
            delta_color="inverse" if _n > 0 else "off",
        )
        st.subheader("Distribuição por Categoria")
        cat_counts = df["categoria"].dropna().value_counts()
        cat_counts = cat_counts[cat_counts > 0]
        if not cat_counts.empty:
            st.bar_chart(cat_counts)
    else:
        st.info("Nenhuma transação encontrada para gerar estatísticas.")


# ---------------------------------------------------------------------------
# ABA: EXPLORADOR DE TRANSAÇÕES
# ---------------------------------------------------------------------------
elif menu == "Explorador de Transações":
    st.title("Explorador de Transações")
    st.sidebar.subheader("Filtros")
    f_categoria = st.sidebar.text_input("Categoria")
    f_cidade    = st.sidebar.text_input("Cidade")
    f_tipo      = st.sidebar.selectbox("Tipo", ["", "debito", "credito", "pix"])
    f_v_min     = st.sidebar.number_input("Valor Mínimo", value=0.0)
    f_v_max     = st.sidebar.number_input("Valor Máximo", value=1000000.0)
    params = {}
    if f_categoria: params["categoria"]      = f_categoria
    if f_cidade:    params["cidade"]         = f_cidade
    if f_tipo:      params["tipo_transacao"] = f_tipo
    params["valor_min"] = f_v_min
    params["valor_max"] = f_v_max
    st.sidebar.markdown("---")
    st.sidebar.subheader("Gerenciar Transação")
    del_id = st.sidebar.number_input("ID para Deletar", min_value=1, step=1)
    if st.sidebar.button("Excluir Registro"):
        status, res = delete_transaction(del_id)
        if status == 200:
            st.sidebar.success(res["mensagem"])
        else:
            st.sidebar.error(res.get("detail", "Erro ao deletar"))
    transactions = get_transactions(params)
    if transactions:
        df = pd.DataFrame(transactions)
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Detecção de Valor Anômalo")
        fator_desvio = st.sidebar.slider("Sensibilidade (× desvio padrão)", min_value=1.0, max_value=5.0, value=2.5, step=0.5)
        _v = df["valor"].tolist()
        if len(_v) >= 2:
            _med = _s.median(_v)
            _lim = _med + fator_desvio * _s.stdev(_v)
        else:
            _med, _lim = 0, 0
        df["alerta_valor"] = df["valor"].apply(lambda v: f"⚠️ R$ {v:,.2f}" if _lim > 0 and v > _lim else "")
        _total_alertas = int((df["alerta_valor"] != "").sum())
        if _total_alertas > 0:
            st.warning(f"⚠️ **{_total_alertas} transação(ões)** com valor anômalo — acima de **R$ {_lim:,.2f}**")
        anomalies = get_anomalies()
        mapa_risco  = {int(a["id"]): a.get("nivel_risco", "Médio") for a in anomalies} if anomalies else {}
        mapa_motivo = {int(a["id"]): a.get("motivo_suspeita", "") for a in anomalies} if anomalies else {}
        def calcular_risco(linha):
            tid = int(linha["id"])
            if tid in mapa_risco: return mapa_risco[tid]
            if linha["is_fraude"] == 1: return "Alto"
            if linha.get("alerta_valor", ""): return "Médio"
            return "Baixo"
        def calcular_motivo(linha):
            tid = int(linha["id"])
            if tid in mapa_motivo and mapa_motivo[tid]: return mapa_motivo[tid]
            if linha["is_fraude"] == 1: return "Sinalizada no banco de dados"
            if linha.get("alerta_valor", ""): return f"Valor atípico: {linha['alerta_valor']}"
            return "-"
        df["nivel_risco"]     = df.apply(calcular_risco, axis=1)
        df["motivo_suspeita"] = df.apply(calcular_motivo, axis=1)
        def destacar_anomalias(row):
            styles = [""] * len(row)
            idx_risco = row.index.get_loc("nivel_risco")
            if   row["nivel_risco"] == "Alto":  styles[idx_risco] = "background-color: #ff4b4b; color: white; font-weight: bold"
            elif row["nivel_risco"] == "Médio": styles[idx_risco] = "background-color: #ffaa00; color: black; font-weight: bold"
            elif row["nivel_risco"] == "Baixo": styles[idx_risco] = "background-color: #00cc66; color: white; font-weight: bold"
            return styles
        st.dataframe(df.style.apply(destacar_anomalias, axis=1), hide_index=True)
    else:
        st.warning("Nenhuma transação encontrada com os filtros selecionados.")
    with st.expander(" + Adicionar Nova Transação"):
        with st.form("new_trans"):
            c1, c2, c3 = st.columns(3)
            new_id    = c1.number_input("ID", min_value=1, step=1)
            new_valor = c2.number_input("Valor", min_value=0.01)
            new_data  = c3.date_input("Data", datetime.now()).strftime("%Y-%m-%d")
            c4, c5, c6 = st.columns(3)
            new_hora = c4.text_input("Hora (HH:MM)", "12:00")
            new_cat  = c5.text_input("Categoria", "Lazer")
            new_tipo = c6.selectbox("Tipo", ["debito", "credito", "pix"])
            c7, c8, c9 = st.columns(3)
            new_cid  = c7.text_input("Cidade", "São Paulo")
            new_est  = c8.text_input("Estado", "SP")
            new_pais = c9.text_input("País", "Brasil")
            if st.form_submit_button("Salvar Transação"):
                payload = {
                    "id": new_id, "valor": new_valor, "data": new_data, "hora": new_hora,
                    "dia_semana": "Segunda", "categoria": new_cat, "conta": "12345-6",
                    "cidade": new_cid, "estado": new_est, "pais": new_pais,
                    "latitude": -23.55, "longitude": -46.63, "tipo_transacao": new_tipo,
                    "dispositivo": "Smartphone", "estabelecimento": "Loja Teste",
                    "tentativas": 1, "ip_origem": "127.0.0.1", "is_fraude": 0,
                }
                status, res = create_transaction(payload)
                if status == 200:
                    st.success("Transação salva com sucesso!")
                else:
                    st.error(f"Erro: {res.get('detail')}")


# ---------------------------------------------------------------------------
# ABA: DETECÇÃO DE ANOMALIAS
# ---------------------------------------------------------------------------
elif menu == "Detecção de Anomalias":
    st.title(" Detecção de Anomalias")

    if "modo_deteccao" not in st.session_state:
        st.session_state.modo_deteccao = "Regras de Negócio (Padrão)"

    MODOS = ["Regras de Negócio (Padrão)", " IA Generativa — Gemini"]
    modo_deteccao = st.radio(
        "Método de Detecção", MODOS,
        index=MODOS.index(st.session_state.modo_deteccao) if st.session_state.modo_deteccao in MODOS else 0,
        horizontal=True, key="radio_modo",
    )
    if modo_deteccao != st.session_state.modo_deteccao:
        for k in list(st.session_state.keys()):
            if k.startswith(("anomalies_", "chat_")):
                del st.session_state[k]
        st.session_state.modo_deteccao = modo_deteccao
        st.rerun()

    _todas = get_transactions() or []
    _vals  = [t["valor"] for t in _todas if isinstance(t.get("valor"), (int, float))]
    _med_g = _s.median(_vals) if len(_vals) >= 2 else 0
    _lim_g = (_med_g + 2.5 * _s.stdev(_vals)) if len(_vals) >= 2 else float("inf")

    anomalies          = []
    modo_ia_generativa = False

    if modo_deteccao == "Regras de Negócio (Padrão)":
        st.markdown("Transações marcadas com base em **regras de segurança pré-definidas**.")
        if "anomalies_regras" not in st.session_state:
            st.session_state.anomalies_regras = get_anomalies()
        anomalies = st.session_state.anomalies_regras or []

    else:
        modo_ia_generativa = True
        st.markdown(
            "Detecção via **IA Híbrida** (Algoritmo Local + Gemini) com explicação detalhada e score de risco."
        )
        apenas_alto = st.checkbox("Analisar apenas risco Alto (economiza cota)", value=True, key="check_alto")
        cache_key   = f"anomalies_ia_{apenas_alto}"
        if cache_key not in st.session_state:
            with st.spinner(" Analisando anomalias com Gemini... (Isso pode levar até 1 minuto)"):
                st.session_state[cache_key] = get_anomalies_ia_explained(apenas_alto_risco=apenas_alto)
        
        res = st.session_state[cache_key]
        
        if res == "timeout":
            st.error("⏰ A análise demorou muito. Tente marcar a opção 'Analisar apenas risco Alto' para ser mais rápido.")
            anomalies = []
        elif res == "429":
            st.error("🚦 Limite de requisições da IA atingido. Aguarde 1 minuto e tente novamente.")
            anomalies = []
        elif res is None:
            st.error("❌ Erro de conexão com o servidor ou API Key inválida no .env.")
            anomalies = []
        else:
            anomalies = res

    # ------------------------------------------------------------------
    # Renderização
    # ------------------------------------------------------------------
    if anomalies:
        for idx, a in enumerate(anomalies):
            risco = a.get("nivel_risco", "Desconhecido")
            if   risco == "Alto":  cor_p, cor_f = "#ff4b4b", "#fff5f5"
            elif risco == "Médio": cor_p, cor_f = "#ffaa00", "#fffbee"
            else:                  cor_p, cor_f = "#00cc66", "#f0fff5"

            badge_anomalo = ""
            if _med_g and a["valor"] > _lim_g:
                badge_anomalo = (
                    f'<span style="background:#fff3cd;color:#856404;border:1px solid #ffc107;'
                    f'padding:3px 10px;border-radius:12px;font-size:12px;font-weight:bold;margin-left:8px;">'
                    f' {a["valor"]/_med_g:.1f}x mediana</span>'
                )

            score = a.get("score_fraude", 0)
            badge_score = ""
            if modo_ia_generativa and score:
                cs = "#ff4b4b" if score >= 70 else "#ffaa00" if score >= 40 else "#00cc66"
                badge_score = (
                    f'<span style="background:{cs}22;color:{cs};border:1px solid {cs};'
                    f'padding:3px 10px;border-radius:12px;font-size:12px;font-weight:bold;margin-left:8px;">'
                    f' Score: {score}/100</span>'
                )

            bloco_ia = ""
            if modo_ia_generativa:
                explicacao  = a.get("explicacao_ia", "")
                acao        = a.get("acao_sugerida", "")
                tipo_fraude = a.get("possivel_tipo_fraude", "")
                criticidade = a.get("nivel_criticidade", "")
                indicadores = a.get("indicadores_detectados", [])
                _cores = {"Crítico": ("#ff4b4b","#fff0f0"), "Alto": ("#ff8c00","#fff8f0"),
                          "Moderado": ("#ffaa00","#fffbee"), "Baixo": ("#00aa55","#f0fff5")}
                _cc, _cf = _cores.get(criticidade, ("#534AB7","#f0f4ff"))
                badge_crit = (
                    f'<span style="background:{_cf};color:{_cc};border:1px solid {_cc};'
                    f'padding:2px 10px;border-radius:10px;font-size:11px;font-weight:bold;margin-left:8px;">'
                    f'Criticidade: {criticidade}</span>'
                ) if criticidade else ""
                tags_ind = ""
                if indicadores:
                    tags = "".join(
                        f'<span style="display:inline-block;background:#fff3cd;color:#856404;'
                        f'border:1px solid #ffc107;padding:2px 8px;border-radius:10px;'
                        f'font-size:11px;margin:2px 3px 2px 0;">{ind}</span>'
                        for ind in indicadores
                    )
                    tags_ind = f'<div style="margin-top:8px;"><p style="margin:0 0 4px;font-size:12px;color:#555;font-weight:bold;">🔍 Indicadores:</p>{tags}</div>'
                bloco_ia = f"""
                <div style="margin-top:12px;padding:12px 14px;background:#f0f4ff;
                            border-left:4px solid #534AB7;border-radius:6px;">
                    <p style="margin:0 0 10px;font-size:13px;color:#534AB7;font-weight:bold;">
                         Análise Gemini {badge_crit}
                    </p>
                    {"<p style='margin:0 0 6px;font-size:12px;color:#555;'> <b>Tipo suspeito:</b> " + tipo_fraude + "</p>" if tipo_fraude else ""}
                    {"<p style='margin:0 0 8px;color:#333;font-size:13px;'>" + explicacao + "</p>" if explicacao else ""}
                    {"<p style='margin:0 0 4px;color:#333;font-size:13px;'><b>Ação sugerida:</b> " + acao + "</p>" if acao else ""}
                    {tags_ind}
                </div>"""

            card_html = f"""
            <div style="border:1px solid {cor_p};padding:15px;border-radius:10px;
                        margin-bottom:4px;background-color:{cor_f};font-family:sans-serif;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <h4 style="color:{cor_p};margin:0;flex:1;">
                        Suspeita: {a.get('motivo_suspeita','Motivo não informado')}
                        {badge_anomalo}{badge_score}
                    </h4>
                    <span style="background:{cor_p};color:white;padding:4px 12px;
                                 border-radius:20px;font-weight:bold;font-size:14px;
                                 white-space:nowrap;margin-left:12px;">
                        Risco: {risco}
                    </span>
                </div>
                <p style="color:#333;margin-top:10px;margin-bottom:0;">
                    <b>ID:</b> {a['id']} |
                    <b>Valor:</b> R$ {a['valor']:.2f} (Média: R$ {a.get('media_conta',0):.2f}) |
                    <b>Data:</b> {a['data']} às {a['hora']}<br>
                    <b>Local:</b> {a['cidade']}, {a['pais']} |
                    <b>Tipo:</b> {a['tipo_transacao']} |
                    <b>Tentativas:</b> {a['tentativas']}
                </p>
                {bloco_ia}
            </div>"""

            altura_card = 400 if (modo_ia_generativa and bloco_ia) else 150
            components.html(f'<div style="padding:2px 2px;">{card_html}</div>',
                            height=altura_card, scrolling=False)

            # Botão para Salvar Motivo (abaixo do card components)
            if modo_ia_generativa and a.get("explicacao_ia"):
                if st.button(f"📥 Registrar Motivo # {a['id']}", key=f"save_{a['id']}"):
                    payload = {
                        "transacao_id": a["id"],
                        "explicacao": a["explicacao_ia"],
                        "score": a["score_fraude"],
                        "indicadores": a["indicadores_detectados"]
                    }
                    if save_motive(payload):
                        st.success(f"Análise da transação {a['id']} registrada com sucesso!")
                    else:
                        st.error("Erro ao registrar análise.")

    else:
        if anomalies is not None:
            st.success(" Nenhuma anomalia detectada. Tudo parece seguro!")



# ---------------------------------------------------------------------------
# ABA: REGISTRO DE MOTIVOS
# ---------------------------------------------------------------------------
elif menu == "Registro de Motivos":
    st.title("📚 Registro Histórico de Motivos")
    st.markdown("Esta tabela contém todas as análises de suspeitas que foram registradas pelos analistas ou pelo sistema.")
    
    motivos = get_motives()
    if motivos:
        df_motivos = pd.DataFrame(motivos)
        
        # Renomear colunas para melhor visualização
        df_motivos = df_motivos.rename(columns={
            "transacao_id": "ID Transação",
            "explicacao": "Análise Técnica",
            "score": "Score de Fraude",
            "indicadores": "Indicadores",
            "data_analise": "Data da Análise",
            "valor": "Valor (R$)",
            "conta": "Conta do Cliente",
            "cidade": "Cidade"
        })
        
        # Reordenar colunas
        cols = ["Data da Análise", "ID Transação", "Conta do Cliente", "Valor (R$)", "Cidade", "Score de Fraude", "Análise Técnica", "Indicadores"]
        df_motivos = df_motivos[cols]
        
        # Estilização
        def highlight_score(val):
            color = 'red' if val > 70 else 'orange' if val > 40 else 'green'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_motivos.style.map(highlight_score, subset=["Score de Fraude"]),
            hide_index=True,
            use_container_width=True
        )
        
        st.download_button(
            "⬇️ Exportar Relatório (CSV)",
            df_motivos.to_csv(index=False).encode('utf-8'),
            "relatorio_motivos_fraude.csv",
            "text/csv",
            key='download-csv'
        )
    else:
        st.info("Ainda não há motivos registrados. Vá em 'Detecção de Anomalias' para registrar as primeiras análises.")


# ---------------------------------------------------------------------------
# ABA: TESTES DE VALIDAÇÃO
# ---------------------------------------------------------------------------
elif menu == "Testes de Validação":
    st.title(" Testes de Validação de Valores")
    st.markdown("Esta aba permite testar manualmente se um valor seria considerado anômalo.")
    transactions = get_transactions()
    if transactions:
        df_all = pd.DataFrame(transactions)
        vals   = df_all["valor"].tolist()
        if len(vals) >= 2:
            mediana = _s.median(vals)
            desvio  = _s.stdev(vals)
            st.sidebar.markdown("---")
            sensibilidade = st.sidebar.slider("Ajustar Sensibilidade (Teste)", 1.0, 5.0, 2.5, 0.5)
            limiar = mediana + (sensibilidade * desvio)
            c1, c2, c3 = st.columns(3)
            c1.metric("Mediana do Banco",  f"R$ {mediana:,.2f}")
            c2.metric("Desvio Padrão",     f"R$ {desvio:,.2f}")
            c3.metric("Limiar de Alerta",  f"R$ {limiar:,.2f}", delta=f"sensibilidade {sensibilidade}x")
            st.markdown("---")
            st.subheader(" Simulador de Transação")
            test_val = st.number_input("Insira um valor para validar (R$):", min_value=0.0, value=float(round(mediana * 1.5, 2)), step=100.0)
            if test_val > limiar:
                st.error(f" **ALERTA!** O valor R$ {test_val:,.2f} está **ACIMA** do limiar de R$ {limiar:,.2f}.")
                st.markdown(f"Este valor é **{test_val/mediana:.1f}x** maior que a mediana do sistema.")
            else:
                st.success(f" **DENTRO DO PADRÃO.** O valor R$ {test_val:,.2f} está abaixo do limiar de R$ {limiar:,.2f}.")
            st.markdown("---")
            st.subheader(" Validação por Probabilidade de Fraude (IA)")
            st.caption("Estima a chance (%) de uma transação ser fraude usando um modelo treinado sobre a base existente. Nenhum dado é gravado.")
            colp1, colp2 = st.columns(2)
            with colp1:
                p_valor = st.number_input("Valor (R$)", min_value=0.0, value=float(round(mediana * 1.5, 2)), step=100.0, key="pf_valor")
                p_hora  = st.text_input("Hora (HH:MM)", value="03:00", key="pf_hora")
                p_tent  = st.number_input("Tentativas", min_value=0, value=1, step=1, key="pf_tent")
            with colp2:
                p_pais  = st.text_input("País", value="Brasil", key="pf_pais")
                p_conta = st.text_input("Conta (opcional)", value="", key="pf_conta")
            if st.button(" Calcular probabilidade de fraude", key="pf_btn"):
                payload = {
                    "valor": p_valor, "hora": p_hora, "tentativas": int(p_tent),
                    "pais": p_pais, "conta": p_conta or None,
                }
                resultado = validar_fraude(payload)
                if not resultado:
                    st.error("Não foi possível obter a validação. Verifique se a API está rodando.")
                elif resultado.get("probabilidade_fraude") is None:
                    st.warning(resultado.get("mensagem", "Modelo indisponível."))
                else:
                    prob  = resultado["probabilidade_fraude"]
                    risco = resultado["nivel_risco"]
                    st.metric("Probabilidade de Fraude", f"{prob:.2f}%", delta=f"Risco {risco}")
                    st.progress(min(int(prob), 100))
                    if risco == "Alto":
                        st.error(f" Risco ALTO — {prob:.2f}% de chance de fraude.")
                    elif risco == "Medio":
                        st.warning(f" Risco MÉDIO — {prob:.2f}% de chance de fraude.")
                    else:
                        st.success(f" Risco BAIXO — {prob:.2f}% de chance de fraude.")
            st.markdown("---")
            st.subheader(" Distribuição de Valores")
            chart_data = (
                df_all.sort_values("valor")[["valor"]]
                .replace([float("inf"), float("-inf")], pd.NA)
                .dropna()
                .reset_index(drop=True)
            )
            if not chart_data.empty:
                st.line_chart(chart_data)
            st.info(f"O limiar de corte para novos alertas é de **R$ {limiar:,.2f}**.")
        else:
            st.warning("Dados insuficientes no banco para calcular estatísticas (mínimo 2 transações).")
    else:
        st.info("Nenhuma transação encontrada no banco de dados.")




# ---------------------------------------------------------------------------
# ABA: VALIDAÇÃO DO CLIENTE
# ---------------------------------------------------------------------------
elif menu == "Validação do Cliente":
    st.title("Validação do Cliente")
    st.markdown("Simulação de notificação push enviada ao cliente para confirmar transações suspeitas.")

    TRANSACOES_SUSPEITAS = [
        {
            "id": 1042,
            "descricao": "Compra na Apple Store Internet",
            "valor": 12450.00,
            "local": "Lisboa, Portugal",
            "ip": "177.203.11.89",
            "data": "06/06/2026",
            "hora": "15:09",
            "tipo": "Compra Internacional",
            "motivo_alerta": "Transação internacional de alto valor fora do padrão do usuário",
        },
        {
            "id": 1078,
            "descricao": "Pix para conta desconhecida",
            "valor": 8900.00,
            "local": "São Paulo, Brasil",
            "ip": "189.45.220.11",
            "data": "06/06/2026",
            "hora": "02:37",
            "tipo": "Pix",
            "motivo_alerta": "Pix de alto valor realizado de madrugada para destinatário nunca usado",
        },
        {
            "id": 1095,
            "descricao": "Saque em caixa eletrônico",
            "valor": 5000.00,
            "local": "Buenos Aires, Argentina",
            "ip": "200.108.55.33",
            "data": "05/06/2026",
            "hora": "23:51",
            "tipo": "Saque",
            "motivo_alerta": "Saque em país estrangeiro sem histórico de viagem",
        },
    ]

    if "val_idx" not in st.session_state:
        st.session_state.val_idx = 0
    if "val_respostas" not in st.session_state:
        st.session_state.val_respostas = {}
    if "val_acoes" not in st.session_state:
        st.session_state.val_acoes = {}

    idx = st.session_state.val_idx
    total = len(TRANSACOES_SUSPEITAS)
    tx = TRANSACOES_SUSPEITAS[idx]
    tx_id = tx["id"]
    ja_respondeu = tx_id in st.session_state.val_respostas

    # ------------------------------------------------------------------
    # Protótipo de celular via components.html
    # ------------------------------------------------------------------
    phone_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body {{
        background: transparent;
        display: flex;
        justify-content: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      }}
      .phone {{
        width: 300px;
        background: #111111;
        border: 6px solid #2a2a2a;
        border-radius: 36px;
        box-shadow: 0 0 0 2px #3a3a3a, 0 16px 48px rgba(0,0,0,0.65);
        overflow: hidden;
        display: flex;
        flex-direction: column;
      }}
      .notch-bar {{
        background: #1a1a1a;
        height: 32px;
        display: flex;
        align-items: flex-end;
        justify-content: center;
        flex-shrink: 0;
      }}
      .notch {{
        width: 80px;
        height: 16px;
        background: #2a2a2a;
        border-radius: 0 0 12px 12px;
      }}
      .content {{
        padding: 14px 16px 22px 16px;
        display: flex;
        flex-direction: column;
        gap: 0;
        flex: 1;
      }}
      .status-bar {{
        display: flex;
        justify-content: space-between;
        font-size: 10px;
        color: #555;
        margin-bottom: 14px;
        letter-spacing: 0.3px;
      }}
      .app-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 16px;
        padding-bottom: 14px;
        border-bottom: 1px solid #222;
      }}
      .app-icon {{
        width: 36px;
        height: 36px;
        background: #a93226;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        color: white;
        font-weight: bold;
        flex-shrink: 0;
        letter-spacing: -0.5px;
      }}
      .app-name {{
        font-size: 14px;
        font-weight: 700;
        color: #eeeeee;
        line-height: 1.2;
      }}
      .app-sub {{
        font-size: 10px;
        color: #666;
        margin-top: 1px;
      }}
      .alert-card {{
        background: #181824;
        border: 1.5px solid #c0392b;
        border-radius: 12px;
        padding: 14px;
        flex: 1;
      }}
      .alert-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
      }}
      .alert-badge {{
        background: #c0392b;
        color: white;
        padding: 3px 9px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
      }}
      .alert-meta {{
        color: #555;
        font-size: 9px;
      }}
      .alert-title {{
        font-size: 14px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 6px;
        line-height: 1.35;
      }}
      .alert-reason {{
        font-size: 10px;
        color: #666;
        margin-bottom: 14px;
        line-height: 1.55;
      }}
      .info-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-bottom: 2px;
      }}
      .info-cell {{
        background: #111120;
        border-radius: 8px;
        padding: 8px 10px;
      }}
      .info-label {{
        font-size: 9px;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
        display: block;
      }}
      .info-value {{
        font-size: 11px;
        color: #cccccc;
        font-weight: 600;
        line-height: 1.3;
      }}
      .info-value.highlight {{
        color: #e07070;
        font-size: 15px;
        font-weight: 700;
      }}
      .info-value.mono {{
        font-family: monospace;
        color: #d09040;
        font-size: 10px;
      }}
      .divider {{
        border: none;
        border-top: 1px solid #222233;
        margin: 14px 0 12px 0;
      }}
      .question {{
        text-align: center;
        font-size: 11px;
        color: #aaaaaa;
        font-style: italic;
        line-height: 1.5;
      }}
      .nav-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 16px;
        padding: 0 2px;
      }}
      .nav-text {{
        font-size: 10px;
        color: #3a3a3a;
      }}
      .nav-count {{
        font-size: 11px;
        color: #555;
        background: #1e1e1e;
        padding: 3px 10px;
        border-radius: 10px;
        border: 1px solid #2a2a2a;
      }}
      .home-bar {{
        width: 80px;
        height: 4px;
        background: #333;
        border-radius: 2px;
        margin: 18px auto 0 auto;
      }}
    </style>
    </head>
    <body>
      <div class="phone">
        <div class="notch-bar"><div class="notch"></div></div>
        <div class="content">
          <div class="status-bar">
            <span>{tx['hora']}</span>
            <span>FinanceGuard</span>
          </div>
          <div class="app-header">
            <div class="app-icon">FG</div>
            <div>
              <div class="app-name">FinanceGuard</div>
              <div class="app-sub">Alerta de Segurança</div>
            </div>
          </div>
          <div class="alert-card">
            <div class="alert-header">
              <span class="alert-badge">Alerta</span>
              <span class="alert-meta">ID #{tx_id} &middot; {tx['data']}</span>
            </div>
            <div class="alert-title">{tx['descricao']}</div>
            <div class="alert-reason">{tx['motivo_alerta']}</div>
            <div class="info-grid">
              <div class="info-cell">
                <span class="info-label">Valor</span>
                <span class="info-value highlight">R$ {tx['valor']:,.2f}</span>
              </div>
              <div class="info-cell">
                <span class="info-label">Local</span>
                <span class="info-value">{tx['local']}</span>
              </div>
              <div class="info-cell">
                <span class="info-label">IP de origem</span>
                <span class="info-value mono">{tx['ip']}</span>
              </div>
              <div class="info-cell">
                <span class="info-label">Tipo</span>
                <span class="info-value">{tx['tipo']}</span>
              </div>
            </div>
            <hr class="divider">
            <div class="question">Esta transação foi realizada por você?</div>
          </div>
          <div class="nav-bar">
            <span class="nav-text">anterior</span>
            <span class="nav-count">{idx + 1} / {total}</span>
            <span class="nav-text">proxima</span>
          </div>
        </div>
        <div class="home-bar"></div>
      </div>
    </body>
    </html>
    """
    components.html(phone_html, height=620, scrolling=False)

    # Navegação
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
    with nav_col1:
        if st.button("Anterior", disabled=(idx == 0)):
            st.session_state.val_idx = max(0, idx - 1)
            st.rerun()
    with nav_col2:
        st.markdown(
            f"<div style='text-align:center;padding:4px 0;font-size:13px;color:#aaa;'>"
            f"Transacao <b style='color:white;'>{idx + 1}</b> de <b style='color:white;'>{total}</b></div>",
            unsafe_allow_html=True,
        )
    with nav_col3:
        if st.button("Proxima", disabled=(idx == total - 1)):
            st.session_state.val_idx = min(total - 1, idx + 1)
            st.rerun()

    st.markdown("---")

    # ------------------------------------------------------------------
    # Botões de resposta (apenas se ainda não respondeu)
    # ------------------------------------------------------------------
    if not ja_respondeu:
        b_col1, b_col2, b_col3 = st.columns([1, 2, 1])
        with b_col2:
            c_nao, c_sim = st.columns(2)
            with c_nao:
                if st.button("Nao fui eu", use_container_width=True, type="primary"):
                    st.session_state.val_respostas[tx_id] = "nao_fui"
                    try:
                        requests.patch(
                            f"{API_URL}/transactions/{tx_id}",
                            json={"is_fraude": 1, "confirmado_usuario": False},
                            timeout=5,
                        )
                    except Exception:
                        pass
                    st.rerun()
            with c_sim:
                if st.button("Fui eu", use_container_width=True):
                    st.session_state.val_respostas[tx_id] = "fui_eu"
                    try:
                        requests.patch(
                            f"{API_URL}/transactions/{tx_id}",
                            json={"is_fraude": 0, "confirmado_usuario": True},
                            timeout=5,
                        )
                    except Exception:
                        pass
                    st.rerun()

    # ------------------------------------------------------------------
    # Resultado após resposta
    # ------------------------------------------------------------------
    else:
        resposta = st.session_state.val_respostas[tx_id]

        if resposta == "fui_eu":
            st.success("Transação confirmada pelo usuário. Nenhuma ação necessária.")
            st.info("A transação foi registrada como legítima e o alerta foi encerrado automaticamente.")

        else:
            st.error("Fraude confirmada pelo usuário. O cliente informou que não realizou esta transação.")

            st.markdown(
                """
                <div style="background:#2a1a1a;border:1px solid #c0392b;border-radius:10px;padding:16px 20px;margin:12px 0;">
                    <div style="font-size:15px;font-weight:700;color:#e74c3c;margin-bottom:10px;">
                        Painel do Analista — Ação Necessária
                    </div>
                    <div style="font-size:13px;color:#ddd;line-height:1.7;">
                        O usuário negou esta transação. A conta pode estar comprometida.<br>
                        Como a transação <b>não foi realizada pelo titular</b>, a recomendação é o
                        <b style="color:#e07070;">bloqueio imediato da conta</b> para evitar novas fraudes.<br>
                        Um canal de comunicação com o cliente também deve ser aberto para suporte.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("**Selecione a ação a ser tomada:**")

            acao_ja_tomada = st.session_state.val_acoes.get(tx_id)

            if not acao_ja_tomada:
                a_col1, a_col2, a_col3 = st.columns(3)

                with a_col1:
                    if st.button(
                        "Bloquear Conta",
                        use_container_width=True,
                        type="primary",
                        help="Recomendado: bloqueia imediatamente a conta do usuário",
                    ):
                        st.session_state.val_acoes[tx_id] = "bloqueio"
                        try:
                            requests.post(
                                f"{API_URL}/transactions/{tx_id}/block",
                                json={"motivo": "Fraude confirmada pelo usuário", "acao": "bloqueio_conta"},
                                timeout=5,
                            )
                        except Exception:
                            pass
                        st.rerun()

                with a_col2:
                    if st.button(
                        "Contatar Cliente",
                        use_container_width=True,
                        help="Abre canal de comunicação com o cliente via SMS/e-mail",
                    ):
                        st.session_state.val_acoes[tx_id] = "contato"
                        try:
                            requests.post(
                                f"{API_URL}/transactions/{tx_id}/block",
                                json={"motivo": "Fraude confirmada pelo usuário", "acao": "contato_cliente"},
                                timeout=5,
                            )
                        except Exception:
                            pass
                        st.rerun()

                with a_col3:
                    if st.button(
                        "Abrir Ocorrencia",
                        use_container_width=True,
                        help="Registra uma ocorrência formal para investigação interna",
                    ):
                        st.session_state.val_acoes[tx_id] = "ocorrencia"
                        try:
                            requests.post(
                                f"{API_URL}/transactions/{tx_id}/block",
                                json={"motivo": "Fraude confirmada pelo usuário", "acao": "ocorrencia"},
                                timeout=5,
                            )
                        except Exception:
                            pass
                        st.rerun()

                st.caption(
                    "Nota: como a transação nao foi realizada pelo usuário, "
                    "o bloqueio de conta é a ação mais indicada. "
                    "Nao há justificativa para manter a conta ativa enquanto há risco de fraude em andamento."
                )

            else:
                MSGS_ACAO = {
                    "bloqueio": (
                        "**Conta bloqueada com sucesso.**\n\n"
                        "A conta foi suspensa imediatamente. O cliente receberá uma notificação "
                        "e deverá entrar em contato com a central para desbloqueio após verificação de identidade."
                    ),
                    "contato": (
                        "**Canal de comunicação aberto.**\n\n"
                        "O cliente será contatado via SMS e e-mail cadastrado. "
                        "Recomenda-se ainda acionar o bloqueio preventivo da conta enquanto o caso é investigado."
                    ),
                    "ocorrencia": (
                        "**Ocorrência registrada.**\n\n"
                        "O caso foi encaminhado para a equipe de prevenção a fraudes. "
                        "ID de ocorrência: **OCO-{:05d}**. Recomenda-se o bloqueio preventivo da conta.".format(tx_id * 7 + 1001)
                    ),
                }
                st.success(MSGS_ACAO.get(acao_ja_tomada, "Ação registrada."))

    # ------------------------------------------------------------------
    # Resumo geral das respostas
    # ------------------------------------------------------------------
    if st.session_state.val_respostas:
        st.markdown("---")
        st.subheader("Resumo das Validações")
        r_cols = st.columns(3)
        pendentes   = total - len(st.session_state.val_respostas)
        confirmadas = sum(1 for v in st.session_state.val_respostas.values() if v == "fui_eu")
        fraudes     = sum(1 for v in st.session_state.val_respostas.values() if v == "nao_fui")
        r_cols[0].metric("Confirmadas pelo usuario", confirmadas)
        r_cols[1].metric("Fraudes confirmadas", fraudes,
                         delta=f"-{fraudes} anomalia(s)" if fraudes else None,
                         delta_color="inverse" if fraudes else "off")
        r_cols[2].metric("Pendentes de resposta", pendentes)

        if fraudes > 0:
            st.warning(
                f"{fraudes} transacao(oes) confirmada(s) como fraude. "
                "Certifique-se de que todas as acoes necessarias foram tomadas no painel acima."
            )


# Footer
st.sidebar.markdown("---")
st.sidebar.caption("FinanceGuard v1.5 - Monitoramento em Tempo Real")