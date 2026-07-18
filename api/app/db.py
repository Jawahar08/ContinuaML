from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

# For SQLite, we add connect_args to avoid sharing session threads errors
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session
