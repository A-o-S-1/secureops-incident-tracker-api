from sqlalchemy.orm import Session
from app.models import AuditLog, User

def record_audit(db: Session, actor: User | None, action: str, record_type: str, record_id: str, details: dict | None = None):
    # Callers must pass an allowlisted, non-secret summary. Never pass credentials or tokens.
    entry = AuditLog(
        actor_user_id=actor.id if actor else None,
        actor_username=actor.username if actor else "system",
        action=action,
        record_type=record_type,
        record_id=str(record_id),
        details=details or {},
    )
    db.add(entry)
