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

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@cbv(router)
class AccountsAPI():
    db: Session = Depends(get_db)
    get_user: DBAccount = Depends(get_current_user)


    @router.post("/register", response_model=AccountOut, status_code=201)
    def register(self, createAccount: AccountCreate):
        if self.db.query(DBAccount).filter(DBAccount.email == createAccount.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = DBAccount(
            **createAccount.model_dump(exclude={"password"}),
            password=hash_password(createAccount.password),
            created_at=date.today()
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

    @router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_account(self,account_id: int, current_user: DBAccount = Depends(get_current_user), _=Depends(require_role(Role.manager))):
        if current_user.id == account_id:
            raise HTTPException(status_code=400, detail="Managers cannot delete themselves")

        account = self.db.query(DBAccount).filter(DBAccount.id == account_id).first()

        if account is None:
            raise HTTPException(status_code=404, detail="Account not found")

        self.db.delete(account)
        self.db.commit()