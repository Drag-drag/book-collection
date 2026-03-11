# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional, Any
from datetime import datetime
from pydantic import model_dump

from . import models, schemas


def create_book(db: Session, book: schemas.BookCreate) -> schemas.Book:
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return schemas.Book.model_validate(db_book)


def get_books(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        author: Optional[str] = None,
        genre: Optional[str] = None
) -> List[schemas.Book]:
    query = db.query(models.Book)

    # Фильтры
    if author:
        query = query.filter(models.Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.filter(models.Book.genre.ilike(f"%{genre}%"))

    return query.offset(skip).limit(limit).all()


def get_book(db: Session, book_id: int) -> Optional[schemas.Book]:
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def get_books_count(
        db: Session,
        author: Optional[str] = None,
        genre: Optional[str] = None
) -> int:
    query = db.query(func.count(models.Book.id))

    if author:
        query = query.filter(models.Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.filter(models.Book.genre.ilike(f"%{genre}%"))

    return query.scalar()


def update_book(
        db: Session,
        book_id: int,
        book: schemas.BookUpdate
) -> Optional[schemas.Book]:
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        update_data = book.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_book, field, value)
        db_book.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_book)
        return schemas.Book.model_validate(db_book)
    return None


def delete_book(db: Session, book_id: int) -> bool:
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        db.delete(db_book)
        db.commit()
        return True
    return False


def get_stats(db: Session) -> model_dump[str, Any]:
    total = get_books_count(db)

    # Количество по жанрам
    genres = db.query(
        models.Book.genre,
        func.count(models.Book.id)
    ).group_by(models.Book.genre).all()

    genres_count = {genre: count for genre, count in genres}


    return {
        "total_books": total,
        "genres_count": genres_count,
        "latest_year": db.query(func.max(models.Book.year)).scalar()
    }


def get_similar_books(
        db: Session,
        author: str,
        genre: str,
        limit: int = 5,
        exclude_id: int = None
) -> List[schemas.Book]:
    query = db.query(models.Book).filter(
        and_(
            models.Book.author.ilike(f"%{author}%"),
            models.Book.genre.ilike(f"%{genre}%")
        )
    )

    if exclude_id:
        query = query.filter(models.Book.id != exclude_id)

    return query.limit(limit).all()