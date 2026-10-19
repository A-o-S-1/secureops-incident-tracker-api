from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated

Category = Literal["malware", "phishing", "unauthorized_access", "data_exposure", "availability", "policy_violation", "other"]
Severity = Literal["low", "medium", "high", "critical"]
Status = Literal["new", "investigating", "contained", "resolved", "closed"]
Username = Annotated[str, StringConstraints(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")]

class UserCreate(BaseModel):
    username: Username
    password: Annotated[str, Field(min_length=12, max_length=128)]
    role: Literal["analyst", "admin"] = "analyst"

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=5, max_length=10000)
    category: Category
    severity: Severity
    source: str = Field(min_length=2, max_length=100)
    assigned_to_id: int | None = None

class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, min_length=5, max_length=10000)
    category: Category | None = None
    severity: Severity | None = None
    source: str | None = Field(default=None, min_length=2, max_length=100)
    assigned_to_id: int | None = None
    resolution_notes: str | None = Field(default=None, max_length=10000)

class StatusUpdate(BaseModel):
    status: Status
    resolution_notes: str | None = Field(default=None, max_length=10000)

class IncidentOut(BaseModel):
    id: int
    reference_id: str
    title: str
    description: str
    category: str
    severity: str
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
    assigned_to_id: int | None
    resolution_notes: str | None
    model_config = ConfigDict(from_attributes=True)

class IncidentPage(BaseModel):
    items: list[IncidentOut]
    total: int
    page: int
    page_size: int

class AuditOut(BaseModel):
    id: int
    actor_user_id: int | None
    actor_username: str
    action: str
    record_type: str
    record_id: str
    timestamp: datetime
    details: dict
    model_config = ConfigDict(from_attributes=True)
