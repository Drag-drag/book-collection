import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.schemas import BookCreate


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_book():
    response = client.post(
        "/books/",
        json={
            "title": "Тестовая книга",
            "author": "Иван Иванов",
            "genre": "Фантастика",
            "status": "читаю",
            "isbn": "1234567890"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестовая книга"
    assert data["author"] == "Иван Иванов"
    assert "id" in data


def test_read_books():
    client.post("/books/", json={
        "title": "Книга 1", "author": "Автор 1", "status": "в планах"
    })

    response = client.get("/books/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["books"]) == 1
    assert data["books"][0]["title"] == "Книга 1"


def test_read_book_by_id():
    create_resp = client.post("/books/", json={
        "title": "Уникальная книга", "author": "Автор", "status": "прочитано"
    })
    book_id = create_resp.json()["id"]

    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Уникальная книга"


def test_update_book():
    create_resp = client.post("/books/", json={
        "title": "Старое название", "author": "Автор", "status": "в планах"
    })
    book_id = create_resp.json()["id"]


    response = client.put(
        f"/books/{book_id}",
        json={
            "title": "Новое название",
            "author": "Автор",
            "status": "прочитано"
        }
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Новое название"
    assert response.json()["status"] == "прочитано"


def test_delete_book():
    create_resp = client.post("/books/", json={
        "title": "На удаление", "author": "Автор", "status": "в планах"
    })
    book_id = create_resp.json()["id"]

    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 204


    get_resp = client.get(f"/books/{book_id}")
    assert get_resp.status_code == 404


def test_get_stats():
    client.post("/books/", json={"title": "К1", "author": "А1", "genre": "Детектив", "status": "прочитано"})
    client.post("/books/", json={"title": "К2", "author": "А1", "genre": "Детектив, Триллер", "status": "прочитано"})

    response = client.get("/books/stats/")
    assert response.status_code == 200
    data = response.json()
    assert data["total_books"] == 2

    assert data["genres_count"]["Детектив"] == 2
    assert data["genres_count"]["Триллер"] == 1
    assert data["top_authors"]["А1"] == 2


def test_create_from_isbn_mock(mocker):
    mock_get = mocker.patch("httpx.AsyncClient.get")

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "totalItems": 1,
        "items": [{
            "volumeInfo": {
                "title": "Книга из API",
                "authors": [{"name": "Известный Автор"}],
                "categories": ["Наука"],
                "imageLinks": {"thumbnail": "http://image.jpg"},
                "description": "Описание"
            }
        }]
    }
    mock_get.return_value = mock_response

    response = client.post("/books/from-isbn", json={"isbn": "9785123456789"})

    assert response.status_code == 201
    assert response.json()["title"] == "Книга из API"
    assert response.json()["author"] == "Известный Автор"
