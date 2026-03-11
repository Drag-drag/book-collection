from pydantic import BaseModel
from typing import List


class BookBase(BaseModel):
    title: str
    author: str
    genre: str | None
    status: str | None

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    status: str | None

class BookInDB(BaseModel):
    id: int
    title: str
    author: str
    genre: str | None
    status: str

    class Config:
        from_attributes = True

class Book(BookBase):
    id: int

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