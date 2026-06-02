from fastapi import APIRouter, Depends, HTTPException
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import DBAccount, DBCard, DBTransaction, TransactionStatus
from schemas import TransactionCreate, TransactionResponse
from auth import get_current_user, require_role
from models import Role

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@cbv(router)
class TransactionsAPI:
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[TransactionResponse])
    def get_my_transactions(self, current_user: DBAccount = Depends(get_current_user)):
        card_ids = [c.id for c in self.db.query(DBCard).filter(DBCard.owner_id == current_user.id).all()]

        transactions = self.db.query(DBTransaction).filter((DBTransaction.from_id.in_(card_ids)) | (DBTransaction.to_id.in_(card_ids))).all()
        return transactions

    @router.get("/all", response_model=list[TransactionResponse])
    def get_all_transactions(self, _=Depends(require_role(Role.manager))):
        return self.db.query(DBTransaction).all()

    @router.post("/", response_model=TransactionResponse)
    def create_transaction(self, transactionCreate: TransactionCreate, current_user: DBAccount = Depends(get_current_user)):
        from_card = self.db.query(DBCard).filter(DBCard.id == transactionCreate.from_id).first()
        to_card   = self.db.query(DBCard).filter(DBCard.id == transactionCreate.to_id).first()

        if from_card is None or to_card is None:
            raise HTTPException(status_code=404, detail="Card not found")

        # Only the card owner (or a manager) can send from a card
        if from_card.owner_id != current_user.id and current_user.role != Role.manager:
            raise HTTPException(status_code=403, detail="Not your card")

        if from_card.cents < transactionCreate.amount_cents:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        from_card.cents -= transactionCreate.amount_cents
        to_card.cents += transactionCreate.amount_cents

        new_transaction = DBTransaction(
            from_id=transactionCreate.from_id,
            to_id=transactionCreate.to_id,
            amount_cents=transactionCreate.amount_cents,
            description=transactionCreate.description,
            status=TransactionStatus.Sent,
            created_at=date.today()
        )

        self.db.add(new_transaction)
        self.db.commit()
        self.db.refresh(new_transaction)
        return new_transaction