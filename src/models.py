from sqlalchemy import Column, Integer, String, Date, Boolean, TIMESTAMP, text, ForeignKey
from database import Base
from enum import IntEnum

class Role(IntEnum):
    client = 0,
    manager = 1

class DBAccount(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    password = Column(String, nullable=False)
    email = Column(String, index=True, nullable=False)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    phonenumber = Column(String, nullable=False)
    address = Column(String, nullable=False)
    birthdate = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    role = Column(Integer, default=Role.client, nullable=False)


class Status(IntEnum):
    Active = 0,
    Inactive = 1,
    Blocked = 2,
    Expired = 3

class DBCard(Base):
    __tablename__ = "cards"

    cents = Column(Integer)

    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    owner_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)

    iban = Column(String, nullable=False)
    card_nr = Column(String, nullable=False)
    expire_date = Column(Date, nullable=False)
    cvc = Column(Integer, nullable=False)
    status = Column(Integer, default=Status.Inactive, nullable=False)


class TransactionStatus(IntEnum):
    Pending = 0,
    Sent = 1

class DBTransaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    from_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    to_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    description = Column(String, nullable=False)
    status = Column(Integer, default=TransactionStatus.Pending, nullable=False)

    amount_cents = Column(Integer)

