from pydantic import BaseModel
from typing import List, Optional

class BookBase(BaseModel):
    title: str
    author: str
    genre: Optional[str] = None
    status: str
    description: Optional[str] = None
    image: Optional[str] = None
    isbn: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    status: Optional[str] = None
    description: Optional[str] = None

class Book(BookBase):
    id: int

    class Config:
        from_attributes = True

class BooksList(BaseModel):
    books: List[Book]
    total: int

class Stats(BaseModel):
    total_books: int
    genres_count: dict

class ISBNRequest(BaseModel):
    isbn: str
