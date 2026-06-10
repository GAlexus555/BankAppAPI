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

    @router.get("/", response_model=list[GetAuditLog])
    def get_all_logs(self, _=Depends(require_role(Role.manager))):
        return self.db.query(DBAuiditLog).order_by(DBAuiditLog.timestamp.desc()).all()

    @router.get("/{account_id}", response_model=list[GetAuditLog])
    def get_logs_by_account(self, account_id: int, _=Depends(require_role(Role.manager))):
        return self.db.query(DBAuiditLog).filter(DBAuiditLog.account_id == account_id).order_by(DBAuiditLog.timestamp.desc()).all()