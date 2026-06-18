# KI-Anfang
# KI: Claude
# prompt: FastAPI Aggregationsendpunkt mit GROUP BY und JOIN über accounts, cards und transactions
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

    @router.get(
        "/transactions-per-account",
        response_model=list[TransactionStats],
        summary="Transaktionsstatistik pro Konto (Manager)",
        description="""
Gibt für jeden Benutzer die Anzahl und das Gesamtvolumen aller ausgehenden Transaktionen zurück.
Nützlich für die Darstellung in Diagrammen und Ranglisten. Nur für Manager zugänglich.

**Antwortfelder:**
- `account_id`: Benutzer-ID
- `firstname`, `lastname`: Name des Benutzers
- `transaction_count`: Anzahl ausgehender Transaktionen
- `total_cents`: Gesamtvolumen in Cent (z. B. `15000` = 150,00 €)
""",
    )
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
# KI-Ende
