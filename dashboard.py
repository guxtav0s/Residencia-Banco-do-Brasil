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
st.sidebar.title("Finance - BB")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação", ["Visão Geral", "Explorador de Transações", "Detecção de Anomalias", "Testes de Validação"])

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
        
       
        _v = df['valor'].tolist()
        if len(_v) >= 2:
            import statistics as _s
            _med = _s.median(_v)
            _lim = _med + 2.5 * _s.stdev(_v)
            _n   = int((df['valor'] > _lim).sum())
        else:
            _med, _lim, _n = 0, 0, 0

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total de Transações", len(df))
        col2.metric("Volume Total", f"R$ {df['valor'].sum():,.2f}")
        col3.metric("Anomalias Detectadas", len(anomalies) if anomalies else 0)
        col4.metric("Cidades Atendidas", df['cidade'].nunique())
        # Novo card: conta transações com valor acima de mediana + 2.5 × desvio padrão
        col5.metric(
            "Valores Anômalos",
            _n,
            delta=f"Acima de R$ {_lim:,.2f}" if _lim > 0 else "Nenhum alerta",
            delta_color="inverse" if _n > 0 else "off",
            help=f"Transações com valor acima de R$ {_lim:,.2f} (Mediana + 2.5x desvio padrão)"
        )
        
        
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

       
       
        # Slider na sidebar para controlar a sensibilidade da detecção.
        # Padrão 2.5 = bom equilíbrio. Menor = mais alertas disparados.
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Detecção de Valor Anômalo")
        fator_desvio = st.sidebar.slider(
            "Sensibilidade (× desvio padrão)",
            min_value=1.0, max_value=5.0, value=2.5, step=0.5,
            help="Menor = mais alertas. Maior = apenas valores extremos."
        )

    
      
        # Limiar calculado sobre o df filtrado atual.
        # Usa mediana (robusta a outliers) + N desvios do slider.
      
        import statistics as _s
        _v = df['valor'].tolist()
        if len(_v) >= 2:
            _med = _s.median(_v)
            _lim = _med + fator_desvio * _s.stdev(_v)
        else:
            _med, _lim = 0, 0

        df['alerta_valor'] = df['valor'].apply(
            lambda v: f"⚠️ R$ {v:,.2f}" if _lim > 0 and v > _lim else ""
        )

        _total_alertas = int((df['alerta_valor'] != "").sum())
        if _total_alertas > 0:
            st.warning(
                f"⚠️ **{_total_alertas} transação(ões)** com valor anômalo "
                f"— acima de **R$ {_lim:,.2f}** "
                f"({fator_desvio}× desvio | mediana R$ {_med:,.2f})."
            )
        
        
        # --- LÓGICA REFINADA PARA MOSTRAR AS REGRAS ESPECÍFICAS ---
        anomalies = get_anomalies()
        
        # Criamos os mapeamentos garantindo que o ID seja tratado da mesma forma (int)
        mapa_risco = {int(a['id']): a.get('nivel_risco', 'Médio') for a in anomalies} if anomalies else {}
        mapa_motivo = {int(a['id']): a.get('motivo_suspeita', '') for a in anomalies} if anomalies else {}
        
        def calcular_risco(linha):
            tid = int(linha['id'])
            if tid in mapa_risco:
                return mapa_risco[tid]
            if linha['is_fraude'] == 1:
                return 'Alto'
            
           
            # Valor anômalo estatístico eleva o risco para "Médio" mesmo
            # sem disparar nenhuma regra do motor ou flag do banco.
            
            if linha.get('alerta_valor', '') != '':
                return 'Médio'
         
            return 'Baixo'

        def calcular_motivo(linha):
            tid = int(linha['id'])
            if tid in mapa_motivo and mapa_motivo[tid] != "":
                return mapa_motivo[tid]
            if linha['is_fraude'] == 1:
                return "Sinalizada no banco de dados"
            
            #  — Explorador de Transações
            # Valor anômalo estatístico aparece como motivo de suspeita
            # com o múltiplo exato em relação à mediana do conjunto.
          
            if linha.get('alerta_valor', '') != '':
                return f"Valor atípico: {linha['alerta_valor']}"
           
            return '-'

        # Aplicando a lógica
        df['nivel_risco'] = df.apply(calcular_risco, axis=1)
        df['motivo_suspeita'] = df.apply(calcular_motivo, axis=1)
            
        # Reordenando as colunas para colocar Valor e Média Histórica lado a lado
        cols = df.columns.tolist()
        # Move 'media_conta' para a posição logo após 'valor' (que geralmente é a 1)
        if 'media_conta' in cols:
            cols.insert(cols.index('valor') + 1, cols.pop(cols.index('media_conta')))
        
        # Move nivel_risco, motivo_suspeita e alerta_valor para o início
        cols.insert(3, cols.pop(cols.index('nivel_risco'))) 
        cols.insert(4, cols.pop(cols.index('motivo_suspeita')))
        cols.insert(5, cols.pop(cols.index('alerta_valor')))
        
        df = df[cols]

        # --- ESTILIZAÇÃO VISUAL ---
        def destacar_anomalias(row):
            styles = [''] * len(row)
            
            # Cores específicas para a coluna de Nível de Risco
            idx_risco = row.index.get_loc('nivel_risco')
            if row['nivel_risco'] == 'Alto':
                styles[idx_risco] = 'background-color: #ff4b4b; color: white; font-weight: bold'
            elif row['nivel_risco'] == 'Médio':
                styles[idx_risco] = 'background-color: #ffaa00; color: black; font-weight: bold'
            elif row['nivel_risco'] == 'Baixo':
                styles[idx_risco] = 'background-color: #00cc66; color: white; font-weight: bold'
            
            return styles

        st.dataframe(
            df.style.apply(destacar_anomalias, axis=1),
            column_config={
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "media_conta": st.column_config.NumberColumn("Média Histórica (R$)", format="R$ %.2f"),
                "data": "Data",
                "categoria": "Categoria",
               
                # Cabeçalho com ícone ⚠️ e tooltip com o limiar ao passar
                # o mouse, mostrando os parâmetros do cálculo aplicado.
              
                "alerta_valor": st.column_config.TextColumn(
                    "⚠️ Alerta de Valor",
                    help=(
                        f"Transações acima de R$ {_lim:,.2f} "
                        f"({fator_desvio}× desvio padrão | mediana: R$ {_med:,.2f})"
                    ),
                    width="medium",
                ),
                
            },
            hide_index=True
        )
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

elif menu == "Detecção de Anomalias":
    st.title("🚨 Detecção de Anomalias")
    
    # Toggle para IA
    modo_deteccao = st.radio(
        "Método de Detecção",
        ["Regras de Negócio (Padrão)", "Inteligência Artificial (Experimental)"],
        horizontal=True,
        help="Regras: Baseado em limites fixos. IA: Baseado em aprendizado de máquina (Isolation Forest)."
    )
    
    if modo_deteccao == "Regras de Negócio (Padrão)":
        st.markdown("As transações abaixo foram marcadas com base em regras de segurança pré-definidas.")
        anomalies = get_anomalies()
    else:
        st.markdown("As transações abaixo foram identificadas como 'outliers' por um modelo de **Machine Learning**.")
        anomalies = get_anomalies_ia()
        if not anomalies:
            st.info("O modelo de IA precisa de pelo menos 10 transações no banco para realizar a análise.")

   
    # Calcula o limiar global para exibir o badge de valor anômalo
    # nos cards HTML. Base: todas as transações sem filtro.

    import statistics as _s
    _todas = get_transactions()
    if _todas and len(_todas) >= 2:
        _vals = [t['valor'] for t in _todas]
        _med_g = _s.median(_vals)
        _lim_g = _med_g + 2.5 * _s.stdev(_vals)
    else:
        _med_g, _lim_g = 0, float('inf')
   

    if anomalies:
        for a in anomalies:
            risco = a.get('nivel_risco', 'Desconhecido')
            
            if risco == "Alto":
                cor_primaria = "#ff4b4b"
                cor_fundo = "#fff5f5"
            elif risco == "Médio":
                cor_primaria = "#ffaa00"
                cor_fundo = "#fffbee"
            else:
                cor_primaria = "#00cc66"
                cor_fundo = "#f0fff5"

          
            # Badge amarelo aparece no card quando o valor supera o limiar.
            # Mostra o múltiplo exato em relação à mediana global.
            
            if _med_g > 0 and a['valor'] > _lim_g:
                badge_anomalo = (
                    f'<span style="background:#fff3cd; color:#856404; border:1px solid #ffc107;'
                    f' padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold; margin-left:8px;">'
                    f'⚠️ {a["valor"] / _med_g:.1f}x a mediana</span>'
                )
            else:
                badge_anomalo = ""
            

            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid {cor_primaria}; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: {cor_fundo}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="color: {cor_primaria}; margin: 0;">Suspeita: {a.get('motivo_suspeita', 'Motivo não informado')} {badge_anomalo}</h4>
                        <span style="background-color: {cor_primaria}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px;">
                            Risco: {risco}
                        </span>
                    </div>
                    <p style="color: #333; margin-top: 10px; margin-bottom: 0;">
                        <b>ID:</b> {a['id']} | <b>Valor:</b> R$ {a['valor']:.2f} (Média: R$ {a.get('media_conta', 0):.2f}) | <b>Data:</b> {a['data']} às {a['hora']}<br>
                        <b>Local:</b> {a['cidade']}, {a['pais']} | <b>Tipo:</b> {a['tipo_transacao']} | <b>Tentativas:</b> {a['tentativas']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("Nenhuma anomalia detectada no momento. Tudo parece seguro!")

elif menu == "Testes de Validação":
    st.title("🧪 Testes de Validação de Valores")
    st.markdown("Esta aba permite testar manualmente se um valor seria considerado anômalo com base no histórico atual.")

    transactions = get_transactions()
    if transactions:
        df_all = pd.DataFrame(transactions)
        vals = df_all['valor'].tolist()

        if len(vals) >= 2:
            import statistics as _s
            mediana = _s.median(vals)
            desvio = _s.stdev(vals)
            
            st.sidebar.markdown("---")
            sensibilidade = st.sidebar.slider(
                "Ajustar Sensibilidade (Teste)", 
                1.0, 5.0, 2.5, 0.5,
                help="O padrão do sistema é 2.5. Menor = mais sensível."
            )
            
            limiar = mediana + (sensibilidade * desvio)

            # Layout de métricas
            c1, c2, c3 = st.columns(3)
            c1.metric("Mediana do Banco", f"R$ {mediana:,.2f}")
            c2.metric("Desvio Padrão", f"R$ {desvio:,.2f}")
            c3.metric("Limiar de Alerta", f"R$ {limiar:,.2f}", delta=f"sensibilidade {sensibilidade}x")

            st.markdown("---")
            
            # Simulador
            st.subheader("🛠️ Simulador de Transação")
            test_val = st.number_input("Insira um valor para validar (R$):", min_value=0.0, value=float(round(mediana * 1.5, 2)), step=100.0)
            
            if test_val > limiar:
                st.error(f"🚨 **ALERTA!** O valor R$ {test_val:,.2f} está **ACIMA** do limiar de R$ {limiar:,.2f}.")
                st.markdown(f"Este valor é **{test_val/mediana:.1f}x** maior que a mediana do sistema.")
            else:
                st.success(f"✅ **DENTRO DO PADRÃO.** O valor R$ {test_val:,.2f} está abaixo do limiar de R$ {limiar:,.2f}.")
            
            # Gráfico de Distribuição
            st.markdown("---")
            st.subheader("📊 Distribuição de Valores")
            
            # Gráfico de linha para mostrar a distribuição
            chart_data = df_all.sort_values('valor')[['valor']].reset_index(drop=True)
            st.line_chart(chart_data)
            st.info(f"O limiar de corte para novos alertas é de **R$ {limiar:,.2f}**. No gráfico de linha acima, transações que geram picos acima deste valor são consideradas atípicas.")

        else:
            st.warning("Dados insuficientes no banco para calcular estatísticas (mínimo 2 transações).")
    else:
        st.info("Nenhuma transação encontrada no banco de dados para realizar os testes.")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("FinanceGuard v1.1 - Monitoramento em Tempo Real")