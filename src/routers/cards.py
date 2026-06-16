from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import DBAccount, DBCard, Role
from schemas import CardBase, CardCreate, CardResponse, CardUpdate
from auth import get_current_user, require_role
from audit import AuditLogger

router = APIRouter(prefix="/cards", tags=["Cards"])


@cbv(router)
class CardsAPI():
    db: Session = Depends(get_db)

    @router.get("/all", response_model=list[CardResponse])
    def get_all_cards(self, _=Depends(require_role(Role.manager))):
        return self.db.query(DBCard).all()

    @router.get("/", response_model=list[CardResponse])
    def get_my_cards(self, current_user: DBAccount = Depends(get_current_user)):
        return self.db.query(DBCard).filter(DBCard.owner_id == current_user.id).all()

    @router.get("/{account_id}", response_model=list[CardResponse])
    def get_cards_from_user(self, account_id: int, _=Depends(require_role(Role.manager))):
        return self.db.query(DBCard).filter(DBCard.owner_id == account_id).all()

    @router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
    def add_card_to_user(self, cardCreate: CardCreate, manager: DBAccount = Depends(require_role(Role.manager))):
        user = self.db.query(DBAccount).filter(DBAccount.id == cardCreate.owner_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        card = DBCard(**cardCreate.model_dump(exclude={"owner_id"}),
                      owner_id=user.id,
                      created_at=date.today())

        self.db.add(card)
        self.db.flush()
        AuditLogger(self.db, manager.id).log("cards", "CREATE", f"card_id={card.id}, owner_id={user.id}")
        self.db.commit()
        self.db.refresh(card)
        return card

    @router.put("/{card_id}", response_model=CardResponse)
    def update_card(self, card_id: int, data: CardUpdate, manager: DBAccount = Depends(require_role(Role.manager))):
        card = self.db.query(DBCard).filter(DBCard.id == card_id).first()
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")

        card.status = data.status
        card.expire_date = data.expire_date

        AuditLogger(self.db, manager.id).log("cards", "UPDATE", f"card_id={card_id}, status={data.status}")
        self.db.commit()
        self.db.refresh(card)
        return card

    @router.delete("/{card_id}", status_code=status.HTTP_200_OK)
    def delete_card(self, card_id: int, manager: DBAccount = Depends(require_role(Role.manager))):
        card = self.db.query(DBCard).filter(DBCard.id == card_id).first()
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")

        AuditLogger(self.db, manager.id).log("cards", "DELETE", f"card_id={card_id}")
        self.db.delete(card)
        self.db.commit()
        return {"message": "Card successfully deleted", "id": card_id}
