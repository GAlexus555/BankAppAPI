from fastapi import APIRouter, Depends, HTTPException
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import DBAccount, DBCard, DBInterest, DBBank, Role
from schemas import CreateInterest, GetInterest
from auth import get_current_user, require_role
from audit import AuditLogger

router = APIRouter(prefix="/interests", tags=["Interests"])


@cbv(router)
class InterestsAPI:
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[GetInterest])
    def get_my_interests(self, current_user: DBAccount = Depends(get_current_user)):
        card_ids = [c.id for c in self.db.query(DBCard).filter(DBCard.owner_id == current_user.id).all()]
        return self.db.query(DBInterest).filter(DBInterest.card_id.in_(card_ids)).all()

    @router.get("/all", response_model=list[GetInterest])
    def get_all_interests(self, _=Depends(require_role(Role.manager))):
        return self.db.query(DBInterest).all()

    @router.post("/", response_model=GetInterest)
    def create_interest(self, interestCreate: CreateInterest, current_user: DBAccount = Depends(get_current_user)):
        card = self.db.query(DBCard).filter(DBCard.id == interestCreate.card_id).first()
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")

        if card.owner_id != current_user.id and current_user.role != Role.manager:
            raise HTTPException(status_code=403, detail="Not your card")

        if card.cents < interestCreate.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        card.cents -= interestCreate.amount
        interest_rate_db = self.db.query(DBBank).first().interest_rate
        if interest_rate_db is None:
            raise  HTTPException(status_code=400, detail="At the time, no banks support this feature")

        new_interest = DBInterest(
            created_at=date.today(),
            withdrawn=False,
            interest_rate = interest_rate_db,
            amount = interestCreate.amount,
            card_id = card.id,
        )

        self.db.add(new_interest)
        AuditLogger(self.db, current_user.id).log("interests", "CREATE", f"amount={interestCreate.amount}, card_id={card.id}")
        self.db.commit()
        self.db.refresh(new_interest)
        return new_interest

    @router.post("/{interest_id}/withdraw", response_model=GetInterest)
    def withdraw_interest(self, interest_id: int, current_user: DBAccount = Depends(get_current_user)):
        interest = self.db.query(DBInterest).filter(DBInterest.id == interest_id).first()
        if interest is None:
            raise HTTPException(status_code=404, detail="Interest not found")

        card = self.db.query(DBCard).filter(DBCard.id == interest.card_id).first()
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")

        if card.owner_id != current_user.id and current_user.role != Role.manager:
            raise HTTPException(status_code=403, detail="Not your interest")

        if interest.withdrawn:
            raise HTTPException(status_code=400, detail="Already withdrawn")

        years = (date.today() - interest.created_at.date()).days / 365.25
        payout = int(interest.amount * ((1 + interest.interest_rate) ** years))

        card.cents += payout
        interest.withdrawn = True

        AuditLogger(self.db, current_user.id).log("interests", "WITHDRAW", f"interest_id={interest.id}, payout={payout}")
        self.db.commit()
        self.db.refresh(interest)
        return interest