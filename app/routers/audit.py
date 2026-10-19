from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_roles
from app.models import AuditLog, User
from app.schemas import AuditOut

router = APIRouter(prefix="/audit-logs", tags=["audit"])

@router.get("", response_model=list[AuditOut])
def list_audit_logs(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), actor: User = Depends(require_roles("admin"))):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).limit(limit).all()
