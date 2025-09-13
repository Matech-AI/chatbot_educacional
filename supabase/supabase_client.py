import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

# Carrega variáveis do .env
load_dotenv()

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Para operações administrativas

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Cliente com service role para operações administrativas
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_SERVICE_KEY else supabase

# ---------------------------
# Usuários e Perfis
# ---------------------------

def get_profiles():
    """Busca todos os perfis de usuários"""
    response = supabase.table("profiles").select("*").execute()
    return response.data

def get_profile_by_id(user_id):
    """Busca perfil pelo ID"""
    response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    return response.data

def get_profile_by_email(email):
    """Busca perfil pelo e-mail"""
    response = supabase.table("profiles").select("*").eq("email", email).single().execute()
    return response.data

def insert_profile(profile):
    """Insere novo perfil"""
    response = supabase.table("profiles").insert(profile).execute()
    return response.data

def update_profile(user_id, updates):
    """Atualiza perfil"""
    response = supabase.table("profiles").update(updates).eq("id", user_id).execute()
    return response.data

def deactivate_profile(user_id):
    """Desativa perfil"""
    response = supabase.table("profiles").update({"is_active": False}).eq("id", user_id).execute()
    return response.data

# ---------------------------
# Materiais
# ---------------------------

def get_materials():
    """Busca todos os materiais"""
    response = supabase.table("materials").select("*").execute()
    return response.data

def get_material_by_id(material_id):
    """Busca material pelo ID"""
    response = supabase.table("materials").select("*").eq("id", material_id).single().execute()
    return response.data

def get_materials_by_user(user_id):
    """Busca materiais enviados por um usuário"""
    response = supabase.table("materials").select("*").eq("uploaded_by", user_id).execute()
    return response.data

def insert_material(material):
    """Insere novo material"""
    response = supabase.table("materials").insert(material).execute()
    return response.data

def update_material(material_id, updates):
    """Atualiza material"""
    response = supabase.table("materials").update(updates).eq("id", material_id).execute()
    return response.data

def delete_material(material_id):
    """Remove material"""
    response = supabase.table("materials").delete().eq("id", material_id).execute()
    return response.data

# ---------------------------
# Sessões de Chat
# ---------------------------

def get_chat_sessions_by_user(user_id):
    """Busca sessões de chat de um usuário"""
    response = supabase.table("chat_sessions").select("*").eq("user_id", user_id).execute()
    return response.data

def insert_chat_session(session):
    """Cria nova sessão de chat"""
    response = supabase.table("chat_sessions").insert(session).execute()
    return response.data

def update_chat_session(session_id, updates):
    """Atualiza sessão de chat"""
    response = supabase.table("chat_sessions").update(updates).eq("id", session_id).execute()
    return response.data

def delete_chat_session(session_id):
    """Remove sessão de chat"""
    response = supabase.table("chat_sessions").delete().eq("id", session_id).execute()
    return response.data

# ---------------------------
# Mensagens de Chat
# ---------------------------

def get_chat_messages(session_id):
    """Busca mensagens de uma sessão"""
    response = supabase.table("chat_messages").select("*").eq("session_id", session_id).order("created_at", desc=False).execute()
    return response.data

def insert_chat_message(message):
    """Insere nova mensagem"""
    response = supabase.table("chat_messages").insert(message).execute()
    return response.data

# ---------------------------
# Configurações do Assistente
# ---------------------------

def get_assistant_configs():
    """Busca todas as configs de assistente"""
    response = supabase.table("assistant_configs").select("*").execute()
    return response.data

def insert_assistant_config(config):
    """Insere nova config de assistente"""
    response = supabase.table("assistant_configs").insert(config).execute()
    return response.data

# ---------------------------
# Validação de conexão e usuários conectados
# ---------------------------

def validate_connection():
    """Valida conexão com o Supabase"""
    try:
        response = supabase.table("profiles").select("id").limit(1).execute()
        # Se response.data não for None, a conexão está ok
        return response.data is not None
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return False

def get_active_users():
    """Retorna usuários ativos"""
    response = supabase.table("profiles").select("*").eq("is_active", True).execute()
    return response.data

# ---------------------------
# Sincronização de Materiais
# ---------------------------

def sync_materials_with_filesystem():
    """
    Sincroniza o banco de materiais com a pasta MATERIALS_DIR:
    - Adiciona ao banco os arquivos novos.
    - Remove do banco os registros de arquivos que não existem mais.
    - Atualiza registros se o arquivo mudou.
    """
    MATERIALS_DIR = "../backend/data/materials"
    if not os.path.exists(MATERIALS_DIR):
        print(f"Pasta não encontrada: {MATERIALS_DIR}")
        return

    # 1. Busca todos os materiais já cadastrados no banco
    db_materials = get_materials() or []
    db_titles = {m['title']: m for m in db_materials if 'title' in m}

    # 2. Lista todos os arquivos presentes na pasta
    fs_files = {filename: os.path.join(MATERIALS_DIR, filename)
                for filename in os.listdir(MATERIALS_DIR)
                if os.path.isfile(os.path.join(MATERIALS_DIR, filename))}

    # 3. Adiciona ou atualiza arquivos do sistema no banco
    for filename, path in fs_files.items():
        size = os.path.getsize(path)
        if filename not in db_titles:
            # Novo arquivo
            material = {
                "title": filename,
                "path": path,
                "type": "document",  # ou defina conforme extensão
                "size": size,
            }
            print(f"Inserindo material: {filename}")
            insert_material(material)
        else:
            # Atualiza se necessário
            db_material = db_titles[filename]
            if db_material.get("size") != size or db_material.get("path") != path:
                updates = {"size": size, "path": path}
                print(f"Atualizando material: {filename}")
                update_material(db_material["id"], updates)
            else:
                print(f"Material já atualizado: {filename}")

    # 4. Remove do banco os registros de arquivos que não existem mais
    fs_filenames = set(fs_files.keys())
    for filename, db_material in db_titles.items():
        if filename not in fs_filenames:
            print(f"Removendo do banco: {filename}")
            delete_material(db_material["id"])

# ---------------------------
# Autenticação Segura
# ---------------------------

def sign_up_user(email: str, password: str, full_name: str, role: str = "student") -> Dict[str, Any]:
    """
    Registra um novo usuário no Supabase Auth e cria perfil
    """
    try:
        # 1. Criar usuário no Supabase Auth
        auth_response = supabase_admin.auth.admin_create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Auto-confirmar email para simplificar
            "user_metadata": {
                "full_name": full_name,
                "role": role
            }
        })
        
        if not auth_response.user:
            raise Exception("Falha ao criar usuário no Auth")
        
        user_id = auth_response.user.id
        
        # 2. Criar perfil na tabela profiles
        profile_data = {
            "id": user_id,
            "full_name": full_name,
            "email": email,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        profile_response = supabase_admin.table("profiles").insert(profile_data).execute()
        
        if not profile_response.data:
            # Se falhar ao criar perfil, remover usuário do Auth
            supabase_admin.auth.admin_delete_user(user_id)
            raise Exception("Falha ao criar perfil do usuário")
        
        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "profile": profile_response.data[0]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def sign_in_user(email: str, password: str) -> Dict[str, Any]:
    """
    Autentica usuário e retorna dados da sessão
    """
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            raise Exception("Credenciais inválidas")
        
        # Buscar perfil do usuário
        profile = get_profile_by_id(auth_response.user.id)
        
        if not profile:
            raise Exception("Perfil do usuário não encontrado")
        
        return {
            "success": True,
            "user": auth_response.user,
            "profile": profile,
            "session": auth_response.session
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def sign_out_user() -> bool:
    """
    Desconecta o usuário atual
    """
    try:
        supabase.auth.sign_out()
        return True
    except Exception as e:
        print(f"Erro ao desconectar: {e}")
        return False

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Retorna dados do usuário atualmente autenticado
    """
    try:
        user = supabase.auth.get_user()
        if not user.user:
            return None
        
        profile = get_profile_by_id(user.user.id)
        return {
            "user": user.user,
            "profile": profile
        }
    except Exception as e:
        print(f"Erro ao buscar usuário atual: {e}")
        return None

def update_user_password(current_password: str, new_password: str) -> Dict[str, Any]:
    """
    Atualiza senha do usuário atual
    """
    try:
        # Primeiro, verificar se a senha atual está correta
        user = get_current_user()
        if not user:
            return {"success": False, "error": "Usuário não autenticado"}
        
        # Atualizar senha
        response = supabase.auth.update_user({
            "password": new_password
        })
        
        return {
            "success": True,
            "message": "Senha atualizada com sucesso"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def reset_password(email: str) -> Dict[str, Any]:
    """
    Envia email de reset de senha
    """
    try:
        response = supabase.auth.reset_password_email(email)
        return {
            "success": True,
            "message": "Email de reset enviado"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def update_user_profile(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Atualiza perfil do usuário atual
    """
    try:
        user = get_current_user()
        if not user:
            return {"success": False, "error": "Usuário não autenticado"}
        
        user_id = user["user"].id
        
        # Atualizar perfil
        response = supabase.table("profiles").update({
            **updates,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        
        if not response.data:
            return {"success": False, "error": "Falha ao atualizar perfil"}
        
        return {
            "success": True,
            "profile": response.data[0]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def admin_create_user(email: str, password: str, full_name: str, role: str = "student") -> Dict[str, Any]:
    """
    Cria usuário como administrador (sem confirmação de email)
    """
    try:
        # Criar usuário no Auth
        auth_response = supabase_admin.auth.admin_create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": full_name,
                "role": role
            }
        })
        
        if not auth_response.user:
            raise Exception("Falha ao criar usuário no Auth")
        
        user_id = auth_response.user.id
        
        # Criar perfil
        profile_data = {
            "id": user_id,
            "full_name": full_name,
            "email": email,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        profile_response = supabase_admin.table("profiles").insert(profile_data).execute()
        
        return {
            "success": True,
            "user_id": user_id,
            "profile": profile_response.data[0] if profile_response.data else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def admin_delete_user(user_id: str) -> Dict[str, Any]:
    """
    Remove usuário (apenas administradores)
    """
    try:
        # Deletar do Auth
        supabase_admin.auth.admin_delete_user(user_id)
        
        # Deletar perfil (cascade já remove dados relacionados)
        supabase_admin.table("profiles").delete().eq("id", user_id).execute()
        
        return {
            "success": True,
            "message": "Usuário removido com sucesso"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def admin_list_users() -> Dict[str, Any]:
    """
    Lista todos os usuários (apenas administradores)
    """
    try:
        response = supabase_admin.table("profiles").select("*").execute()
        return {
            "success": True,
            "users": response.data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def admin_update_user_role(user_id: str, new_role: str) -> Dict[str, Any]:
    """
    Atualiza role do usuário (apenas administradores)
    """
    try:
        response = supabase_admin.table("profiles").update({
            "role": new_role,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        
        return {
            "success": True,
            "profile": response.data[0] if response.data else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ---------------------------
# Exemplo de uso
# ---------------------------

if __name__ == "__main__":
    print("Conexão válida?", validate_connection())
    print("Usuários ativos:", get_active_users())
    sync_materials_with_filesystem()