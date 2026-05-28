from pydantic import BaseModel, Field, field_validator

class AccountBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=40)