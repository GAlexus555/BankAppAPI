from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import DBAccount, DBCard, DBTransaction, Role
from schemas import TransactionStats
from auth import require_role

router = APIRouter(prefix="/stats", tags=["Stats"])


@cbv(router)
class StatsAPI:
    db: Session = Depends(get_db)

    @router.get("/transactions-per-account", response_model=list[TransactionStats])
    def get_transactions_per_account(self, _=Depends(require_role(Role.manager))):
        rows = (
            self.db.query(
                DBAccount.id.label("account_id"),
                DBAccount.firstname,
                DBAccount.lastname,
                func.count(DBTransaction.id).label("transaction_count"),
                func.coalesce(func.sum(DBTransaction.amount_cents), 0).label("total_cents"),
            )
            .outerjoin(DBCard, DBCard.owner_id == DBAccount.id)
            .outerjoin(DBTransaction, DBTransaction.from_id == DBCard.id)
            .group_by(DBAccount.id)
            .all()
        )
        return [
            TransactionStats(
                account_id=row.account_id,
                firstname=row.firstname,
                lastname=row.lastname,
                transaction_count=row.transaction_count,
                total_cents=row.total_cents,
            )
            for row in rows
        ]
