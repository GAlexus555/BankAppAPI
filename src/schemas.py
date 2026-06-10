from pydantic import BaseModel, Field, EmailStr, field_validator
from models import Role, Status, TransactionStatus
from datetime import date

class AccountBase(BaseModel):
    role: Role = Role.client
    firstname: str = Field(...)
    lastname: str = Field(...)

    @field_validator("firstname", "lastname")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.replace("-", "").replace(" ", "").isalpha(): # .replace löscht alle "-"" und " " damit ez auf nur buchstaben geschaut wird
            raise ValueError("Name must only contain letters, hyphens or spaces") # hyphens sind so -
        if len(value) < 3 or len(value) > 30:
            raise ValueError("Name must be between 3 and 30 characters long")
        return value.strip()
    
    email: EmailStr
    phonenumber: str
    address: str
    birthdate: date

class AccountCreate(AccountBase):
    password: str = Field(...)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit")
        return value

class AccountOut(AccountBase):
    id: int
    created_at: date

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ==================================================================================================

class CardBase(BaseModel):
    cents: int
    status: Status = Status.Inactive
    owner_id: int

    iban: str = Field(...) 

    @field_validator("iban")
    @classmethod
    def validate_iban(cls, value: str) -> str:
        value = value.replace(" ", "").upper() # .uppper macht zu großbuchstabne
        if not value[:2].isalpha() or not value[2:].isalnum(): # muss anfangen mit AT, DE, ... und aufhören mit nummern (.isalpha schaut auf buchstaben, .isalnum schaut auf zahlen (ohne sonderzeichen ))
            raise ValueError("IBAN must start with a 2-letter country code")
        if len(value) < 15 or len(value) > 34:  
            raise ValueError("IBAN length is invalid")
        return value

    card_nr: str = Field(...)

    @field_validator("card_nr")
    @classmethod
    def validate_card_nr(cls, value: str) -> str:
        value = value.replace(" ", "")
        if not value.isdigit():
            raise ValueError("Card number must contain only digits")
        if len(value) < 13 or len(value) > 16:
            raise ValueError("Card number must be between 13 and 16 digits")
        return value

    
    cvc: int
    expire_date: date

class CardCreate(CardBase):
    pass

class CardResponse(CardBase):
    id: int
    created_at: date

    class Config:
        from_attributes = True

#=====================================================================================================

class TransactionBase(BaseModel):
    amount_cents: int

    iban_from: str
    iban_to: str

    @field_validator("amount_cents")
    @classmethod
    def validate_amount_cents(cls, value: int):
        if value <= 0:
            raise ValueError(
                "The transaction amount can't be lower or exactly 0"
            )
        return value

    description: str
    status: TransactionStatus = TransactionStatus.Pending

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    created_at: date

    class Config:
        from_attributes = True

#==========================================================================

class InterestBase(BaseModel):
    card_id: int
    amount: int

class CreateInterest(InterestBase):
    pass

class GetInterest(InterestBase):
    created_at: date
    id: int

    class Config:
        from_attributes = True

#====================================================================

class BankBase(BaseModel):
    bankname: str
    interest_rate: float

class CreateBank(BankBase):
    pass

class GetBank(BankBase):
    id: int

    class Config:
        from_attributes = True

