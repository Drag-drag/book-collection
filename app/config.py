from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
SQLALCHEMY_DATABASE_URI = "sqlite:///./books_collection.db"
