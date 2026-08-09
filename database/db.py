"""
Database engine, session factory, and initialization.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

import config


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    getattr(config, "DATABASE_URL", None)
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured. "
        "Set DATABASE_URL in Render Environment Variables."
    )


# Render/PostgreSQL compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )


# Add psycopg2 driver if needed
if DATABASE_URL.startswith("postgresql://"):
    if (
        "+psycopg2" not in DATABASE_URL
        and "+psycopg" not in DATABASE_URL
    ):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1
        )


print("=" * 70)
print("DATABASE INITIALIZATION")
print("=" * 70)

print(f"Database configured: {bool(DATABASE_URL)}")

if DATABASE_URL:
    safe_host = DATABASE_URL.split("@")[-1]
    print(f"Database host: {safe_host}")

print("=" * 70)


# ============================================================
# SQLAlchemy ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


# ============================================================
# SESSION
# ============================================================

Session = scoped_session(
    sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():
    """
    Create all database tables if they don't already exist.
    """

    from database.models import Base

    Base.metadata.create_all(engine)

    print("[OK] Database tables initialized.")


# ============================================================
# GET SESSION
# ============================================================

def get_session():
    """
    Return a thread-local database session.
    """

    return Session()


# ============================================================
# SHUTDOWN SESSION
# ============================================================

def shutdown_session(exception=None):
    """
    Remove the current database session.
    """

    Session.remove()