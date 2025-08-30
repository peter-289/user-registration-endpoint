# seed_admin.py
from sqlalchemy.orm import Session
from database.database_setup import SessionLocal, engine, Base
import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_admin():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    admin_email = "admin@example.com"

    existing = db.query(models.User).filter(models.User.email == admin_email).first()
    if not existing:
        admin = models.User(
            email=admin_email,
            password=pwd_context.hash("AdminPass123"),
            is_admin=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Admin seeded: {admin.email}")
    else:
        print("Admin already exists")

if __name__ == "__main__":
    seed_admin()
