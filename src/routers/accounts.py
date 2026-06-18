from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import DBAccount, Role
from schemas import AccountCreate, AccountOut, TokenOut
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, require_role
)
from audit import AuditLogger

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@cbv(router)
class AccountsAPI():
    db: Session = Depends(get_db)


    @router.post(
        "/register",
        response_model=AccountOut,
        status_code=201,
        summary="Neues Konto registrieren",
        description="""
Erstellt ein neues Benutzerkonto. Keine Authentifizierung erforderlich.

**Wertebereiche:**
- `firstname`, `lastname`: 3–30 Zeichen, nur Buchstaben, Bindestriche, Leerzeichen
- `email`: gültige E-Mail-Adresse (eindeutig im System)
- `password`: mindestens 8 Zeichen, mind. 1 Großbuchstabe und 1 Ziffer
- `phonenumber`: 7–15 Ziffern, optional `+` am Anfang, Leerzeichen/Bindestriche erlaubt
- `address`: 5–100 Zeichen
- `birthdate`: Format `YYYY-MM-DD`
- `role`: `0` = client (Standard), `1` = manager

**Fehler:**
- `409` – E-Mail bereits registriert
""",
    )
    def register(self, createAccount: AccountCreate):
        if self.db.query(DBAccount).filter(DBAccount.email == createAccount.email).first():
            raise HTTPException(status_code=409, detail="Email already registered")

        user = DBAccount(
            **createAccount.model_dump(exclude={"password"}),
            password=hash_password(createAccount.password),
            created_at=date.today()
        )
        self.db.add(user)
        self.db.flush()
        AuditLogger(self.db, user.id).log("accounts", "CREATE", f"email={user.email}")
        self.db.commit()
        self.db.refresh(user)
        return user


    @router.post(
        "/login",
        response_model=TokenOut,
        summary="Anmelden und JWT-Token erhalten",
        description="""
Authentifiziert einen Benutzer und gibt einen JWT Bearer-Token zurück.

Sende die Daten als `application/x-www-form-urlencoded`:
- `username`: E-Mail-Adresse
- `password`: Passwort

Der Token ist im `Authorization`-Header als `Bearer <token>` zu senden.

**Fehler:**
- `401` – Ungültige E-Mail oder falsches Passwort
""",
    )
    def login(self, form: OAuth2PasswordRequestForm = Depends()):
        user = self.db.query(DBAccount).filter(DBAccount.email == form.username).first()
        if not user or not verify_password(form.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token({"sub": user.email, "role": user.role})
        return {"access_token": token}


    @router.get(
        "/me",
        response_model=AccountOut,
        summary="Eigenes Konto abrufen",
        description="Gibt die Kontodaten des aktuell angemeldeten Benutzers zurück. Erfordert gültigen Bearer-Token.",
    )
    def get_me(self, current_user: DBAccount = Depends(get_current_user)):
        return current_user


    @router.get(
        "/",
        response_model=list[AccountOut],
        summary="Alle Konten abrufen (Manager)",
        description="Gibt eine Liste aller registrierten Benutzerkonten zurück. Nur für Manager zugänglich.",
    )
    def get_accounts(self, _=Depends(require_role(Role.manager))):
        return self.db.query(DBAccount).all()

    @router.get(
        "/{account_id}",
        response_model=AccountOut,
        summary="Konto nach ID abrufen",
        description="""
Gibt das Konto mit der angegebenen ID zurück. Erfordert Authentifizierung.

**Fehler:**
- `404` – Konto nicht gefunden
""",
    )
    def get_account(self, account_id: int, _=Depends(get_current_user)):
        account = self.db.query(DBAccount).filter(DBAccount.id == account_id).first()
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")
        return account

    @router.put(
        "/me",
        response_model=AccountOut,
        summary="Eigenes Profil aktualisieren",
        description="""
Aktualisiert die eigenen Kontodaten. Die Rolle kann nicht selbst geändert werden.

**Wertebereiche:** identisch mit `POST /accounts/register`

**Hinweis:** Ein neues Passwort wird sofort gesetzt.
""",
    )
    def update_me(self, data: AccountCreate, current_user: DBAccount = Depends(get_current_user)):
        for field, value in data.model_dump(exclude={"password", "role"}).items():
            setattr(current_user, field, value)
        current_user.password = hash_password(data.password)
        AuditLogger(self.db, current_user.id).log("accounts", "UPDATE", f"account_id={current_user.id}")
        self.db.commit()
        self.db.refresh(current_user)
        return current_user

    @router.put(
        "/{account_id}",
        response_model=AccountOut,
        summary="Konto bearbeiten (Manager)",
        description="""
Aktualisiert ein beliebiges Konto. Nur für Manager.

**Wertebereiche:** identisch mit `POST /accounts/register`

**Fehler:**
- `404` – Konto nicht gefunden
""",
    )
    def update_account(self, account_id: int, data: AccountCreate, _=Depends(require_role(Role.manager))):
        account = self.db.query(DBAccount).filter(DBAccount.id == account_id).first()
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")

        for field, value in data.model_dump(exclude={"password"}).items():
            setattr(account, field, value)
        account.password = hash_password(data.password)

        AuditLogger(self.db, account.id).log("accounts", "UPDATE", f"account_id={account_id}")
        self.db.commit()
        self.db.refresh(account)
        return account

    @router.delete(
        "/{account_id}",
        status_code=status.HTTP_200_OK,
        summary="Konto löschen (Manager)",
        description="""
Löscht das Konto mit der angegebenen ID. Nur für Manager.

**Fehler:**
- `400` – Manager kann sich nicht selbst löschen
- `404` – Konto nicht gefunden
""",
    )
    def delete_account(self, account_id: int, current_user: DBAccount = Depends(get_current_user), _=Depends(require_role(Role.manager))):
        if current_user.id == account_id:
            raise HTTPException(status_code=400, detail="Managers cannot delete themselves")

        account = self.db.query(DBAccount).filter(DBAccount.id == account_id).first()

        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")

        AuditLogger(self.db, current_user.id).log("accounts", "DELETE", f"account_id={account_id}")
        self.db.delete(account)
        self.db.commit()
        return {"message": "Account successfully deleted", "id": account_id}
