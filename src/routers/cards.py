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

    @router.get(
        "/all",
        response_model=list[CardResponse],
        summary="Alle Karten abrufen (Manager)",
        description="Gibt alle Karten aller Benutzer zurück. Nur für Manager zugänglich.",
    )
    def get_all_cards(self, _=Depends(require_role(Role.manager))):
        return self.db.query(DBCard).all()

    @router.get(
        "/",
        response_model=list[CardResponse],
        summary="Eigene Karten abrufen",
        description="Gibt alle Karten des aktuell angemeldeten Benutzers zurück.",
    )
    def get_my_cards(self, current_user: DBAccount = Depends(get_current_user)):
        return self.db.query(DBCard).filter(DBCard.owner_id == current_user.id).all()

    @router.get(
        "/{account_id}",
        response_model=list[CardResponse],
        summary="Karten eines Benutzers abrufen (Manager)",
        description="""
Gibt alle Karten des Benutzers mit der angegebenen Konto-ID zurück. Nur für Manager.

**Fehler:**
- `404` – Kein Benutzer mit dieser ID (leere Liste wenn Karten fehlen)
""",
    )
    def get_cards_from_user(self, account_id: int, _=Depends(require_role(Role.manager))):
        return self.db.query(DBCard).filter(DBCard.owner_id == account_id).all()

    @router.post(
        "/",
        response_model=CardResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Neue Karte erstellen (Manager)",
        description="""
Erstellt eine neue Karte für einen Benutzer. Nur für Manager.

**Wertebereiche:**
- `cents`: Startguthaben in Cent ≥ 0 (z. B. `5000` = 50,00 €)
- `status`: `0` = Active, `1` = Inactive, `2` = Blocked, `3` = Expired
- `owner_id`: ID eines existierenden Benutzers (> 0)
- `iban`: 15–34 Zeichen, Ländercode (2 Buchstaben) + alphanumerisch
- `card_nr`: 13–16 Ziffern, nur Ziffern erlaubt
- `cvc`: 3-stellig (100–999) oder 4-stellig (1000–9999)
- `expire_date`: Format `YYYY-MM-DD`

**Fehler:**
- `404` – Benutzer nicht gefunden
""",
    )
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

    @router.put(
        "/{card_id}",
        response_model=CardResponse,
        summary="Karte aktualisieren (Manager)",
        description="""
Aktualisiert Status und Ablaufdatum einer Karte. Nur für Manager.

**Wertebereiche:**
- `status`: `0` = Active, `1` = Inactive, `2` = Blocked, `3` = Expired
- `expire_date`: Format `YYYY-MM-DD`

**Fehler:**
- `404` – Karte nicht gefunden
""",
    )
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

    @router.delete(
        "/{card_id}",
        status_code=status.HTTP_200_OK,
        summary="Karte löschen (Manager)",
        description="""
Löscht die Karte mit der angegebenen ID. Nur für Manager.

**Fehler:**
- `404` – Karte nicht gefunden
""",
    )
    def delete_card(self, card_id: int, manager: DBAccount = Depends(require_role(Role.manager))):
        card = self.db.query(DBCard).filter(DBCard.id == card_id).first()
        if card is None:
            raise HTTPException(status_code=404, detail="Card not found")

        AuditLogger(self.db, manager.id).log("cards", "DELETE", f"card_id={card_id}")
        self.db.delete(card)
        self.db.commit()
        return {"message": "Card successfully deleted", "id": card_id}
