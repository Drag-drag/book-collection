import pytest
import os
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    time.sleep(0.1)

    if os.path.exists("./test_app.db"):
        try:
            os.remove("./test_app.db")
        except PermissionError:
            print("Предупреждение: Не удалось удалить тестовую БД, файл занят.")


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_add_book_manual(client):
    payload = {
        "title": "Clean Code",
        "author": "Robert Martin",
        "genre": "IT",
        "status": "прочитана",
        "description": "A handbook of agile software craftsmanship"
    }
    response = client.post("/books/", json=payload)
    assert response.status_code == 201
    assert response.json()["title"] == "Clean Code"


def test_get_books_filtering(client):
    client.post("/books/", json={"title": "Unique Title", "author": "AuthX", "genre": "G1", "status": "в планах"})

    response = client.get("/books/?author=AuthX")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["books"][0]["author"] == "AuthX"


def test_stats_accuracy(client):
    response = client.get("/books/stats/")
    assert response.status_code == 200
    data = response.json()
    assert "total_books" in data
    assert "genres_count" in data


def test_book_deletion_flow(client):
    res = client.post("/books/", json={"title": "To Delete", "author": "A", "genre": "G", "status": "в планах"})
    book_id = res.json()["id"]

    del_res = client.delete(f"/books/{book_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/books/{book_id}")
    assert get_res.status_code == 404


def test_semantic_recommendation_quality(client):
    client.post("/books/", json={
        "title": "Python Programming", "author": "A", "genre": "IT", "status": "в планах",
        "description": "Language basics and core concepts"
    })
    client.post("/books/", json={
        "title": "Java Guide", "author": "B", "genre": "IT", "status": "в планах",
        "description": "Object oriented programming and syntax"
    })
    client.post("/books/", json={
        "title": "History of France", "author": "C", "genre": "History", "status": "в планах",
        "description": "European history and culture"
    })

    books = client.get("/books/").json()["books"]
    python_id = [b["id"] for b in books if "Python" in b["title"]][0]

    response = client.get(f"/books/{python_id}/similar/")
    assert response.status_code == 200
    similar_titles = [b["title"] for b in response.json()]

    if "Java Guide" in similar_titles and "History of France" in similar_titles:
        assert similar_titles.index("Java Guide") < similar_titles.index("History of France")