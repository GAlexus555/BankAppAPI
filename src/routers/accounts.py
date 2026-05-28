from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from typing import Optional

from models import DBAccount
from database import get_db

router = APIRouter(prefix="/items", tags=["Items"])

@cbv(router)
class AccountsAPI():
    db: Session = Depends(get_db)

    @router.get("/")
    def get_accounts(self):
        return self.db.query(DBAccount).all()