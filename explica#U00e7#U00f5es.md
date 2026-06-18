# Explicações do Projeto

- **src/main.py**: Ponto de entrada que inicializa a API e coordena as rotas e serviços.
- **src/ai/anomaly_detector.py**: Contém a lógica de IA para treinar modelos e detectar anomalias em transações.
- **src/controllers/transaction_controller.py**: Gerencia as requisições HTTP e direciona o fluxo entre o usuário e o repositório.
- **src/core/database.py**: Responsável pela conexão com o SQLite e gerenciamento de sessões do banco.
- **src/models/transaction_model.py**: Define a estrutura da tabela de transações e a representação de dados no sistema.
- **src/repositories/transaction_repository.py**: Abstrai o acesso aos dados, realizando operações de persistência (CRUD) no banco.
- **src/services/anomaly_detection.py**: Orquestra a execução do detector de anomalias dentro do fluxo de negócio.
- **src/schemas/transactions_schema.py**: Define as regras de validação e serialização dos dados de transação.
- **data/banco.db**: Banco de dados SQLite onde as transações e registros são armazenados permanentemente.
- **scripts/setup_db.py**: Script utilitário para criar e configurar a estrutura inicial do banco de dados.
- **tests/test_anomaly.py**: Conjunto de testes automatizados para validar a eficácia da detecção de anomalias.
- **requirements.txt**: Lista todas as bibliotecas e dependências necessárias para executar o projeto.
