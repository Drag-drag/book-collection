# app/routers/books.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal

# Создаем роутер
router = APIRouter(
    prefix="/books",
    tags=["books"],
    responses={
        404: {"description": "Книга не найдена"},
        400: {"description": "Некорректные данные"}
    }
)


# Dependency для БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


## === ОСНОВНЫЕ CRUD ОПЕРАЦИИ ===

@router.post("/", response_model=schemas.Book, status_code=status.HTTP_201_CREATED)
async def create_book(
        book: schemas.BookCreate,
        db: Session = Depends(get_db)
):
    """Создать новую книгу в коллекции"""
    return crud.create_book(db=db, book=book)


@router.get("/", response_model=schemas.BooksList)
async def read_books(
        skip: int = Query(0, ge=0, description="С какого элемента начинать"),
        limit: int = Query(10, ge=1, le=100, description="Количество элементов"),
        author: Optional[str] = Query(None, description="Фильтр по автору"),
        genre: Optional[str] = Query(None, description="Фильтр по жанру"),
        db: Session = Depends(get_db)
):
    """Получить список книг с пагинацией и фильтрами"""
    books = crud.get_books(db, skip=skip, limit=limit, author=author, genre=genre)
    total = crud.get_books_count(db, author=author, genre=genre)
    return schemas.BooksList(books=books, total=total, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=schemas.Book)
async def read_book(book_id: int, db: Session = Depends(get_db)):
    """Получить книгу по ID"""
    book = crud.get_book(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book


@router.put("/{book_id}", response_model=schemas.Book)
async def update_book(
        book_id: int,
        book: schemas.BookUpdate,
        db: Session = Depends(get_db)
):
    """Обновить данные книги (частично)"""
    if not book.dict(exclude_unset=True):  # если ничего не передано
        raise HTTPException(status_code=400, detail="Передайте хотя бы одно поле")

    updated_book = crud.update_book(db, book_id=book_id, book=book)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return updated_book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Удалить книгу из коллекции"""
    success = crud.delete_book(db, book_id=book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Книга не найдена")


## === ДОПОЛНИТЕЛЬНЫЕ ОПЕРАЦИИ ===

@router.get("/stats/")
async def get_stats(db: Session = Depends(get_db)):
    """Статистика коллекции"""
    return crud.get_stats(db)


@router.get("/{book_id}/similar/")
async def get_similar_books(
        book_id: int,
        limit: int = Query(5, ge=1, le=20),
        db: Session = Depends(get_db)
):
    """Найти похожие книги (по автору и жанру)"""
    book = crud.get_book(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    similar = crud.get_similar_books(db, author=book.author, genre=book.genre, limit=limit, exclude_id=book_id)
    return similar
