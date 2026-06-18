# KI-Anfang
# KI: Claude
# prompt: init_db.py Skript das alle SQLAlchemy Tabellen anlegt ohne die App zu starten
from src.database import engine, Base
import src.models

def init():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init()
# KI-Ende
