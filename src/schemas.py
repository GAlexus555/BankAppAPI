from pydantic import BaseModel, Field, EmailStr, field_validator
from models import Role, Status, TransactionStatus
from datetime import date

class AccountBase(BaseModel):
    role: Role = Role.client
    firstname: str = Field(..., min_length=3, max_length=30)
    lastname: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    phonenumber: str
    address: str
    birthdate: date

class AccountCreate(AccountBase):
    password: str = Field(..., min_length=8)

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
    iban: str = Field(..., min_length=16)
    card_nr: str = Field(..., min_length=8, max_length=19)
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

