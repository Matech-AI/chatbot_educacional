import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Arquivo para armazenar tokens de autenticação
AUTH_TOKENS_FILE = Path(__file__).parent.parent / "data" / "auth_tokens.json"

# Tempo de expiração do token em segundos (24 horas)
TOKEN_EXPIRATION = 24 * 60 * 60


def load_auth_tokens():
    """Carrega os tokens de autenticação do arquivo"""
    try:
        if AUTH_TOKENS_FILE.exists():
            with open(AUTH_TOKENS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_auth_tokens(tokens):
    """Salva os tokens de autenticação no arquivo"""
    with open(AUTH_TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)


def create_auth_token(username, token, email=None):
    """Cria um novo token de autenticação"""
    tokens = load_auth_tokens()

    # Adicionar novo token
    tokens[token] = {
        "username": username,
        "email": email,
        "created_at": time.time(),
        "expires_at": time.time() + TOKEN_EXPIRATION,
        "used": False
    }

    save_auth_tokens(tokens)
    return token


def verify_auth_token(token):
    """Verifica se um token é válido e não expirou"""
    tokens = load_auth_tokens()

    if token not in tokens:
        return None

    token_data = tokens[token]

    # Verificar se o token expirou
    if token_data["expires_at"] < time.time():
        return None

    # Verificar se o token já foi usado
    if token_data["used"]:
        return None

    return token_data


def mark_token_as_used(token):
    """Marca um token como usado"""
    tokens = load_auth_tokens()

    if token in tokens:
        tokens[token]["used"] = True
        save_auth_tokens(tokens)
        return True

    return False


def clean_expired_tokens():
    """Remove tokens expirados"""
    tokens = load_auth_tokens()
    current_time = time.time()

    # Filtrar tokens não expirados
    valid_tokens = {}
    for token, data in tokens.items():
        if data["expires_at"] > current_time:
            valid_tokens[token] = data

    # Salvar tokens válidos
    save_auth_tokens(valid_tokens)

    return len(tokens) - len(valid_tokens)  # Número de tokens removidos
