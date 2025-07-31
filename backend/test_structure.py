#!/usr/bin/env python3
"""
Script de teste para verificar a estrutura de arquivos após a reorganização.
Este script não tenta importar módulos, apenas verifica se os arquivos estão nos lugares corretos.
"""

import os
from pathlib import Path


def test_directory_structure():
    """Testa se a estrutura de diretórios está correta"""

    print("📁 Testando estrutura de diretórios...")
    print("=" * 50)

    # Estrutura esperada
    expected_structure = {
        "auth": [
            "__init__.py",
            "auth.py",
            "auth_token_manager.py",
            "user_management.py",
            "external_id_manager.py",
            "email_service.py"
        ],
        "drive_sync": [
            "__init__.py",
            "drive_handler.py",
            "drive_handler_recursive.py"
        ],
        "rag_system": [
            "__init__.py",
            "rag_handler.py",
            "enhanced_rag_handler.py"
        ],
        "chat_agents": [
            "__init__.py",
            "chat_agent.py",
            "educational_agent.py"
        ],
        "video_processing": [
            "__init__.py",
            "video_handler.py"
        ],
        "tests": [
            "__init__.py",
            "test_recursive_drive.py",
            "drive_test_script.py"
        ],
        "maintenance": [
            "__init__.py",
            "maintenance_endpoints.py"
        ],
        "utils": [
            "__init__.py"
        ],
        "config": [
            "__init__.py",
            "requirements.txt",
            "start_backend.py",
            "start.sh"
        ],
        "data": [
            "users_db.json",
            "approved_users.json",
            "auth_tokens.json",
            "external_id_counter.json",
            "video_analysis_cache.json",
            "users.json"
        ]
    }

    success_count = 0
    total_count = 0

    for directory, expected_files in expected_structure.items():
        print(f"📂 Verificando {directory}/...")
        dir_path = Path(directory)

        if not dir_path.exists():
            print(f"   ❌ Diretório {directory} não existe")
            continue

        for expected_file in expected_files:
            total_count += 1
            file_path = dir_path / expected_file
            if file_path.exists():
                print(f"   ✅ {expected_file}")
                success_count += 1
            else:
                print(f"   ❌ {expected_file} não encontrado")

    print("=" * 50)
    print(f"📊 Resultado: {success_count}/{total_count} arquivos encontrados")

    return success_count, total_count


def test_main_file():
    """Testa se o arquivo main.py existe e tem o tamanho esperado"""

    print("\n📄 Testando arquivo main.py...")
    print("=" * 50)

    main_file = Path("main.py")
    if main_file.exists():
        size_kb = main_file.stat().st_size / 1024
        print(f"✅ main.py encontrado ({size_kb:.1f} KB)")

        # Verificar se tem conteúdo mínimo
        if size_kb > 50:  # Mais de 50KB
            print("✅ Arquivo tem tamanho adequado")
            return True
        else:
            print("⚠️  Arquivo parece muito pequeno")
            return False
    else:
        print("❌ main.py não encontrado")
        return False


def test_readme():
    """Testa se o README.md existe"""

    print("\n📖 Testando README.md...")
    print("=" * 50)

    readme_file = Path("README.md")
    if readme_file.exists():
        size_kb = readme_file.stat().st_size / 1024
        print(f"✅ README.md encontrado ({size_kb:.1f} KB)")
        return True
    else:
        print("❌ README.md não encontrado")
        return False


def test_special_directories():
    """Testa se diretórios especiais existem"""

    print("\n🔧 Testando diretórios especiais...")
    print("=" * 50)

    special_dirs = [
        ".chromadb",
        "backup",
        ".venv"
    ]

    success_count = 0
    total_count = len(special_dirs)

    for dir_name in special_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/")
            success_count += 1
        else:
            print(f"⚠️  {dir_name}/ (opcional)")

    print("=" * 50)
    print(
        f"📊 Resultado: {success_count}/{total_count} diretórios especiais encontrados")

    return success_count, total_count


def main():
    """Função principal do teste"""

    print("🚀 Testando estrutura de reorganização do sistema")
    print("=" * 60)

    # Testar estrutura de diretórios
    files_success, files_total = test_directory_structure()

    # Testar arquivo main.py
    main_ok = test_main_file()

    # Testar README
    readme_ok = test_readme()

    # Testar diretórios especiais
    special_success, special_total = test_special_directories()

    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)

    print(
        f"📁 Estrutura de arquivos: {files_success}/{files_total} arquivos encontrados")
    print(f"📄 main.py: {'✅ OK' if main_ok else '❌ FALHOU'}")
    print(f"📖 README.md: {'✅ OK' if readme_ok else '❌ FALHOU'}")
    print(
        f"🔧 Diretórios especiais: {special_success}/{special_total} encontrados")

    # Calcular percentual de sucesso
    total_files = files_total + 2  # +2 para main.py e README.md
    successful_files = files_success + \
        (1 if main_ok else 0) + (1 if readme_ok else 0)
    success_rate = (successful_files / total_files) * 100

    print(f"\n📊 Taxa de sucesso: {success_rate:.1f}%")

    if success_rate >= 90:
        print("\n🎉 Estrutura reorganizada com sucesso!")
        return 0
    elif success_rate >= 70:
        print("\n⚠️  Estrutura parcialmente organizada. Verifique os itens faltantes.")
        return 1
    else:
        print("\n❌ Estrutura com problemas. Verifique a reorganização.")
        return 1


if __name__ == "__main__":
    exit(main())
