from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Any
from collections import Counter
from . import models, schemas


def create_book(db: Session, book: schemas.BookCreate) -> schemas.Book:
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return schemas.Book.model_validate(db_book)


def get_books(db: Session, author: Optional[str] = None, genre: Optional[str] = None) -> List[schemas.Book]:
    query = db.query(models.Book)
    if author:
        query = query.filter(models.Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.filter(models.Book.genre.ilike(f"%{genre}%"))
    return query.all()


def get_book(db: Session, book_id: int) -> Optional[schemas.Book]:
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def get_books_count(db: Session, author: Optional[str] = None, genre: Optional[str] = None) -> int:
    query = db.query(func.count(models.Book.id))
    if author:
        query = query.filter(models.Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.filter(models.Book.genre.ilike(f"%{genre}%"))
    return query.scalar()


def update_book(db: Session, book_id: int, book: schemas.BookUpdate) -> Optional[schemas.Book]:
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book:
        update_data = book.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_book, field, value)
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


def get_stats(db: Session) -> dict[str, Any]:
    total = get_books_count(db)
    genre_rows = db.query(models.Book.genre).filter(models.Book.genre.isnot(None)).all()
    genres_counter = Counter()
    for row in genre_rows:
        if row.genre:
            split_genres = [g.strip().lower() for g in row.genre.split(",") if g.strip()]
            genres_counter.update(split_genres)

    genres_count = {g.capitalize(): c for g, c in genres_counter.items()}

    author_rows = db.query(models.Book.author).filter(models.Book.author.isnot(None)).all()
    authors_counter = Counter(r.author.strip() for r in author_rows if r.author)
    top_authors = dict(authors_counter.most_common(10))

    return {"total_books": total, "genres_count": genres_count, "top_authors": top_authors}


def get_similar_books(db: Session, author: str, genre: str, limit: int = 5, exclude_id: int = None) -> List[
    schemas.Book]:
    query = db.query(models.Book).filter(or_(
        models.Book.author.ilike(f"%{author}%"),
        models.Book.genre.ilike(f"%{genre}%")
    ))
    if exclude_id:
        query = query.filter(models.Book.id != exclude_id)
    return query.limit(limit).all()