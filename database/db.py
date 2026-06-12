"""
Database engine, session factory, and initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

import config

engine = create_engine(config.DATABASE_URL, echo=False)
Session = scoped_session(sessionmaker(bind=engine))


def init_db():
    """Create all tables if they don't exist."""
    from database.models import Base
    Base.metadata.create_all(engine)


def get_session():
    """Return a thread-local database session."""
    return Session()


def shutdown_session(exception=None):
    """Remove the current session (call at end of request)."""
    Session.remove()
