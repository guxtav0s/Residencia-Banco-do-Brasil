import subprocess
import sys
import os

if __name__ == "__main__":
    # Caminho para o dashboard dentro da nova estrutura
    dashboard_path = os.path.join("src", "views", "dashboard.py")
    
    try:
        subprocess.run(["streamlit", "run", dashboard_path])
    except KeyboardInterrupt:
        print("\nDashboard encerrado.")
    except Exception as e:
        print(f"Erro ao iniciar o dashboard: {e}")
