from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
import httpx

from .. import crud, schemas, models
from ..database import get_db
from ..config import templates

router = APIRouter(
    prefix="/books",
    tags=["books"],
    responses={
        404: {"description": "Книга не найдена"},
        400: {"description": "Некорректные данные"}
    }
)

@router.post("/", response_model=schemas.Book, status_code=status.HTTP_201_CREATED)
async def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    return crud.create_book(db=db, book=book)

@router.post("/from-isbn", response_model=schemas.Book, status_code=status.HTTP_201_CREATED)
async def create_book_from_isbn(request: schemas.ISBNRequest, db: Session = Depends(get_db)):
    isbn = request.isbn
    if not isbn:
        raise HTTPException(status_code=400, detail="Поле 'isbn' обязательно")

    isbn_clean = ''.join(filter(str.isdigit, isbn))
    if not (10 <= len(isbn_clean) <= 13):
        raise HTTPException(status_code=400, detail="ISBN должен содержать 10 или 13 цифр.")

    existing_book = db.query(models.Book).filter(models.Book.isbn == isbn_clean).first()
    if existing_book:
        raise HTTPException(status_code=400, detail=f"Книга с ISBN {isbn_clean} уже существует")

    volume = None
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_clean}", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("totalItems", 0) > 0:
                    volume = data["items"][0]["volumeInfo"]
        except Exception:
            pass

        if not volume:
            try:
                resp = await client.get(f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn_clean}&format=json&jscmd=data", timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    key = f"ISBN:{isbn_clean}"
                    if key in data:
                        ol_book = data[key]
                        volume = {
                            "title": ol_book.get("title", "Без названия"),
                            "authors": [{"name": a["name"]} for a in ol_book.get("authors", [])],
                            "categories": [{"name": s["name"]} for s in ol_book.get("subjects", [])[:1]],
                            "imageLinks": {"thumbnail": ol_book.get("cover", {}).get("medium")},
                            "description": ol_book.get("by_statement"),
                        }
            except Exception:
                pass

    if not volume:
        raise HTTPException(status_code=404, detail="Книга не найдена. Попробуйте добавить вручную.")

    title = volume.get("title")
    authors = volume.get("authors", [])
    if not title or not authors:
        raise HTTPException(status_code=400, detail="Недостаточно данных: нужны название и автор")

    categories = volume.get("categories", [])
    genre = ", ".join([c["name"] if isinstance(c, dict) else c for c in categories]) if categories else None
    author_str = ", ".join([a["name"] if isinstance(a, dict) else a for a in authors])

    book_to_create = schemas.BookCreate(
        title=title, author=author_str, genre=genre, status="в планах",
        isbn=isbn_clean, image=volume.get("imageLinks", {}).get("thumbnail")
    )
    return crud.create_book(db=db, book=book_to_create)

@router.get("/", response_model=schemas.BooksList)
async def read_books(author: Optional[str] = Query(None), genre: Optional[str] = Query(None), db: Session = Depends(get_db)):
    books = crud.get_books(db, author=author, genre=genre)
    total = crud.get_books_count(db, author=author, genre=genre)
    return schemas.BooksList(books=books, total=total)

@router.get("/{book_id}", response_model=schemas.Book)
async def read_book(book_id: int, db: Session = Depends(get_db)):
    book = crud.get_book(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book

@router.put("/{book_id}", response_model=schemas.Book)
async def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db)):
    if not book.model_dump(exclude_unset=True):
        raise HTTPException(status_code=400, detail="Передайте хотя бы одно поле")
    updated_book = crud.update_book(db, book_id=book_id, book=book)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return updated_book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    if not crud.delete_book(db, book_id=book_id):
        raise HTTPException(status_code=404, detail="Книга не найдена")

@router.get("/stats/")
async def get_stats(db: Session = Depends(get_db)):
    return crud.get_stats(db)

@router.get("/{book_id}/similar/")
async def get_similar_books(book_id: int, limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    book = crud.get_book(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return crud.get_similar_books(db, author=book.author, genre=book.genre, limit=limit, exclude_id=book_id)