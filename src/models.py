from sqlalchemy import Column, Integer, String, Boolean, Date
from database import Base
from enum import IntEnum

class Role(IntEnum):
    client = 0,
    manager = 1

class DBAccount(Base):
    __tablename__ = "accounts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    password = Column(String, nullable=False)
    email = Column(String, index=True, nullable=False)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    phonenumber = Column(String, nullable=False)
    address = Column(String, nullable=False)
    birthdate = Column(Date, nullable=False)
    createdat = Column(Date, nullable=False)
    role = Column(Integer, default=Role.client, nullable=False)