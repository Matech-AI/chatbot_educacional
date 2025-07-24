import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
# Exemplo de uso
# ---------------------------

if __name__ == "__main__":
    print("Conexão válida?", validate_connection())
    print("Usuários ativos:", get_active_users())
    sync_materials_with_filesystem()