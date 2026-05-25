"""
One-time migration: import users_db.json + approved_users.json into SQLite.

Run once from the backend/ directory:
    python -m database.migrate_json_to_sqlite

Safe to run multiple times — skips users that already exist.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Allow running as a script from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import engine, Base
from database.models import UserDB, ApprovedUserDB
from sqlalchemy.orm import Session

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_JSON = DATA_DIR / "users_db.json"
APPROVED_JSON = DATA_DIR / "approved_users.json"


def _parse_dt(value) -> datetime:
    if not value:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def migrate():
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        # ── users_db.json ─────────────────────────────────────────────────────
        if USERS_JSON.exists():
            users_raw: dict = json.loads(USERS_JSON.read_text(encoding="utf-8"))
            imported = skipped = 0
            for username, u in users_raw.items():
                exists = session.query(UserDB).filter(UserDB.username == username).first()
                if exists:
                    skipped += 1
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
            print(f"✅ users_db.json — {imported} imported, {skipped} already existed")
        else:
            print("⚠️  users_db.json not found — skipping users migration")

        # ── approved_users.json ───────────────────────────────────────────────
        if APPROVED_JSON.exists():
            approved_raw: list = json.loads(APPROVED_JSON.read_text(encoding="utf-8"))
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
            print(f"✅ approved_users.json — {imported} imported, {skipped} already existed")
        else:
            print("⚠️  approved_users.json not found — skipping approved users migration")

    print("\n🎉 Migration complete. Database:", engine.url)
    print("   You can now delete users_db.json and approved_users.json")
    print("   (keep backups until you verify everything works)")


if __name__ == "__main__":
    migrate()
