import json
from pathlib import Path
from typing import List, Dict, Optional

# Arquivo para armazenar o último ID externo utilizado
EXTERNAL_ID_FILE = Path(__file__).parent.parent / \
    "data" / "external_id_counter.json"


def initialize_external_id_file():
    """Inicializa o arquivo de contador de ID externo se não existir"""
    if not EXTERNAL_ID_FILE.exists():
        with open(EXTERNAL_ID_FILE, 'w', encoding='utf-8') as f:
            json.dump({"last_id": 0, "deleted_ids": []}, f)


def load_external_id_data() -> Dict:
    """Carrega os dados de ID externo"""
    initialize_external_id_file()
    try:
        with open(EXTERNAL_ID_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_id": 0, "deleted_ids": []}


def save_external_id_data(data: Dict):
    """Salva os dados de ID externo"""
    with open(EXTERNAL_ID_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_next_external_id() -> str:
    """Obtém o próximo ID externo disponível

    Se houver IDs deletados, usa o menor deles.
    Caso contrário, incrementa o último ID utilizado.
    """
    data = load_external_id_data()

    # Se houver IDs deletados, use o menor deles
    if data["deleted_ids"]:
        # Ordena os IDs deletados
        deleted_ids = sorted([int(id_str) for id_str in data["deleted_ids"]])
        next_id = str(deleted_ids[0])
        # Remove o ID da lista de deletados
        data["deleted_ids"].remove(next_id)
        save_external_id_data(data)
        return next_id

    # Caso contrário, incrementa o último ID
    next_id = data["last_id"] + 1
    data["last_id"] = next_id
    save_external_id_data(data)
    return str(next_id)


def mark_external_id_as_deleted(external_id: str):
    """Marca um ID externo como deletado para reutilização"""
    if not external_id or external_id == "null" or external_id == "None":
        return

    data = load_external_id_data()

    # Adiciona o ID à lista de deletados se não estiver lá
    if external_id not in data["deleted_ids"]:
        data["deleted_ids"].append(external_id)
        save_external_id_data(data)


def reorganize_external_ids(users_db: Dict) -> Dict:
    """Reorganiza os IDs externos após exclusões

    Todos os IDs acima do menor ID deletado são decrementados
    para preencher os espaços vazios.
    """
    data = load_external_id_data()

    # Se não houver IDs deletados, não há nada para reorganizar
    if not data["deleted_ids"]:
        return users_db

    # Converte os IDs para inteiros e ordena
    deleted_ids = sorted([int(id_str) for id_str in data["deleted_ids"]])

    # Mapeia os IDs antigos para os novos
    id_mapping = {}

    # Para cada ID deletado, decrementa os IDs acima dele
    for deleted_id in deleted_ids:
        for username, user_data in users_db.items():
            if user_data.get("external_id") and user_data["external_id"] != "null":
                try:
                    current_id = int(user_data["external_id"])
                    if current_id > deleted_id:
                        # Se este ID já foi mapeado antes, use o valor mapeado
                        if user_data["external_id"] in id_mapping:
                            new_id = int(
                                id_mapping[user_data["external_id"]]) - 1
                        else:
                            new_id = current_id - 1

                        id_mapping[user_data["external_id"]] = str(new_id)
                except (ValueError, TypeError):
                    # Ignora IDs que não são números
                    pass

    # Aplica o mapeamento aos usuários
    for username, user_data in users_db.items():
        if user_data.get("external_id") and user_data["external_id"] in id_mapping:
            user_data["external_id"] = id_mapping[user_data["external_id"]]

    # Limpa a lista de IDs deletados
    data["deleted_ids"] = []
    save_external_id_data(data)

    return users_db
