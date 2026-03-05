from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from db.config import settings


engine = create_engine(url=settings.DATABASE_URL_psycopg)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db