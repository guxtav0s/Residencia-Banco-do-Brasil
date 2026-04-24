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
