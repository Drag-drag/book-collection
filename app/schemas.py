from pydantic import BaseModel


class BookBase(BaseModel):
    title: str
    author: str
    genre: str | None
    status: str

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    status: str | None

class BookInDB(BaseModel):
    id: int
    title: str
    author: str
    genre: str
    status: str

    class Config:
        from_attributes = True

class Book(BookBase):
    id: int

    class Config:
        from_attributes = True
