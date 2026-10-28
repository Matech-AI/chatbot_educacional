#!/usr/bin/env python3
"""
Backup dos usuários do banco (SQLite local ou Postgres/Supabase) em JSON.

Gera backend/data/backups/<data_hora>/users_db.json e approved_users.json,
no mesmo formato que o seed_production_db.py lê. Para restaurar:

  python backend/scripts/seed_production_db.py --from backend/data/backups/<data_hora>

Como usar:
  python backend/scripts/backup_db.py                       # banco local
  DATABASE_URL="postgresql://..." python backend/scripts/backup_db.py   # produção
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent
sys.path.insert(0, str(_BACKEND))

from database.db import DATABASE_URL, SessionLocal  # noqa: E402
from database.models import UserDB, ApprovedUserDB  # noqa: E402

BACKUP_DIR = _BACKEND / "data" / "backups"


def _dt(value):
    return value.isoformat() if value else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out = BACKUP_DIR / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        users = {
            u.username: {
                "username": u.username,
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "hashed_password": u.hashed_password,
                "disabled": u.disabled,
                "created_at": _dt(u.created_at),
                "updated_at": _dt(u.updated_at),
                "external_id": u.external_id,
                "approved": u.approved,
                "last_login": _dt(u.last_login),
                "is_temporary_password": u.is_temporary_password,
                "instructor_username": u.instructor_username,
            }
            for u in db.query(UserDB).all()
        }
        approved = [
            {
                "external_id": a.external_id,
                "username": a.username,
                "email": a.email,
                "full_name": a.full_name,
                "role": a.role,
            }
            for a in db.query(ApprovedUserDB).all()
        ]
    finally:
        db.close()

    (out / "users_db.json").write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "approved_users.json").write_text(json.dumps(approved, indent=2, ensure_ascii=False), encoding="utf-8")

    # No SQLite, guarda também uma cópia do arquivo inteiro
    if DATABASE_URL.startswith("sqlite"):
        db_file = Path(DATABASE_URL.replace("sqlite:///", ""))
        if db_file.exists():
            shutil.copy2(db_file, out / db_file.name)

    print(f"Backup salvo em {out} ({len(users)} usuários, {len(approved)} aprovados)")


if __name__ == "__main__":
    main()
