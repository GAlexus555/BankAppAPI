from fastapi import APIRouter, Depends, HTTPException
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import DBBank, DBAccount, Role
from schemas import CreateBank, GetBank
from auth import get_current_user, require_role

router = APIRouter(prefix="/banks", tags=["Banks"])


@cbv(router)
class BankssAPI:
    db: Session = Depends(get_db)

    @router.get("/", response_model=GetBank)
    def get_banks(self):
        bank = self.db.query(DBBank).first()
        if bank is None:
            raise HTTPException(status_code=404, detail="No bank found")
        return bank

    @router.post("/", response_model=GetBank)
    def create_bank(self, bankCreate: CreateBank, _=Depends(require_role(Role.manager))):
        new_bank = DBBank(
            bankname = bankCreate.bankname,
            interest_rate = bankCreate.interest_rate
        )
        self.db.add(new_bank)
        self.db.commit()
        self.db.refresh(new_bank)
        return new_bank