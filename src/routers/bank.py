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

    @router.get(
        "/",
        response_model=GetBank,
        summary="Bankdaten abrufen",
        description="""
Gibt die Daten der konfigurierten Bank zurück (es gibt genau eine Bank im System).

**Fehler:**
- `404` – Noch keine Bank angelegt
""",
    )
    def get_banks(self):
        bank = self.db.query(DBBank).first()
        if bank is None:
            raise HTTPException(status_code=404, detail="No bank found")
        return bank

    @router.post(
        "/",
        response_model=GetBank,
        summary="Bank anlegen (Manager)",
        description="""
Legt eine neue Bank mit Zinssatz an. Nur für Manager.

**Wertebereiche:**
- `bankname`: 1–100 Zeichen
- `interest_rate`: Jahreszinssatz als Dezimalzahl, 0 < Wert ≤ 1 (z. B. `0.035` = 3,5 %)
""",
    )
    def create_bank(self, bankCreate: CreateBank, _=Depends(require_role(Role.manager))):
        new_bank = DBBank(
            bankname=bankCreate.bankname,
            interest_rate=bankCreate.interest_rate
        )
        self.db.add(new_bank)
        self.db.commit()
        self.db.refresh(new_bank)
        return new_bank

    @router.put(
        "/{bank_id}",
        response_model=GetBank,
        summary="Bank aktualisieren (Manager)",
        description="""
Aktualisiert Name und Zinssatz der Bank mit der angegebenen ID. Nur für Manager.

**Wertebereiche:**
- `bankname`: 1–100 Zeichen
- `interest_rate`: Jahreszinssatz als Dezimalzahl, 0 < Wert ≤ 1 (z. B. `0.035` = 3,5 %)

**Fehler:**
- `404` – Bank nicht gefunden
""",
    )
    def update_bank(self, bank_id: int, data: CreateBank, _=Depends(require_role(Role.manager))):
        bank = self.db.query(DBBank).filter(DBBank.id == bank_id).first()
        if bank is None:
            raise HTTPException(status_code=404, detail="Bank not found")
        bank.bankname = data.bankname
        bank.interest_rate = data.interest_rate
        self.db.commit()
        self.db.refresh(bank)
        return bank
