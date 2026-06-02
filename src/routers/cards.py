from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import DBAccount, DBCard, Role
from schemas import CardBase, CardCreate, CardResponse
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, require_role
)

router = APIRouter(prefix="/cards", tags=["Cards"])


@cbv(router)
class CardsAPI():
    db: Session = Depends(get_db)

    @router.get("/", response_model=list[CardResponse])
    def get_my_cards(self, DBAccount=Depends(get_current_user)):
        user_id = DBAccount.id
        cards = self.db.query(DBCard).filter(DBCard.owner_id == user_id).all()
        return cards

    @router.get("/all", response_model=list[CardResponse])
    def get_all_cards(self, _=Depends(require_role(Role.manager))):
        cards = self.db.query(DBCard).all()
        return cards

    @router.post("/", response_model=CardResponse)
    def add_card_to_user(self, cardCreate: CardCreate, _=Depends(require_role(Role.manager))):
        user = self.db.query(DBAccount).filter(DBAccount.id == cardCreate.owner_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        card = DBCard(**cardCreate.model_dump(exclude={"owner_id"}),
                      owner_id=user.id,
                      created_at=date.today())

        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return card

    @router.delete("/", response_model=CardResponse)
    def delete_card(self, card_id: int, _=Depends(require_role(Role.manager))):
        card = self.db.query(DBCard).filter(DBCard.id == card_id).first()
        if card is None:
            raise HTTPException(status_code=404, detail="User not found")

        self.db.delete(card)
        self.db.commit()
        return card
