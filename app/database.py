import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URI = "sqlite:///./books_collection.db"

engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    print("БД создана")

def drop_db():
    Base.metadata.drop_all(bind=engine)
    print("БД дропнута")

def test_connection() -> bool:
    try:
        with SessionLocal() as session:
            session.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
