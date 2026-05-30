from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas
from ..database import get_db
from ..services.book_service import BookService

router = APIRouter(prefix="/books", tags=["books"])

@router.get("/", response_model=schemas.BooksList)
async def read_books(
    author: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    service = BookService(db)
    books = service.get_all(author, genre)
    return {"books": books, "total": len(books)}

@router.get("/{book_id}", response_model=schemas.Book)
async def read_book(book_id: int, db: Session = Depends(get_db)):
    book = BookService(db).get_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book

@router.post("/", response_model=schemas.Book, status_code=status.HTTP_201_CREATED)
async def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    return BookService(db).create_book(book)

@router.post("/from-isbn", response_model=schemas.Book)
async def create_by_isbn(request: schemas.ISBNRequest, db: Session = Depends(get_db)):
    try:
        return await BookService(db).create_from_isbn(request.isbn)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{book_id}", response_model=schemas.Book)
async def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db)):
    updated = BookService(db).update_book(book_id, book)
    if not updated:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return updated

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    if not BookService(db).delete_book(book_id):
        raise HTTPException(status_code=404, detail="Книга не найдена")

@router.get("/stats/")
async def get_stats(db: Session = Depends(get_db)):
    return BookService(db).get_stats()

@router.get("/{book_id}/similar/", response_model=List[schemas.Book])
async def get_similar(book_id: int, limit: int = 5, db: Session = Depends(get_db)):
    return BookService(db).get_similar_books(book_id, limit)
