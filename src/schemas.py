from pydantic import BaseModel, Field, EmailStr, field_validator
from models import Role, Status, TransactionStatus
from datetime import date, datetime

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


    @field_validator("phonenumber")
    @classmethod
    def validate_phonenumber(cls, value: str) -> str:
        value = value.replace(" ", "").replace("-", "")
        if not value.lstrip("+").isalnum(): # lstrip("+") macht vom anfang der nummer das + weg das man nur auf nummern überprüfen kann
            raise ValueError("Phone number must contain only digits, spaces, hyphens or a + at the start")
        if len(value) < 7 or len(value) > 15:
            raise ValueError("Phone number must be between 7 and 15 digits")
        return value

    address: str

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        if len(value) < 5 or len(value) > 100:
            raise ValueError("Address must be between 5 and 100 characters")
        return value.strip()

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

class CardUpdate(BaseModel):
    status: Status
    expire_date: date

class CardResponse(CardBase):
    id: int
    created_at: date

    class Config:
        from_attributes = True

#=====================================================================================================

class TransactionBase(BaseModel):
    amount_cents: int

    @field_validator("amount_cents")
    @classmethod
    def validate_amount_cents(cls, value: int):
        if value <= 0:
            raise ValueError(
                "The transaction amount can't be lower or exactly 0"
            )
        return value

    iban_from: str
    iban_to: str

    @field_validator("iban_from", "iban_to")
    @classmethod
    def validate_ibans(cls, value: str) -> str:
        value = value.replace(" ", "").upper()
        if not value[:2].isalpha() or not value[2:].isalnum():
            raise ValueError("IBAN must start with a 2-letter country code")
        if len(value) < 15 or len(value) > 34:
            raise ValueError("IBAN length is invalid")
        return value


    description: str = Field(..., max_length=255)
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
    withdrawn: bool
    interest_rate: float

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

#====================================================================

class TransactionStats(BaseModel):
    account_id: int
    firstname: str
    lastname: str
    transaction_count: int
    total_cents: int

    class Config:
        from_attributes = True

class GetAuditLog(BaseModel):
    id: int
    account_id: int
    timestamp: datetime
    tablename: str
    action: str
    details: str | None

    class Config:
        from_attributes = True