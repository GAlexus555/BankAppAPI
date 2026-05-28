from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from datetime import date

from src.database import get_db
from src.models import DBAccount, Role
from src.schemas import AccountCreate, AccountOut, TokenOut
from src.auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, require_role
)

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@cbv(router)
class AccountsAPI():
    db: Session = Depends(get_db)


    @router.post("/register", response_model=AccountOut, status_code=201)
    def register(self, payload: AccountCreate):
        if self.db.query(DBAccount).filter(DBAccount.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = DBAccount(
            **payload.model_dump(exclude={"password"}),
            password=hash_password(payload.password),
            createdat=date.today()
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


    @router.post("/login", response_model=TokenOut)
    def login(self, form: OAuth2PasswordRequestForm = Depends()):
        user = self.db.query(DBAccount).filter(DBAccount.email == form.username).first()
        if not user or not verify_password(form.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token({"sub": user.email, "role": user.role})
        return {"access_token": token}


    @router.get("/me", response_model=AccountOut)
    def get_me(self, current_user: DBAccount = Depends(get_current_user)):
        return current_user


    @router.get("/", response_model=list[AccountOut])
    def get_accounts(self, _=Depends(require_role(Role.manager))):
        return self.db.query(DBAccount).all()