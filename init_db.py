# KI-Anfang
# KI: Claude
# prompt: init_db.py das die Datenbank komplett zurücksetzt und einen Standard-Admin anlegt
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from datetime import date
from database import engine, Base, SessionLocal
import models
from models import DBAccount, Role
from auth import hash_password


def init():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = DBAccount(
            email="admin@gmail.com",
            password=hash_password("admin123"),
            firstname="Admin",
            lastname="Admin",
            phonenumber="0000000000",
            address="Bank HQ",
            birthdate=date(2000, 1, 1),
            role=Role.manager
        )
        db.add(admin)
        db.commit()
        print("Admin created: admin@gmail.com / admin123")
    finally:
        db.close()

    print("Done.")


if __name__ == "__main__":
    init()
# KI-Ende
