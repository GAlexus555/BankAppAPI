from sqlalchemy import Column, Integer, String, Date, Boolean, TIMESTAMP, text, ForeignKey, Double, Float
from sqlalchemy.orm import relationship
from database import Base
from enum import IntEnum

class Role(IntEnum):
    client = 0
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
    Active = 0
    Inactive = 1
    Blocked = 2
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
    Pending = 0
    Sent = 1

class DBTransaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)

    from_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"))
    to_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"))

    from_card = relationship("DBCard", foreign_keys=[from_id])
    to_card = relationship("DBCard", foreign_keys=[to_id])

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    description = Column(String, nullable=False)
    status = Column(Integer, default=TransactionStatus.Pending, nullable=False)

    amount_cents = Column(Integer)

    @property
    def iban_from(self):
        return self.from_card.iban

    @property
    def iban_to(self):
        return self.to_card.iban

class DBInterest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"))
    amount = Column(Double)
    interest_rate = Column(Double, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    withdrawn = Column(Boolean, default=False)

class DBBank(Base):
    __tablename__ = "bank"
    id = Column(Integer, primary_key=True)
    bankname = Column(String, nullable=False, index=True)
    interest_rate = Column(Float, nullable=False)

class DBAuiditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"))
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    tablename = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(String)