from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.audit import record_audit
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import Incident, User
from app.schemas import IncidentCreate, IncidentUpdate, IncidentOut, IncidentPage, StatusUpdate

router = APIRouter(prefix="/incidents", tags=["incidents"])
TRANSITIONS = {
    "new": {"investigating"},
    "investigating": {"contained", "resolved"},
    "contained": {"investigating", "resolved"},
    "resolved": {"closed", "investigating"},
    "closed": set(),
}

def check_assignee(db: Session, assigned_to_id: int | None):
    if assigned_to_id is None:
        return
    user = db.get(User, assigned_to_id)
    if not user or not user.is_active or user.role not in {"analyst", "admin"}:
        raise HTTPException(status_code=422, detail="Assignee must be an active analyst or administrator")

@router.post("", response_model=IncidentOut, status_code=201)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    check_assignee(db, payload.assigned_to_id)
    data = payload.model_dump()
    incident = Incident(reference_id=f"INC-{uuid4().hex[:10].upper()}", **data)
    db.add(incident)
    db.flush()
    record_audit(db, actor, "incident.created", "incident", incident.reference_id, {"severity": incident.severity, "category": incident.category, "status": incident.status})
    db.commit()
    db.refresh(incident)
    return incident

@router.get("", response_model=IncidentPage)
def list_incidents(
    q: str | None = Query(default=None, max_length=160),
    severity: str | None = Query(default=None, pattern="^(low|medium|high|critical)$"),
    status_filter: str | None = Query(default=None, alias="status", pattern="^(new|investigating|contained|resolved|closed)$"),
    category: str | None = Query(default=None, pattern="^(malware|phishing|unauthorized_access|data_exposure|availability|policy_violation|other)$"),
    page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db), actor: User = Depends(get_current_user),
):
    query = db.query(Incident)
    if q:
        term = f"%{q}%"
        query = query.filter(or_(Incident.title.ilike(term), Incident.description.ilike(term), Incident.reference_id.ilike(term), Incident.source.ilike(term)))
    if severity: query = query.filter(Incident.severity == severity)
    if status_filter: query = query.filter(Incident.status == status_filter)
    if category: query = query.filter(Incident.category == category)
    total = query.count()
    items = query.order_by(Incident.created_at.desc(), Incident.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.get("/{reference_id}", response_model=IncidentOut)
def get_incident(reference_id: str, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    incident = db.query(Incident).filter(Incident.reference_id == reference_id).first()
    if not incident: raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.patch("/{reference_id}", response_model=IncidentOut)
def update_incident(reference_id: str, payload: IncidentUpdate, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    incident = db.query(Incident).filter(Incident.reference_id == reference_id).first()
    if not incident: raise HTTPException(status_code=404, detail="Incident not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes: raise HTTPException(status_code=400, detail="No changes supplied")
    if "assigned_to_id" in changes: check_assignee(db, changes["assigned_to_id"])
    # Closed incidents are immutable except through a future audited admin workflow.
    if incident.status == "closed" and actor.role != "admin":
        raise HTTPException(status_code=403, detail="Closed incidents can only be modified by administrators")
    safe_changes = {}
    for key, value in changes.items():
        setattr(incident, key, value)
        safe_changes[key] = value if key != "description" and key != "resolution_notes" else "[updated]"
    record_audit(db, actor, "incident.updated", "incident", incident.reference_id, {"changed_fields": sorted(changes), "changes": safe_changes})
    db.commit()
    db.refresh(incident)
    return incident

@router.patch("/{reference_id}/status", response_model=IncidentOut)
def update_status(reference_id: str, payload: StatusUpdate, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    incident = db.query(Incident).filter(Incident.reference_id == reference_id).first()
    if not incident: raise HTTPException(status_code=404, detail="Incident not found")
    if payload.status == incident.status:
        raise HTTPException(status_code=400, detail="Incident is already in that status")
    if payload.status not in TRANSITIONS[incident.status]:
        raise HTTPException(status_code=409, detail=f"Invalid status transition: {incident.status} -> {payload.status}")
    if payload.status == "closed" and actor.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators may close incidents")
    if payload.status == "resolved" and not (payload.resolution_notes or incident.resolution_notes):
        raise HTTPException(status_code=422, detail="Resolution notes are required before resolving")
    old = incident.status
    incident.status = payload.status
    if payload.resolution_notes is not None: incident.resolution_notes = payload.resolution_notes
    record_audit(db, actor, "incident.status_changed", "incident", incident.reference_id, {"from": old, "to": incident.status})
    db.commit()
    db.refresh(incident)
    return incident

@router.delete("/{reference_id}", status_code=204)
def delete_incident(reference_id: str, db: Session = Depends(get_db), actor: User = Depends(require_roles("admin"))):
    incident = db.query(Incident).filter(Incident.reference_id == reference_id).first()
    if not incident: raise HTTPException(status_code=404, detail="Incident not found")
    record_audit(db, actor, "incident.deleted", "incident", incident.reference_id, {"severity": incident.severity, "status": incident.status})
    db.delete(incident)
    db.commit()
    return None
