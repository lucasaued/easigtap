from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import database_url


def make_session_factory():
    return sessionmaker(create_engine(database_url()), expire_on_commit=False)
