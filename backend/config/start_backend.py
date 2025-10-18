import subprocess
import sys
import os

if __name__ == "__main__":
    # Start the backend server
    try:
        print("🚀 Iniciando backend...")
        # Get the parent directory (backend) to use as the working directory
        config_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(config_dir)  # Parent directory of config
        
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", "8002",
            "--reload"
        ], check=True, cwd=backend_dir)  # Run from backend directory
    except KeyboardInterrupt:
        print("\n❌ Backend interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar backend: {e}")
