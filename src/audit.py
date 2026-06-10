from sqlalchemy.orm import Session
from models import DBAuiditLog


class AuditLogger:
    def __init__(self, db: Session, account_id: int):
        self.db = db
        self.account_id = account_id

    def log(self, tablename: str, action: str, details: str = None):
        entry = DBAuiditLog(
            account_id=self.account_id,
            tablename=tablename,
            action=action,
            details=details
        )
        self.db.add(entry)
        self.db.commit()