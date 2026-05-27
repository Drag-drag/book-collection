from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from .database import SessionLocal, init_db, test_connection, get_db
from .routers import books
from . import crud
from .config import templates
from .schemas import Book


@asynccontextmanager
async def lifespan(app: FastAPI):
    if test_connection():
        init_db()
    yield
    with SessionLocal() as session:
        session.close_all()

app = FastAPI(
    title="Управление коллекцией книг",
    lifespan=lifespan
)

app.include_router(books.router)

@app.get("/")
async def root(
    request: Request,
    author: str = None,
    genre: str = None,
    db: Session = Depends(get_db)
):
    books = crud.get_books(db, author=author, genre=genre)
    books = [Book.model_validate(book) for book in books]
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "books": books,
            "author": author,
            "genres": genre
        }
    )
