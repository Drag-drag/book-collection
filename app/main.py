from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager
from .config import templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import SessionLocal, init_db, test_connection, get_db
from .routers import books
from . import crud


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
async def root(
    request: Request,
    db: Session = Depends(get_db)  # ← нужно импортировать из database
):
    books = crud.get_books(db, skip=0, limit=50)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "books": books}
    )