import httpx
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session

from .. import models, schemas
from ..ml import ml_service


class RecommendationStrategy(ABC):
    @abstractmethod
    def recommend(self, db: Session, target_book: models.Book, limit: int) -> List[models.Book]:
        pass


class SemanticRecommendationStrategy(RecommendationStrategy):
    def recommend(self, db: Session, target_book: models.Book, limit: int) -> List[models.Book]:
        if target_book.embedding is None:
            return []
        all_books = db.query(models.Book).filter(models.Book.id != target_book.id).all()
        similarities = []
        for book in all_books:
            if book.embedding is not None:
                score = ml_service.cosine_similarity(target_book.embedding, book.embedding)
                if score > 0.4:
                    similarities.append((book, score))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in similarities[:limit]]


class BookService:
    def __init__(self, db: Session, rec_strategy: RecommendationStrategy = None):
        self.db = db
        self.rec_strategy = rec_strategy or SemanticRecommendationStrategy()

    def get_all(self, author: str = None, genre: str = None) -> List[models.Book]:
        query = self.db.query(models.Book)
        if author:
            query = query.filter(models.Book.author.ilike(f"%{author}%"))
        if genre:
            query = query.filter(models.Book.genre.ilike(f"%{genre}%"))
        return query.all()

    def get_by_id(self, book_id: int) -> Optional[models.Book]:
        return self.db.query(models.Book).filter(models.Book.id == book_id).first()

    def create_book(self, book_data: schemas.BookCreate) -> models.Book:
        embedding = ml_service.generate_embedding(
            title=book_data.title,
            author=book_data.author,
            genre=book_data.genre or "",
            description=book_data.description or ""
        )
        db_book = models.Book(**book_data.model_dump(), embedding=embedding)
        self.db.add(db_book)
        self.db.commit()
        self.db.refresh(db_book)
        return db_book

    async def create_from_isbn(self, isbn: str) -> models.Book:
        isbn_clean = ''.join(filter(str.isdigit, isbn))
        volume = None

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_clean}", timeout=5.0)
            if resp.status_code == 200 and resp.json().get("totalItems", 0) > 0:
                volume = resp.json()["items"][0]["volumeInfo"]
            else:
                resp = await client.get(f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn_clean}&format=json&jscmd=data",
                                        timeout=5.0)
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
                            "description": ol_book.get("description") or ol_book.get("by_statement"),
                        }

        if not volume:
            raise ValueError("Книга не найдена во внешних сервисах")

        authors = volume.get("authors", ["Неизвестен"])
        categories = volume.get("categories", [])
        print(categories)
        new_book_data = schemas.BookCreate(
            title=volume.get("title", "Без названия"),
            author=", ".join([i.get('name') for i in authors]),
            genre=", ".join([i.get('name') for i in categories]) if categories else "Разное",
            status="в планах",
            description=volume.get("description"),
            isbn=isbn_clean,
            image=volume.get("imageLinks", {}).get("thumbnail")
        )
        return self.create_book(new_book_data)

    def update_book(self, book_id: int, book_data: schemas.BookUpdate) -> Optional[models.Book]:
        db_book = self.get_by_id(book_id)
        if not db_book:
            return None

        update_dict = book_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_book, key, value)

        db_book.embedding = ml_service.generate_embedding(
            title=db_book.title,
            author=db_book.author,
            genre=db_book.genre or "",
            description=db_book.description or ""
        )

        self.db.commit()
        self.db.refresh(db_book)
        return db_book

    def delete_book(self, book_id: int) -> bool:
        db_book = self.get_by_id(book_id)
        if db_book:
            self.db.delete(db_book)
            self.db.commit()
            return True
        return False

    def get_similar_books(self, book_id: int, limit: int = 5) -> List[models.Book]:
        target_book = self.get_by_id(book_id)
        if not target_book:
            return []
        return self.rec_strategy.recommend(self.db, target_book, limit)

    def get_stats(self) -> dict:
        from collections import Counter
        total = self.db.query(models.Book).count()
        genres = [r.genre for r in self.db.query(models.Book.genre).all() if r.genre]

        genres_counter = Counter()
        for g in genres:
            genres_counter.update([i.strip().capitalize() for i in g.split(",")])

        return {
            "total_books": total,
            "genres_count": dict(genres_counter)
        }
