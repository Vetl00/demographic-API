import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


def get_engine(db_url=None):
    """
    Creates and returns a SQLAlchemy engine instance.
    For PostgreSQL, use: 'postgresql://user:password@localhost/dbname'
    """
    if db_url is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///demographics.db")
    return create_engine(db_url, echo=False)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine)


def init_db(database_engine=engine):
    """Creates all database tables defined in the metadata."""
    logging.info("Initializing database and creating tables...")
    Base.metadata.create_all(database_engine)


def get_db():
    """Yields a database session and closes it after use."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
