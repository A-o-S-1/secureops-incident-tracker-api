"""Insert clearly synthetic demo incidents. Run only in development/demo environments."""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Incident, User
from app.audit import record_audit

DEMO = [
    dict(reference_id="INC-DEMO0001", title="Synthetic phishing report", description="Training scenario: a fictional user reported a suspicious message. No real message or personal data is included.", category="phishing", severity="medium", status="new", source="demo-mail-gateway"),
    dict(reference_id="INC-DEMO0002", title="Synthetic endpoint malware alert", description="Training scenario: a lab endpoint generated a simulated malware alert. No real endpoint identifiers are included.", category="malware", severity="high", status="investigating", source="demo-endpoint-agent"),
    dict(reference_id="INC-DEMO0003", title="Synthetic service availability alert", description="Training scenario: a fictional internal service exceeded a simulated error threshold.", category="availability", severity="low", status="contained", source="demo-monitor"),
]
def main():
    db: Session = SessionLocal()
    try:
        if db.query(Incident).filter(Incident.reference_id.like("INC-DEMO%")).count():
            print("Demo records already exist; no changes made.")
            return
        db.add_all([Incident(**item) for item in DEMO])
        db.commit()
        print(f"Added {len(DEMO)} synthetic incidents.")
    finally:
        db.close()
if __name__ == "__main__":
    main()
