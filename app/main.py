from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles  # Важно для CSS/JS
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from .database import SessionLocal, init_db, test_connection, get_db
from .routers import books
from .services.book_service import BookService
from .config import templates
from . import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    if test_connection():
        init_db()
    yield
    with SessionLocal() as session:
        session.close_all()


app = FastAPI(
    title="Book Collection Professional",
    description="Система управления коллекцией книг с использованием ML-рекомендаций",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(books.router)


@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    service = BookService(db)
    books_data = service.get_all(
        author=request.query_params.get("author"),
        genre=request.query_params.get("genre")
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "books": books_data
        }
    )