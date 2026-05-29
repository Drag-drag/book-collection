from sqlalchemy import Column, Integer, String, DateTime, func, PickleType
from .database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    genre = Column(String(50), nullable=True, index=True)
    status = Column(String(50), nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    isbn = Column(String(13), unique=True, index=True, nullable=True)
    image = Column(String, nullable=True)
    embedding = Column(PickleType, nullable=True)

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"
