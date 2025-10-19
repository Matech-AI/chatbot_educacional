#!/usr/bin/env python3
"""
Script de migração de arquivos JSON para banco de dados PostgreSQL
Migra dados de users_db.json, profiles.json, materials.json, etc. para PostgreSQL
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime
import hashlib
import uuid

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent.parent))

from auth.auth import verify_password, get_password_hash

# Configurações do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/dna_da_forca")

def get_db_connection():
    """Conecta ao banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        return None

def load_json_file(file_path):
    """Carrega dados de um arquivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar {file_path}: {e}")
        return None

def migrate_users(conn):
    """Migra usuários de users_db.json para a tabela profiles"""
    print("🔄 Migrando usuários...")
    
    users_file = Path(__file__).parent.parent / "data" / "users_db.json"
    users_data = load_json_file(users_file)
    
    if not users_data:
        print("⚠️ Nenhum dado de usuário encontrado")
        return
    
    cursor = conn.cursor()
    
    try:
        for username, user_data in users_data.items():
            # Gerar UUID para o usuário
            user_id = str(uuid.uuid4())
            
            # Inserir na tabela auth.users (simulada)
            # Nota: Em produção, isso seria feito pelo Supabase Auth
            print(f"📝 Migrando usuário: {username}")
            
            # Inserir na tabela profiles
            cursor.execute("""
                INSERT INTO profiles (id, full_name, email, role, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    role = EXCLUDED.role,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
            """, (
                user_id,
                user_data.get('full_name', username),
                user_data.get('email', f'{username}@iadnadaforca.com.br'),
                user_data.get('role', 'student'),
                not user_data.get('disabled', False),
                datetime.now(),
                datetime.now()
            ))
        
        conn.commit()
        print(f"✅ {len(users_data)} usuários migrados com sucesso")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao migrar usuários: {e}")
    finally:
        cursor.close()

def migrate_materials(conn):
    """Migra materiais de materials.json para a tabela materials"""
    print("🔄 Migrando materiais...")
    
    materials_file = Path(__file__).parent.parent / "data" / "materials.json"
    materials_data = load_json_file(materials_file)
    
    if not materials_data:
        print("⚠️ Nenhum dado de material encontrado")
        return
    
    cursor = conn.cursor()
    
    try:
        for material_id, material_data in materials_data.items():
            print(f"📝 Migrando material: {material_data.get('title', material_id)}")
            
            # Determinar o tipo do material baseado no caminho
            path = material_data.get('path', '')
            if path.endswith('.mp4') or path.endswith('.avi') or path.endswith('.mov'):
                material_type = 'video'
            elif path.endswith('.pdf') or path.endswith('.docx'):
                material_type = 'document'
            elif path.endswith('.jpg') or path.endswith('.png') or path.endswith('.jpeg'):
                material_type = 'image'
            else:
                material_type = 'text'
            
            # Obter o ID do usuário que fez upload (se existir)
            uploaded_by = None
            if 'uploaded_by' in material_data:
                cursor.execute("SELECT id FROM profiles WHERE full_name = %s", (material_data['uploaded_by'],))
                result = cursor.fetchone()
                if result:
                    uploaded_by = result[0]
            
            cursor.execute("""
                INSERT INTO materials (id, title, description, type, path, original_filename, size, tags, status, uploaded_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    type = EXCLUDED.type,
                    path = EXCLUDED.path,
                    original_filename = EXCLUDED.original_filename,
                    size = EXCLUDED.size,
                    tags = EXCLUDED.tags,
                    status = EXCLUDED.status,
                    uploaded_by = EXCLUDED.uploaded_by,
                    updated_at = EXCLUDED.updated_at
            """, (
                material_id,
                material_data.get('title', 'Sem título'),
                material_data.get('description', ''),
                material_type,
                material_data.get('path', ''),
                material_data.get('original_filename', ''),
                material_data.get('size', 0),
                material_data.get('tags', []),
                'processed',  # Assumir que os materiais existentes estão processados
                uploaded_by,
                datetime.now(),
                datetime.now()
            ))
        
        conn.commit()
        print(f"✅ {len(materials_data)} materiais migrados com sucesso")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao migrar materiais: {e}")
    finally:
        cursor.close()

def migrate_assistant_configs(conn):
    """Migra configurações de assistente de assistant_configs.json para a tabela assistant_configs"""
    print("🔄 Migrando configurações de assistente...")
    
    configs_file = Path(__file__).parent.parent / "data" / "assistant_configs.json"
    configs_data = load_json_file(configs_file)
    
    if not configs_data:
        print("⚠️ Nenhuma configuração de assistente encontrada")
        return
    
    cursor = conn.cursor()
    
    try:
        for config_id, config_data in configs_data.items():
            print(f"📝 Migrando configuração: {config_data.get('name', config_id)}")
            
            # Obter o ID do usuário que criou a configuração
            created_by = None
            if 'created_by' in config_data:
                cursor.execute("SELECT id FROM profiles WHERE full_name = %s", (config_data['created_by'],))
                result = cursor.fetchone()
                if result:
                    created_by = result[0]
            
            cursor.execute("""
                INSERT INTO assistant_configs (id, name, description, prompt, model, temperature, chunk_size, chunk_overlap, retrieval_search_type, embedding_model, created_by, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    prompt = EXCLUDED.prompt,
                    model = EXCLUDED.model,
                    temperature = EXCLUDED.temperature,
                    chunk_size = EXCLUDED.chunk_size,
                    chunk_overlap = EXCLUDED.chunk_overlap,
                    retrieval_search_type = EXCLUDED.retrieval_search_type,
                    embedding_model = EXCLUDED.embedding_model,
                    created_by = EXCLUDED.created_by,
                    updated_at = EXCLUDED.updated_at
            """, (
                config_id,
                config_data.get('name', 'Configuração sem nome'),
                config_data.get('description', ''),
                config_data.get('prompt', ''),
                config_data.get('model', 'gpt-3.5-turbo'),
                config_data.get('temperature', 0.7),
                config_data.get('chunk_size', 2000),
                config_data.get('chunk_overlap', 200),
                config_data.get('retrieval_search_type', 'similarity'),
                config_data.get('embedding_model', 'text-embedding-ada-002'),
                created_by,
                datetime.now(),
                datetime.now()
            ))
        
        conn.commit()
        print(f"✅ {len(configs_data)} configurações de assistente migradas com sucesso")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao migrar configurações de assistente: {e}")
    finally:
        cursor.close()

def create_backup():
    """Cria backup dos arquivos JSON antes da migração"""
    print("🔄 Criando backup dos arquivos JSON...")
    
    backup_dir = Path(__file__).parent.parent / "data" / "backup_json"
    backup_dir.mkdir(exist_ok=True)
    
    json_files = [
        "users_db.json",
        "profiles.json", 
        "materials.json",
        "assistant_configs.json",
        "auth_tokens.json",
        "approved_users.json"
    ]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for file_name in json_files:
        source_file = Path(__file__).parent.parent / "data" / file_name
        if source_file.exists():
            backup_file = backup_dir / f"{file_name}.{timestamp}"
            import shutil
            shutil.copy2(source_file, backup_file)
            print(f"📁 Backup criado: {backup_file}")
    
    print("✅ Backup dos arquivos JSON concluído")

def main():
    """Função principal de migração"""
    print("🚀 Iniciando migração de arquivos JSON para banco de dados PostgreSQL")
    print(f"📊 URL do banco: {DATABASE_URL}")
    
    # Criar backup
    create_backup()
    
    # Conectar ao banco
    conn = get_db_connection()
    if not conn:
        print("❌ Não foi possível conectar ao banco de dados")
        return
    
    try:
        # Executar migrações
        migrate_users(conn)
        migrate_materials(conn)
        migrate_assistant_configs(conn)
        
        print("🎉 Migração concluída com sucesso!")
        print("📝 Próximos passos:")
        print("   1. Verificar os dados migrados no banco")
        print("   2. Atualizar o código para usar o banco ao invés dos JSONs")
        print("   3. Testar o sistema com os novos dados")
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
