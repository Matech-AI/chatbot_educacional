"""
Script para migrar usuários do sistema local para o Supabase
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'supabase'))

from supabase_client import admin_create_user, validate_connection
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def load_local_users():
    """Carrega usuários do sistema local"""
    users_file = Path(__file__).parent.parent / "data" / "users_db.json"
    
    if not users_file.exists():
        print("❌ Arquivo users_db.json não encontrado")
        return {}
    
    with open(users_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def migrate_users():
    """Migra usuários do sistema local para o Supabase"""
    
    print("🔄 Iniciando migração de usuários para o Supabase...")
    
    # Verificar conexão com Supabase
    if not validate_connection():
        print("❌ Erro: Não foi possível conectar ao Supabase")
        return False
    
    print("✅ Conexão com Supabase estabelecida")
    
    # Carregar usuários locais
    local_users = load_local_users()
    
    if not local_users:
        print("❌ Nenhum usuário encontrado no sistema local")
        return False
    
    print(f"📊 Encontrados {len(local_users)} usuários no sistema local")
    
    # Contadores
    migrated = 0
    errors = 0
    
    for username, user_data in local_users.items():
        try:
            print(f"\n🔄 Migrando usuário: {username}")
            
            # Verificar se o usuário tem email
            if not user_data.get('email'):
                print(f"⚠️  Usuário {username} não tem email, pulando...")
                continue
            
            # Criar usuário no Supabase
            result = admin_create_user(
                email=user_data['email'],
                password=os.getenv("TEMP_USER_PASSWORD", "TempPassword123!"),  # Senha temporária
                full_name=user_data.get('full_name', username),
                role=user_data.get('role', 'student')
            )
            
            if result['success']:
                print(f"✅ Usuário {username} migrado com sucesso")
                migrated += 1
            else:
                print(f"❌ Erro ao migrar {username}: {result['error']}")
                errors += 1
                
        except Exception as e:
            print(f"❌ Erro inesperado ao migrar {username}: {str(e)}")
            errors += 1
    
    # Resumo da migração
    print(f"\n📊 Resumo da migração:")
    print(f"✅ Usuários migrados: {migrated}")
    print(f"❌ Erros: {errors}")
    print(f"📝 Total processado: {len(local_users)}")
    
    return errors == 0

def create_admin_user():
    """Cria usuário administrador padrão"""
    print("\n🔧 Criando usuário administrador padrão...")
    
    result = admin_create_user(
        email="admin@dnaforca.com",
        password=os.getenv("ADMIN_PASSWORD", "adminpass"),
        full_name="Administrador",
        role="admin"
    )
    
    if result['success']:
        print("✅ Usuário administrador criado com sucesso")
        print("📧 Email: admin@dnaforca.com")
        print("🔑 Senha: Admin123!")
        return True
    else:
        print(f"❌ Erro ao criar administrador: {result['error']}")
        return False

def main():
    """Função principal"""
    print("🚀 Script de Migração de Usuários para Supabase")
    print("=" * 50)
    
    # Verificar se o usuário quer continuar
    response = input("\n⚠️  Este script irá migrar todos os usuários do sistema local para o Supabase.\nContinuar? (s/N): ")
    
    if response.lower() not in ['s', 'sim', 'y', 'yes']:
        print("❌ Migração cancelada pelo usuário")
        return
    
    # Criar usuário administrador
    if not create_admin_user():
        print("❌ Falha ao criar usuário administrador. Abortando migração.")
        return
    
    # Migrar usuários
    if migrate_users():
        print("\n🎉 Migração concluída com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Faça login com o usuário administrador")
        print("2. Verifique se todos os usuários foram migrados corretamente")
        print("3. Configure as senhas dos usuários migrados")
        print("4. Teste o sistema de autenticação")
    else:
        print("\n❌ Migração concluída com erros. Verifique os logs acima.")

if __name__ == "__main__":
    main()
