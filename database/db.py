from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

import config

engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True
)

Session = scoped_session(
    sessionmaker(bind=engine)
)


def init_db():
    from database.models import Base
    Base.metadata.create_all(engine)


def get_session():
    return Session()


def shutdown_session(exception=None):
    Session.remove()