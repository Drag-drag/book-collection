from pydantic import BaseModel
from typing import List, Optional


class BookBase(BaseModel):
    title: Optional[str] = None      # ← сделали опциональными
    author: Optional[str] = None     # ← иначе BookCreate не может создаться без них
    genre: Optional[str] = None
    status: Optional[str] = None
    image: Optional[str] = None  # ← добавь


class BookCreate(BookBase):
    isbn: Optional[str] = None

class BookUpdate(BookBase):
    status: Optional[str] = None
    isbn: Optional[str] = None

class Book(BookBase):
    id: int
    isbn: Optional[str] = None

    class Config:
        from_attributes = True

class BooksList(BaseModel):
    books: List[Book]
    total: int
    skip: int
    limit: int

class Stats(BaseModel):
    total_books: int
    genres_count: dict

class ISBNRequest(BaseModel):
    isbn: str
