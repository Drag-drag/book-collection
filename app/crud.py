from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Any
from collections import Counter
import numpy as np

from . import models, schemas
from .ml import ml_service


def create_book(db: Session, book: schemas.BookCreate) -> schemas.Book:
    embedding = ml_service.generate_embedding(
        title=book.title,
        author=book.author,
        genre=book.genre or "",
        description=book.description or ""
    )

    db_book = models.Book(**book.model_dump(), embedding=embedding)
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

        db_book.embedding = ml_service.generate_embedding(
            title=db_book.title,
            author=db_book.author,
            genre=db_book.genre or "",
            description=db_book.description or ""
        )

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

    genres_count = {genre.capitalize(): count for genre, count in genres_counter.items()}
    author_rows = db.query(models.Book.author).filter(models.Book.author.isnot(None)).all()
    authors_counter = Counter(row.author.strip() for row in author_rows if row.author)
    top_authors = dict(authors_counter.most_common(10))

    return {"total_books": total, "genres_count": genres_count, "top_authors": top_authors}


def get_similar_books(db: Session, target_book_id: int, limit: int = 5) -> List[schemas.Book]:
    target_book = db.query(models.Book).filter(models.Book.id == target_book_id).first()
    if not target_book or target_book.embedding is None:
        return []

    all_books = db.query(models.Book).filter(models.Book.id != target_book_id).all()

    similarities = []
    for book in all_books:
        if book.embedding is not None:
            score = ml_service.cosine_similarity(target_book.embedding, book.embedding)
            # Порог схожести
            if score > 0.4:
                similarities.append((book, score))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return [schemas.Book.model_validate(item[0]) for item in similarities[:limit]]
