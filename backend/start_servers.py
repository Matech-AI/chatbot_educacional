#!/usr/bin/env python3
"""
Script para iniciar ambos os servidores (RAG e API) com as portas corretas
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path


def check_dependencies():
    """Verificar se as dependências estão instaladas"""
    print("🔍 Verificando dependências...")

    try:
        import fastapi
        import uvicorn
        import aiohttp
        print("✅ Dependências básicas OK")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r config/requirements.txt")
        return False


def check_env_file():
    """Verificar se o arquivo .env existe"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Arquivo .env não encontrado")
        print("💡 Copie env.example para .env e configure suas chaves")
        return False
    return True


def start_api_server():
    """Iniciar servidor API na porta 8000"""
    print("🚀 Iniciando servidor API (porta 8000)...")

    try:
        # Iniciar servidor API em background
        api_process = subprocess.Popen([
            sys.executable, "api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Aguardar um pouco para o servidor inicializar
        time.sleep(3)

        # Verificar se o processo ainda está rodando
        if api_process.poll() is None:
            print("✅ Servidor API iniciado com sucesso (porta 8000)")
            return api_process
        else:
            stdout, stderr = api_process.communicate()
            print(f"❌ Erro ao iniciar servidor API:")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return None

    except Exception as e:
        print(f"❌ Erro ao iniciar servidor API: {e}")
        return None


def start_rag_server():
    """Iniciar servidor RAG na porta 8001"""
    print("🧠 Iniciando servidor RAG (porta 8001)...")

    try:
        # Iniciar servidor RAG em background
        rag_process = subprocess.Popen([
            sys.executable, "rag_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Aguardar um pouco para o servidor inicializar
        time.sleep(3)

        # Verificar se o processo ainda está rodando
        if rag_process.poll() is None:
            print("✅ Servidor RAG iniciado com sucesso (porta 8001)")
            return rag_process
        else:
            stdout, stderr = rag_process.communicate()
            print(f"❌ Erro ao iniciar servidor RAG:")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return None

    except Exception as e:
        print(f"❌ Erro ao iniciar servidor RAG: {e}")
        return None


def test_servers():
    """Testar se os servidores estão respondendo"""
    print("\n🧪 Testando servidores...")

    import requests

    # Testar servidor API (porta 8000)
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor API respondendo (porta 8000)")
        else:
            print(f"⚠️  Servidor API retornou status {response.status_code}")
    except Exception as e:
        print(f"❌ Servidor API não está respondendo: {e}")

    # Testar servidor RAG (porta 8001)
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor RAG respondendo (porta 8001)")
        else:
            print(f"⚠️  Servidor RAG retornou status {response.status_code}")
    except Exception as e:
        print(f"❌ Servidor RAG não está respondendo: {e}")


def cleanup(api_process, rag_process):
    """Limpar processos ao sair"""
    print("\n🛑 Parando servidores...")

    if api_process:
        api_process.terminate()
        api_process.wait()
        print("✅ Servidor API parado")

    if rag_process:
        rag_process.terminate()
        rag_process.wait()
        print("✅ Servidor RAG parado")


def main():
    """Função principal"""
    print("🚀 Iniciando Sistema RAG + API")
    print("=" * 50)
    print("📊 Configuração de Portas:")
    print("   API Server: http://localhost:8000")
    print("   RAG Server: http://localhost:8001")
    print("=" * 50)

    # Verificações iniciais
    if not check_dependencies():
        sys.exit(1)

    if not check_env_file():
        print("⚠️  Continuando sem arquivo .env...")

    api_process = None
    rag_process = None

    try:
        # Iniciar servidores
        api_process = start_api_server()
        if not api_process:
            print("❌ Falha ao iniciar servidor API")
            sys.exit(1)

        rag_process = start_rag_server()
        if not rag_process:
            print("❌ Falha ao iniciar servidor RAG")
            cleanup(api_process, None)
            sys.exit(1)

        # Testar servidores
        test_servers()

        print("\n🎉 SISTEMA INICIADO COM SUCESSO!")
        print("=" * 50)
        print("📊 Servidores rodando:")
        print("   API Server: http://localhost:8000")
        print("   RAG Server: http://localhost:8001")
        print("\n💡 Para testar:")
        print("   python test_system.py")
        print("\n🛑 Pressione Ctrl+C para parar os servidores")

        # Manter os processos rodando
        try:
            while True:
                time.sleep(1)
                # Verificar se os processos ainda estão rodando
                if api_process and api_process.poll() is not None:
                    print("❌ Servidor API parou inesperadamente")
                    break
                if rag_process and rag_process.poll() is not None:
                    print("❌ Servidor RAG parou inesperadamente")
                    break
        except KeyboardInterrupt:
            print("\n🛑 Interrupção recebida...")

    except Exception as e:
        print(f"❌ Erro durante inicialização: {e}")
    finally:
        cleanup(api_process, rag_process)
        print("👋 Sistema parado")


if __name__ == "__main__":
    main()
