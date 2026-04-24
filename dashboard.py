import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="FinanceGuard - Dashboard de Transações", layout="wide", page_icon="💰")

# URL base da API FastAPI
API_URL = "http://127.0.0.1:8000"

# Funções auxiliares para comunicação com a API
def get_transactions(params=None):
    try:
        response = requests.get(f"{API_URL}/transactions", params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return None

def get_anomalies():
    try:
        response = requests.get(f"{API_URL}/anomalies")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return None

def create_transaction(data):
    try:
        response = requests.post(f"{API_URL}/transactions", json=data)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"detail": str(e)}

def delete_transaction(transaction_id):
    try:
        response = requests.delete(f"{API_URL}/transactions/{transaction_id}")
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"detail": str(e)}

# Título e Sidebar
st.sidebar.title("💳 FinanceGuard")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação", ["Visão Geral", "Explorador de Transações", "Detecção de Anomalias"])

# Verificação de conexão com a API
api_status = get_transactions({"limit": 1})
if api_status is None:
    st.error("⚠️ Não foi possível conectar à API FastAPI. Certifique-se de que ela está rodando em http://127.0.0.1:8000")
    st.stop()

# --- ABA: VISÃO GERAL ---
if menu == "Visão Geral":
    st.title("📊 Visão Geral do Sistema")
    
    transactions = get_transactions()
    anomalies = get_anomalies()
    
    if transactions:
        df = pd.DataFrame(transactions)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Transações", len(df))
        col2.metric("Volume Total", f"R$ {df['valor'].sum():,.2f}")
        col3.metric("Anomalias Detectadas", len(anomalies) if anomalies else 0)
        col4.metric("Cidades Atendidas", df['cidade'].nunique())
        
        st.subheader("Distribuição por Categoria")
        st.bar_chart(df['categoria'].value_counts())
    else:
        st.info("Nenhuma transação encontrada para gerar estatísticas.")

# --- ABA: EXPLORADOR DE TRANSAÇÕES ---
elif menu == "Explorador de Transações":
    st.title("🔍 Explorador de Transações")
    
    # Filtros na Sidebar
    st.sidebar.subheader("Filtros")
    f_categoria = st.sidebar.text_input("Categoria")
    f_cidade = st.sidebar.text_input("Cidade")
    f_tipo = st.sidebar.selectbox("Tipo", ["", "debito", "credito", "pix"])
    f_v_min = st.sidebar.number_input("Valor Mínimo", value=0.0)
    f_v_max = st.sidebar.number_input("Valor Máximo", value=1000000.0)
    
    params = {}
    if f_categoria: params["categoria"] = f_categoria
    if f_cidade: params["cidade"] = f_cidade
    if f_tipo: params["tipo_transacao"] = f_tipo
    params["valor_min"] = f_v_min
    params["valor_max"] = f_v_max
    
    # Botão para deletar na Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Gerenciar Transação")
    del_id = st.sidebar.number_input("ID para Deletar", min_value=1, step=1)
    if st.sidebar.button("Excluir Registro", help="Deleta a transação permanentemente"):
        status, res = delete_transaction(del_id)
        if status == 200:
            st.sidebar.success(res["mensagem"])
        else:
            st.sidebar.error(res.get("detail", "Erro ao deletar"))

    # Listagem
    transactions = get_transactions(params)
    if transactions:
        df = pd.DataFrame(transactions)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Nenhuma transação encontrada com os filtros selecionados.")
        
    # Formulário para nova transação
    with st.expander("➕ Adicionar Nova Transação"):
        with st.form("new_trans"):
            c1, c2, c3 = st.columns(3)
            new_id = c1.number_input("ID", min_value=1, step=1)
            new_valor = c2.number_input("Valor", min_value=0.01)
            new_data = c3.date_input("Data", datetime.now()).strftime("%Y-%m-%d")
            
            c4, c5, c6 = st.columns(3)
            new_hora = c4.text_input("Hora (HH:MM)", "12:00")
            new_cat = c5.text_input("Categoria", "Lazer")
            new_tipo = c6.selectbox("Tipo", ["debito", "credito", "pix"])
            
            c7, c8, c9 = st.columns(3)
            new_cid = c7.text_input("Cidade", "São Paulo")
            new_est = c8.text_input("Estado", "SP")
            new_pais = c9.text_input("País", "Brasil")
            
            # Campos padrão para simplificar o exemplo
            submitted = st.form_submit_button("Salvar Transação")
            if submitted:
                payload = {
                    "id": new_id, "valor": new_valor, "data": new_data, "hora": new_hora,
                    "dia_semana": "Segunda", "categoria": new_cat, "conta": "12345-6",
                    "cidade": new_cid, "estado": new_est, "pais": new_pais,
                    "latitude": -23.55, "longitude": -46.63, "tipo_transacao": new_tipo,
                    "dispositivo": "Smartphone", "estabelecimento": "Loja Teste",
                    "tentativas": 1, "ip_origem": "127.0.0.1", "is_fraude": 0
                }
                status, res = create_transaction(payload)
                if status == 200:
                    st.success("Transação salva com sucesso!")
                else:
                    st.error(f"Erro: {res.get('detail')}")

# --- ABA: DETECÇÃO DE ANOMALIAS ---
elif menu == "Detecção de Anomalias":
    st.title("🚨 Detecção de Anomalias")
    st.markdown("As transações abaixo foram marcadas pelo sistema com base em regras de segurança.")
    
    anomalies = get_anomalies()
    if anomalies:
        for a in anomalies:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ff4b4b; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #fff5f5">
                    <h4 style="color: #ff4b4b; margin: 0">Suspeita: {a['motivo_suspeita']}</h4>
                    <p style="color: #333">
                        <b>ID:</b> {a['id']} | <b>Valor:</b> R$ {a['valor']:.2f} | <b>Data:</b> {a['data']} às {a['hora']}<br>
                        <b>Local:</b> {a['cidade']}, {a['pais']} | <b>Tipo:</b> {a['tipo_transacao']} | <b>Tentativas:</b> {a['tentativas']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("Nenhuma anomalia detectada no momento. Tudo parece seguro!")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("FinanceGuard v1.0 - Monitoramento em Tempo Real")
