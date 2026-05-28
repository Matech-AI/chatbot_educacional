#!/usr/bin/env python3
"""
Seed da base de dados de produção com usuários do users_db.json local.

Como usar:
  1. Garanta que a senha do postgres está correta no banco (veja instrução abaixo)
  2. Execute com a DATABASE_URL de produção:

     Windows:
       set DATABASE_URL=postgresql://postgres:Ip%%40DeM%%402214@<HOST>:5432/bd_chatbot_educacional
       python backend/scripts/seed_production_db.py

     Linux/Mac:
       DATABASE_URL="postgresql://postgres:Ip%40DeM%402214@<HOST>:5432/bd_chatbot_educacional" python backend/scripts/seed_production_db.py

     Ou, no servidor (dentro do container api-server ou direto):
       python -m backend.scripts.seed_production_db

IMPORTANTE — Para corrigir a senha do postgres primeiro, execute no terminal
do container postgres no Coolify:
  psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'Ip@DeM@2214';"
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Permite rodar a partir da raiz do projeto ou de dentro de backend/
_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent
sys.path.insert(0, str(_BACKEND.parent))  # raiz
sys.path.insert(0, str(_BACKEND))         # backend/

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///" + str(_BACKEND / "data" / "app.db"),
)


def _get_engine():
    from sqlalchemy import create_engine
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    return create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)


def _parse_dt(value) -> datetime:
    if not value:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def seed_users(session, users_raw: dict):
    from database.models import UserDB

    imported = skipped = updated = 0
    for username, u in users_raw.items():
        existing = session.query(UserDB).filter(UserDB.username == username).first()
        if existing:
            # Atualiza senha e role caso já exista
            existing.hashed_password = u.get("hashed_password", existing.hashed_password)
            existing.role = u.get("role", existing.role)
            existing.email = u.get("email", existing.email)
            existing.full_name = u.get("full_name", existing.full_name)
            existing.approved = u.get("approved", existing.approved)
            existing.updated_at = datetime.utcnow()
            skipped += 1
            updated += 1
            continue

        row = UserDB(
            username=username,
            id=u.get("id", username),
            email=u.get("email"),
            full_name=u.get("full_name"),
            role=u.get("role", "student"),
            hashed_password=u.get("hashed_password", ""),
            disabled=u.get("disabled", False),
            created_at=_parse_dt(u.get("created_at")),
            updated_at=_parse_dt(u.get("updated_at")),
            external_id=u.get("external_id"),
            approved=u.get("approved", True),
            last_login=_parse_dt(u.get("last_login")) if u.get("last_login") else None,
            is_temporary_password=u.get("is_temporary_password", False),
            instructor_username=u.get("instructor_username"),
        )
        session.add(row)
        imported += 1

    session.commit()
    print(f"  Usuários: {imported} importados, {updated} atualizados")


def seed_approved_users(session, approved_raw: list):
    from database.models import ApprovedUserDB

    imported = skipped = 0
    for u in approved_raw:
        ext_id = u.get("external_id") or u.get("username")
        exists = session.query(ApprovedUserDB).filter(
            ApprovedUserDB.external_id == ext_id
        ).first()
        if exists:
            skipped += 1
            continue
        session.add(ApprovedUserDB(
            external_id=ext_id,
            username=u.get("username", ""),
            email=u.get("email"),
            full_name=u.get("full_name"),
            role=u.get("role", "student"),
        ))
        imported += 1

    session.commit()
    print(f"  Approved users: {imported} importados, {skipped} já existiam")


def main():
    print(f"🔌 Conectando em: {DATABASE_URL[:60]}...")

    engine = _get_engine()

    # Importa modelos e cria tabelas se não existirem
    from database.db import Base
    from database.models import UserDB, ApprovedUserDB  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas verificadas/criadas")

    from sqlalchemy.orm import Session

    DATA_DIR = _BACKEND / "data"
    users_file = DATA_DIR / "users_db.json"
    approved_file = DATA_DIR / "approved_users.json"

    with Session(engine) as session:
        # Seed usuários
        if users_file.exists():
            print("\n📋 Importando users_db.json...")
            users_raw = json.loads(users_file.read_text(encoding="utf-8"))
            seed_users(session, users_raw)
        else:
            print("⚠️  users_db.json não encontrado — pulando")

        # Seed approved users
        if approved_file.exists():
            print("\n📋 Importando approved_users.json...")
            approved_raw = json.loads(approved_file.read_text(encoding="utf-8"))
            seed_approved_users(session, approved_raw)
        else:
            print("⚠️  approved_users.json não encontrado — pulando")

    print(f"\n🎉 Seed concluído! Banco: {engine.url}")


if __name__ == "__main__":
    main()
