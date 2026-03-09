from fastapi import Depends

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from typing import Annotated

from core.config import settings


engine = create_engine(url=settings.DATABASE_URL_psycopg)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db


db_dependency = Annotated[Session, Depends(get_db)]