from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class DBAccount(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)