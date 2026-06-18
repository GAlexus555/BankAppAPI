from fastapi import APIRouter, Depends
from fastapi_restful.cbv import cbv
from sqlalchemy.orm import Session

from database import get_db
from models import DBAuiditLog, Role
from schemas import GetAuditLog
from auth import require_role

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@cbv(router)
class AuditLogAPI:
    db: Session = Depends(get_db)

    @router.get(
        "/",
        response_model=list[GetAuditLog],
        summary="Alle Audit-Logs abrufen (Manager)",
        description="""
Gibt alle Audit-Log-Einträge zurück, sortiert nach Zeitpunkt absteigend.
Nur für Manager zugänglich.

Jeder Eintrag protokolliert eine Datenbankänderung (CREATE, UPDATE, DELETE, WITHDRAW).

**Antwortfelder:**
- `id`: Log-ID
- `account_id`: ID des ausführenden Benutzers
- `timestamp`: Zeitpunkt der Aktion (UTC)
- `tablename`: Betroffene Tabelle (z. B. `accounts`, `cards`, `transactions`, `interests`)
- `action`: Durchgeführte Aktion
- `details`: Optionale Zusatzinformationen (z. B. `email=max@example.com`)
""",
    )
    def get_all_logs(self, _=Depends(require_role(Role.manager))):
        return self.db.query(DBAuiditLog).order_by(DBAuiditLog.timestamp.desc()).all()

    @router.get(
        "/{account_id}",
        response_model=list[GetAuditLog],
        summary="Audit-Logs eines Benutzers abrufen (Manager)",
        description="""
Gibt alle Audit-Log-Einträge eines bestimmten Benutzers zurück, sortiert nach Zeitpunkt absteigend.
Nur für Manager zugänglich.

**Fehler:**
- Leere Liste wenn keine Logs für diesen Benutzer vorhanden
""",
    )
    def get_logs_by_account(self, account_id: int, _=Depends(require_role(Role.manager))):
        return self.db.query(DBAuiditLog).filter(DBAuiditLog.account_id == account_id).order_by(DBAuiditLog.timestamp.desc()).all()
