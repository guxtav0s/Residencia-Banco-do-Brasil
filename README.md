<<<<<<< HEAD
# 💰 FinanceGuard - Gestão e Detecção de Fraudes

Sistema de gerenciamento de transações financeiras com detecção de anomalias em tempo real, utilizando **FastAPI** para o backend e **Streamlit** para o dashboard interativo.

## 🚀 Tecnologias Utilizadas
- **Python 3.10+**
- **FastAPI**: Criação da API RESTful.
- **Streamlit**: Dashboard interativo para visualização de dados.
- **SQLite**: Banco de dados relacional leve.
- **Pydantic**: Validação de dados.

## 📂 Estrutura do Projeto
- `app/`: Contém a lógica da API (rotas, modelos, serviços).
- `data/`: Armazenamento de dados (SQLite e JSON inicial).
- `scripts/`: Scripts de suporte como configuração de banco de dados.
- `dashboard.py`: Interface interativa para o usuário final.

## 🔧 Como Executar

### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Prepare o banco de dados
```bash
python scripts/setup_db.py
```

### 3. Inicie a API (Backend)
```bash
uvicorn app.main:app --reload
```

### 4. Inicie o Dashboard (Frontend)
Em um novo terminal, execute:
```bash
streamlit run dashboard.py
```

## 🚨 Regras de Anomalias
O sistema detecta automaticamente:
1. Transações de alto valor (> R$ 3.000) na madrugada (00h - 06h).
2. Múltiplas tentativas de transação (3 ou mais).
3. Transações internacionais de alto valor (> R$ 1.000).

---
Desenvolvido como projeto de monitoramento financeiro.
=======
# 🏦 API de Análise e Validação de Transações

Este projeto consiste em uma API desenvolvida em Python para processar, armazenar e validar transações financeiras. O sistema consome dados de transações, armazena em um banco de dados relacional e aplica regras de negócio específicas (como detecção de possíveis fraudes ou anomalias) antes de retornar os resultados via endpoints.

## Estrutura do Projeto

Abaixo está a organização dos arquivos principais do projeto:

* **`api.py`**: Contém as rotas da API e a lógica de comunicação com os endpoints (desenvolvido com frameworks como FastAPI ou Flask).
* **`main.py`**: Script principal responsável por inicializar o sistema, orquestrar a leitura inicial dos dados e configurar a conexão.
* **`banco.db`**: Banco de dados SQLite (`.db`) onde as transações processadas e validadas são armazenadas.
* **`transacoes.json`**: Arquivo de dados brutos contendo o lote de transações financeiras (dataset) que será consumido e analisado pelo sistema.
* **`.gitignore`**: Arquivo para ocultar pastas como `__pycache__` e outros arquivos temporários do controle de versão do Git.

## Regras de Negócio Aplicadas

A API não apenas armazena os dados, mas atua como um filtro rigoroso. Durante a requisição e processamento, as seguintes regras de negócio são verificadas no banco de dados:

1.  **Validação de Saldo/Limite:** A transação só é aprovada se o valor não exceder parâmetros de limite predefinidos.
2.  **Detecção de Anomalias (Antifraude):** Identificação de transações com valores atípicos ou frequência muito alta em um curto período de tempo para a mesma conta.
3.  **Integridade dos Dados:** Verificação de campos obrigatórios no JSON antes da inserção no banco de dados SQLite.

## Tecnologias Utilizadas

* **Python 3.x**
* **FastAPI / Flask** (Criação das rotas da API)
* **SQLite** (Banco de dados leve e integrado)
* **Pandas** (Para manipulação e leitura eficiente do arquivo `transacoes.json`)
* **Uvicorn** (Servidor ASGI, se utilizado FastAPI)

## Como Executar o Projeto

**1. Clone o repositório:**
```bash
git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
cd seu-repositorio
>>>>>>> 064fd263ccb0ec8f98a3631171e781769d004876
