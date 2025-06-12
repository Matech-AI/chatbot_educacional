import subprocess
import sys
import os

if __name__ == "__main__":
    # Start the backend server
    try:
        print("🚀 Iniciando backend...")
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n❌ Backend interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar backend: {e}")

