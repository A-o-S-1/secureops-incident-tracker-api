"""Create the first admin interactively; never pass passwords on the command line."""
import getpass
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.security import hash_password

def main():
    username = input("Admin username (3-50 chars): ").strip()
    password = getpass.getpass("Admin password (minimum 12 chars): ")
    confirm = getpass.getpass("Confirm password: ")
    if len(username) < 3 or len(username) > 50 or not username.replace("_","").replace("-","").replace(".","").isalnum():
        raise SystemExit("Invalid username. Use letters, numbers, dot, underscore, or hyphen.")
    if len(password) < 12 or len(password) > 128 or password != confirm:
        raise SystemExit("Passwords must match and be 12-128 characters.")
    db: Session = SessionLocal()
    try:
        if db.query(User).filter(User.role == "admin").count():
            raise SystemExit("An administrator already exists. Use the authenticated admin endpoint to add users.")
        if db.query(User).filter(User.username == username).first():
            raise SystemExit("Username already exists.")
        db.add(User(username=username, password_hash=hash_password(password), role="admin"))
        db.commit()
        print(f"Administrator '{username}' created.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
