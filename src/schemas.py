from pydantic import BaseModel, Field, EmailStr
from models import Role
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
    createdat: date

    model_config = {"from_attributes": True}

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"