"""
SQLAlchemy ORM models — matches the existing users_db.json schema exactly
so the migration is a straight import.
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String, Text
from .db import Base


class UserDB(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    id = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    full_name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="student")
    hashed_password = Column(Text, nullable=False)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    external_id = Column(String, nullable=True, unique=True, index=True)
    approved = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    is_temporary_password = Column(Boolean, default=False)
    instructor_username = Column(String, nullable=True)


class ApprovedUserDB(Base):
    """Pre-approved users list (whitelist for self-registration)."""
    __tablename__ = "approved_users"

    external_id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    role = Column(String, default="student")
