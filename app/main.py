from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .database import SessionLocal, init_db, test_connection
from .routers import books

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск...")
    if test_connection():
        init_db()
    yield
    print("Остановка")

app = FastAPI(
    title="Управление коллекцией книг",
    lifespan=lifespan
)

# Раздача статики
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CORS — разрешаем localhost:5500
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000",
                    "http://127.0.0.1:8000",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router)

@app.get("/")
async def root():
    return {"message": "Готово"}

@app.get("/ui")
async def ui():
    return {"message": "Перейдите на /static/index.html"}