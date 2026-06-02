from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMIE_URL = "sqlite:///src/cool_db.db"

# engine erstellen
engine = create_engine(SQLALCHEMIE_URL, connect_args={"check_same_thread": False})

# Session Factory erstellen
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base erstellen
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()