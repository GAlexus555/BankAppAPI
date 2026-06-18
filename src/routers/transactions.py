from fastapi import APIRouter, Depends, HTTPException
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import DBAccount, DBCard, DBTransaction, TransactionStatus, Role
from schemas import TransactionCreate, TransactionResponse
from auth import get_current_user, require_role
from audit import AuditLogger

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@cbv(router)
class TransactionsAPI:
    db: Session = Depends(get_db)

    @router.get(
        "/",
        response_model=list[TransactionResponse],
        summary="Eigene Transaktionen abrufen",
        description="Gibt alle ein- und ausgehenden Transaktionen des aktuell angemeldeten Benutzers zurück.",
    )
    def get_my_transactions(self, current_user: DBAccount = Depends(get_current_user)):
        card_ids = [c.id for c in self.db.query(DBCard).filter(DBCard.owner_id == current_user.id).all()]
        transactions = self.db.query(DBTransaction).filter(
            (DBTransaction.from_id.in_(card_ids)) | (DBTransaction.to_id.in_(card_ids))
        ).all()
        return transactions

    @router.get(
        "/all",
        response_model=list[TransactionResponse],
        summary="Alle Transaktionen abrufen (Manager)",
        description="Gibt alle Transaktionen im System zurück. Nur für Manager zugänglich.",
    )
    def get_all_transactions(self, _=Depends(require_role(Role.manager))):
        return self.db.query(DBTransaction).all()

    @router.get(
        "/account/{account_id}",
        response_model=list[TransactionResponse],
        summary="Transaktionen eines Benutzers abrufen (Manager)",
        description="""
Gibt alle ein- und ausgehenden Transaktionen des Benutzers mit der angegebenen Konto-ID zurück.
Sortiert nach Datum absteigend. Nur für Manager.

**Fehler:**
- Leere Liste wenn der Benutzer keine Karten oder Transaktionen hat
""",
    )
    def get_transactions_by_account(self, account_id: int, _=Depends(require_role(Role.manager))):
        card_ids = [c.id for c in self.db.query(DBCard).filter(DBCard.owner_id == account_id).all()]
        return (self.db.query(DBTransaction)
                .filter((DBTransaction.from_id.in_(card_ids)) | (DBTransaction.to_id.in_(card_ids)))
                .order_by(DBTransaction.created_at.desc())
                .all())

    @router.post(
        "/",
        response_model=TransactionResponse,
        summary="Überweisung durchführen",
        description="""
Führt eine Überweisung zwischen zwei Karten durch.

**Wertebereiche:**
- `amount_cents`: Betrag in Cent, muss > 0 sein (z. B. `1000` = 10,00 €)
- `iban_from`: IBAN der Absenderkarte (15–34 Zeichen)
- `iban_to`: IBAN der Empfängerkarte (15–34 Zeichen)
- `description`: Verwendungszweck, max. 255 Zeichen

**Voraussetzungen:**
- Beide IBANs müssen im System vorhanden sein
- Die Absenderkarte muss dem angemeldeten Benutzer gehören (außer Manager)
- Ausreichendes Guthaben muss vorhanden sein

**Fehler:**
- `400` – Nicht genug Guthaben auf der Absenderkarte
- `403` – Die Absenderkarte gehört nicht dem angemeldeten Benutzer
- `404` – Karte nicht gefunden
""",
    )
    def create_transaction(self, transactionCreate: TransactionCreate, current_user: DBAccount = Depends(get_current_user)):
        from_card = self.db.query(DBCard).filter(DBCard.iban == transactionCreate.iban_from).first()
        to_card   = self.db.query(DBCard).filter(DBCard.iban == transactionCreate.iban_to).first()

        if from_card is None or to_card is None:
            raise HTTPException(status_code=404, detail="Card not found")

        if from_card.owner_id != current_user.id and current_user.role != Role.manager:
            raise HTTPException(status_code=403, detail="Not your card")

        if from_card.cents < transactionCreate.amount_cents:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        from_card.cents -= transactionCreate.amount_cents
        to_card.cents += transactionCreate.amount_cents

        new_transaction = DBTransaction(
            from_id=from_card.id,
            to_id=to_card.id,
            amount_cents=transactionCreate.amount_cents,
            description=transactionCreate.description,
            status=TransactionStatus.Sent,
            created_at=date.today()
        )

        self.db.add(new_transaction)
        self.db.flush()
        AuditLogger(self.db, current_user.id).log("transactions", "CREATE", f"from={transactionCreate.iban_from}, to={transactionCreate.iban_to}, amount_cents={transactionCreate.amount_cents}")
        self.db.commit()
        self.db.refresh(new_transaction)
        return new_transaction
