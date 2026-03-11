from fastapi import FastAPI
from contextlib import asynccontextmanager

from .database import SessionLocal, init_db, test_connection
from .routers import books

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Запуск...")
    if test_connection():
        init_db()
    yield
    print("🛑 Остановка")

app = FastAPI(
    title="Управление коллекцией книг",
    lifespan=lifespan
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.include_router(books.router)

@app.get("/")
async def root():
    return {"message": "API готово!", "docs": "/docs"}
