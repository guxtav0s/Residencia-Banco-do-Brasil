# 💰 FinanceGuard - Sistema de Detecção de Fraudes

O **FinanceGuard** é uma solução completa para o monitoramento de transações financeiras e detecção de anomalias em tempo real. O sistema utiliza um motor de regras de negócio aliado a modelos de **Inteligência Artificial (Machine Learning)** para identificar comportamentos suspeitos e prevenir fraudes.

## 🚀 Tecnologias Utilizadas

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Frontend/Dashboard:** [Streamlit](https://streamlit.io/)
- **Banco de Dados:** SQLite (Relacional)
- **Data Science/ML:** Scikit-Learn (Isolation Forest), Pandas, NumPy
- **Validação de Dados:** Pydantic

---

## 📂 Estrutura do Projeto

O projeto segue uma arquitetura modularizada dentro da pasta `src/`, focada em separação de responsabilidades e escalabilidade:

```text
├── src/
│   ├── main.py                # Ponto de entrada da API FastAPI
│   ├── api/                   # Definição de rotas e controllers
│   ├── core/                  # Configurações de banco (config.py) e globais (settings.py)
│   ├── models/                # Schemas de dados e validação Pydantic
│   ├── repositories/          # Camada de acesso ao banco (Queries SQL)
│   ├── services/              # Regras de negócio e lógica de detecção de anomalias
│   └── views/                 # Interface visual (Dashboard Streamlit)
├── data/                      # Base de dados (SQLite e arquivos JSON)
├── notebooks/                 # Análises exploratórias e experimentos de ML
├── tests/                     # Testes unitários e de integração
├── run_dashboard.py           # Script facilitador para iniciar o Dashboard
└── requirements.txt           # Dependências do projeto
```

---

## 🔧 Como Executar

### 1. Clonar o repositório e instalar dependências
```bash
# Instale as bibliotecas necessárias
pip install -r requirements.txt
```

### 2. Configurar o Banco de Dados
Execute o script de setup para criar as tabelas e popular com dados iniciais:
```bash
python scripts/setup_db.py
```

### 3. Iniciar o Backend (API)
A API gerencia todas as operações de banco de dados e o motor de análise:
```bash
uvicorn src.main:app --reload
```
*Acesse a documentação interativa em: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

### 4. Iniciar o Frontend (Dashboard)
Em um novo terminal, execute o script facilitador:
```bash
python run_dashboard.py
```

---

## 🚨 Motor de Detecção de Anomalias

O sistema utiliza dois níveis de proteção:

### 1. Regras de Negócio (Heurísticas)
- **Madrugada de Risco:** Transações acima de R$ 3.000 entre 00:00 e 06:00.
- **Múltiplas Tentativas:** Alerta ao atingir 3 ou mais tentativas de transação.
- **Internacional de Alto Valor:** Transações fora do país acima de R$ 1.000.
- **Desvio de Padrão:** Valores 3x maiores que a média histórica do cliente.

### 2. Inteligência Artificial (Machine Learning)
Utiliza o algoritmo **Isolation Forest** para detectar *outliers* estatísticos, analisando padrões de comportamento que fogem à normalidade do banco de dados, independentemente de regras fixas.

---

## 📊 Dashboard de Visualização
O dashboard permite:
- Visualizar o volume total de transações e cidades atendidas.
- Filtrar transações por categoria, valor e localidade.
- Analisar detalhes de cada anomalia detectada (Nível de Risco e Motivo).
- Simular transações para testar a sensibilidade do motor de regras.

---

## ⚖️ Licença
Este projeto foi desenvolvido para fins de residência tecnológica e monitoramento financeiro.
