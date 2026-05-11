# 💰 FinanceGuard - Gestão e Detecção de Fraudes

Sistema de gerenciamento de transações financeiras com detecção de anomalias em tempo real, utilizando **FastAPI** para o backend e **Streamlit** para o dashboard interativo.

## 🚀 Tecnologias Utilizadas
- **Python 3.10+**
- **FastAPI**: Criação da API RESTful.
- **Streamlit**: Dashboard interativo para visualização de dados.
- **SQLite**: Banco de dados relacional leve.
- **Pydantic**: Validação de dados.
- **Uvicorn**: Servidor ASGI para rodar a API.

## 📂 Estrutura do Projeto
- `app/`: Contém a lógica da API (rotas, modelos, serviços).
- `data/`: Armazenamento de dados (SQLite e arquivos de dados).
- `scripts/`: Scripts de suporte como configuração de banco de dados.
- `dashboard.py`: Interface interativa (Streamlit) para o usuário final.
- `requirements.txt`: Lista de dependências do projeto.

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
1. **Transações de alto valor na madrugada:** Valor > R$ 3.000 entre 00h e 06h.
2. **Alta frequência:** Múltiplas tentativas de transação (3 ou mais) em curto período.
3. **Transações internacionais suspeitas:** Transações internacionais com valor > R$ 1.000.

---
Projeto desenvolvido para monitoramento financeiro e detecção de comportamentos suspeitos em tempo real.
