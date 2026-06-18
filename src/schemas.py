from pydantic import BaseModel, Field, EmailStr, field_validator
from models import Role, Status, TransactionStatus
from datetime import date, datetime


# ──────────────────────────────────────────────────────────────────────────────
# Accounts
# ──────────────────────────────────────────────────────────────────────────────

class AccountBase(BaseModel):
    role: Role = Field(
        default=Role.client,
        description="Benutzerrolle: `0` = client, `1` = manager",
        example=0,
    )
    firstname: str = Field(
        ...,
        min_length=3, max_length=30,
        description="Vorname – 3 bis 30 Zeichen, nur Buchstaben, Bindestriche und Leerzeichen",
        example="Max",
    )
    lastname: str = Field(
        ...,
        min_length=3, max_length=30,
        description="Nachname – 3 bis 30 Zeichen, nur Buchstaben, Bindestriche und Leerzeichen",
        example="Mustermann",
    )

    @field_validator("firstname", "lastname")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.replace("-", "").replace(" ", "").isalpha():
            raise ValueError("Name must only contain letters, hyphens or spaces")
        if len(value) < 3 or len(value) > 30:
            raise ValueError("Name must be between 3 and 30 characters long")
        return value.strip()

    email: EmailStr = Field(
        ...,
        description="Gültige E-Mail-Adresse",
        example="max.mustermann@example.com",
    )
    phonenumber: str = Field(
        ...,
        description="Telefonnummer – 7 bis 15 Ziffern, optional mit führendem `+`, Leerzeichen und Bindestriche erlaubt",
        example="+43123456789",
    )

    @field_validator("phonenumber")
    @classmethod
    def validate_phonenumber(cls, value: str) -> str:
        value = value.replace(" ", "").replace("-", "")
        if not value.lstrip("+").isalnum():
            raise ValueError("Phone number must contain only digits, spaces, hyphens or a + at the start")
        if len(value) < 7 or len(value) > 15:
            raise ValueError("Phone number must be between 7 and 15 digits")
        return value

    address: str = Field(
        ...,
        min_length=5, max_length=100,
        description="Vollständige Adresse – 5 bis 100 Zeichen",
        example="Musterstraße 1, 1010 Wien",
    )

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        if len(value) < 5 or len(value) > 100:
            raise ValueError("Address must be between 5 and 100 characters")
        return value.strip()

    birthdate: date = Field(
        ...,
        description="Geburtsdatum im Format `YYYY-MM-DD`",
        example="1990-06-15",
    )


class AccountCreate(AccountBase):
    password: str = Field(
        ...,
        min_length=8,
        description="Passwort – mindestens 8 Zeichen, mind. 1 Großbuchstabe und 1 Ziffer",
        example="Sicher1!",
    )

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

    class Config:
        json_schema_extra = {
            "example": {
                "firstname": "Max",
                "lastname": "Mustermann",
                "email": "max.mustermann@example.com",
                "password": "Sicher1!",
                "phonenumber": "+43123456789",
                "address": "Musterstraße 1, 1010 Wien",
                "birthdate": "1990-06-15",
                "role": 0,
            }
        }


class AccountOut(AccountBase):
    id: int = Field(..., description="Eindeutige Benutzer-ID", example=1)
    created_at: datetime = Field(..., description="Erstellungszeitpunkt des Kontos")

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="max.mustermann@example.com")
    password: str   = Field(..., example="Sicher1!")


class TokenOut(BaseModel):
    access_token: str = Field(..., description="JWT Bearer-Token")
    token_type: str   = Field(default="bearer", description="Token-Typ, immer `bearer`")


# ──────────────────────────────────────────────────────────────────────────────
# Cards
# ──────────────────────────────────────────────────────────────────────────────

class CardBase(BaseModel):
    cents: int = Field(
        ...,
        ge=0,
        description="Guthaben in Cent (≥ 0). Beispiel: `5000` = 50,00 €",
        example=5000,
    )
    status: Status = Field(
        default=Status.Inactive,
        description="Kartenstatus: `0` = Active, `1` = Inactive, `2` = Blocked, `3` = Expired",
        example=1,
    )
    owner_id: int = Field(
        ...,
        gt=0,
        description="ID des Karteninhabers (> 0)",
        example=1,
    )
    iban: str = Field(
        ...,
        min_length=15, max_length=34,
        description="IBAN – 15 bis 34 Zeichen, beginnt mit 2-buchstabigem Ländercode",
        example="AT611904300234573201",
    )

    @field_validator("iban")
    @classmethod
    def validate_iban(cls, value: str) -> str:
        value = value.replace(" ", "").upper()
        if not value[:2].isalpha() or not value[2:].isalnum():
            raise ValueError("IBAN must start with a 2-letter country code")
        if len(value) < 15 or len(value) > 34:
            raise ValueError("IBAN length is invalid")
        return value

    card_nr: str = Field(
        ...,
        min_length=13, max_length=16,
        description="Kartennummer – 13 bis 16 Ziffern, nur Ziffern erlaubt",
        example="4539578763621486",
    )

    @field_validator("card_nr")
    @classmethod
    def validate_card_nr(cls, value: str) -> str:
        value = value.replace(" ", "")
        if not value.isdigit():
            raise ValueError("Card number must contain only digits")
        if len(value) < 13 or len(value) > 16:
            raise ValueError("Card number must be between 13 and 16 digits")
        return value

    cvc: int = Field(
        ...,
        ge=100, le=9999,
        description="CVC/CVV – 3-stellig (100–999) oder 4-stellig (1000–9999)",
        example=123,
    )
    expire_date: date = Field(
        ...,
        description="Ablaufdatum der Karte im Format `YYYY-MM-DD`",
        example="2028-12-31",
    )


class CardCreate(CardBase):
    class Config:
        json_schema_extra = {
            "example": {
                "cents": 5000,
                "status": 1,
                "owner_id": 1,
                "iban": "AT611904300234573201",
                "card_nr": "4539578763621486",
                "cvc": 123,
                "expire_date": "2028-12-31",
            }
        }


class CardUpdate(BaseModel):
    status: Status = Field(
        ...,
        description="Neuer Kartenstatus: `0` = Active, `1` = Inactive, `2` = Blocked, `3` = Expired",
        example=2,
    )
    expire_date: date = Field(
        ...,
        description="Neues Ablaufdatum im Format `YYYY-MM-DD`",
        example="2028-12-31",
    )

    class Config:
        json_schema_extra = {
            "example": {"status": 2, "expire_date": "2028-12-31"}
        }


class CardResponse(CardBase):
    id: int          = Field(..., description="Eindeutige Karten-ID", example=1)
    created_at: datetime = Field(..., description="Erstellungszeitpunkt der Karte")

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────────────────────────
# Transactions
# ──────────────────────────────────────────────────────────────────────────────

class TransactionBase(BaseModel):
    amount_cents: int = Field(
        ...,
        gt=0,
        description="Überweisungsbetrag in Cent (> 0). Beispiel: `1000` = 10,00 €",
        example=1000,
    )

    @field_validator("amount_cents")
    @classmethod
    def validate_amount_cents(cls, value: int):
        if value <= 0:
            raise ValueError("The transaction amount can't be lower or exactly 0")
        return value

    iban_from: str = Field(
        ...,
        description="IBAN des Absenders – 15 bis 34 Zeichen",
        example="AT611904300234573201",
    )
    iban_to: str = Field(
        ...,
        description="IBAN des Empfängers – 15 bis 34 Zeichen",
        example="AT483200000012345864",
    )

    @field_validator("iban_from", "iban_to")
    @classmethod
    def validate_ibans(cls, value: str) -> str:
        value = value.replace(" ", "").upper()
        if not value[:2].isalpha() or not value[2:].isalnum():
            raise ValueError("IBAN must start with a 2-letter country code")
        if len(value) < 15 or len(value) > 34:
            raise ValueError("IBAN length is invalid")
        return value

    description: str = Field(
        ...,
        max_length=255,
        description="Verwendungszweck – max. 255 Zeichen",
        example="Miete März 2025",
    )
    status: TransactionStatus = Field(
        default=TransactionStatus.Pending,
        description="Transaktionsstatus: `0` = Pending, `1` = Sent",
        example=1,
    )


class TransactionCreate(TransactionBase):
    class Config:
        json_schema_extra = {
            "example": {
                "amount_cents": 1000,
                "iban_from": "AT611904300234573201",
                "iban_to": "AT483200000012345864",
                "description": "Miete März 2025",
                "status": 0,
            }
        }


class TransactionResponse(TransactionBase):
    id: int              = Field(..., description="Eindeutige Transaktions-ID", example=1)
    created_at: datetime = Field(..., description="Zeitpunkt der Transaktion")

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────────────────────────
# Interests (Sparzinsen)
# ──────────────────────────────────────────────────────────────────────────────

class InterestBase(BaseModel):
    card_id: int = Field(
        ...,
        gt=0,
        description="ID der Karte, von der der Betrag abgebucht wird (> 0)",
        example=1,
    )
    amount: int = Field(
        ...,
        gt=0,
        description="Anlagebetrag in Cent (> 0). Muss als Guthaben auf der Karte vorhanden sein",
        example=10000,
    )


class CreateInterest(InterestBase):
    class Config:
        json_schema_extra = {
            "example": {"card_id": 1, "amount": 10000}
        }


class GetInterest(InterestBase):
    created_at: datetime = Field(..., description="Anlagezeitpunkt")
    id: int             = Field(..., description="Eindeutige Zinsen-ID", example=1)
    withdrawn: bool     = Field(..., description="`true` wenn bereits ausgezahlt", example=False)
    interest_rate: float = Field(..., description="Jahreszinssatz zum Anlagezeitpunkt (z. B. `0.035` = 3,5 %)", example=0.035)

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────────────────────────
# Bank
# ──────────────────────────────────────────────────────────────────────────────

class BankBase(BaseModel):
    bankname: str = Field(
        ...,
        min_length=1, max_length=100,
        description="Name der Bank – 1 bis 100 Zeichen",
        example="Österreichische Sparbank",
    )
    interest_rate: float = Field(
        ...,
        gt=0, le=1,
        description="Jahreszinssatz als Dezimalzahl (0 < Wert ≤ 1). Beispiel: `0.035` = 3,5 %",
        example=0.035,
    )


class CreateBank(BankBase):
    class Config:
        json_schema_extra = {
            "example": {"bankname": "Österreichische Sparbank", "interest_rate": 0.035}
        }


class GetBank(BankBase):
    id: int = Field(..., description="Eindeutige Bank-ID", example=1)

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────────────────────────
# Stats & Audit
# ──────────────────────────────────────────────────────────────────────────────

class TransactionStats(BaseModel):
    account_id: int        = Field(..., description="Benutzer-ID", example=1)
    firstname: str         = Field(..., description="Vorname", example="Max")
    lastname: str          = Field(..., description="Nachname", example="Mustermann")
    transaction_count: int = Field(..., description="Anzahl ausgehender Transaktionen", example=12)
    total_cents: int       = Field(..., description="Gesamtvolumen ausgehender Transaktionen in Cent", example=150000)

    class Config:
        from_attributes = True


class GetAuditLog(BaseModel):
    id: int             = Field(..., description="Eindeutige Log-ID", example=1)
    account_id: int     = Field(..., description="ID des ausführenden Benutzers", example=1)
    timestamp: datetime = Field(..., description="Zeitpunkt der Aktion (UTC)", example="2025-03-01T10:30:00")
    tablename: str      = Field(..., description="Betroffene Datenbanktabelle", example="accounts")
    action: str         = Field(..., description="Durchgeführte Aktion", example="CREATE")
    details: str | None = Field(None, description="Optionale Zusatzinformationen", example="email=max@example.com")

    class Config:
        from_attributes = True
