from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import settings

# Normalize the DB URL to the psycopg (v3) driver. Managed hosts like Railway
# inject a bare "postgres://" / "postgresql://" URL, which SQLAlchemy maps to
# psycopg2 — a driver we don't install. Rewrite it to "postgresql+psycopg://".
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgres://"):
    _db_url = "postgresql+psycopg://" + _db_url[len("postgres://"):]
elif _db_url.startswith("postgresql://"):
    _db_url = "postgresql+psycopg://" + _db_url[len("postgresql://"):]

engine = create_engine(
    _db_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
