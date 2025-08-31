from database.database_setup import Base, SessionLocal, engine
from security_utilities.dependencies import admin_required
from fastapi.middleware.cors import CORSMiddleware
from database.database_setup import SessionLocal
from config import FRONT_END_URL, ADMIN_PASSWORD
from fastapi import FastAPI, Depends
from models.user_model import User, UserRole
from routes.user_registration import router
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from routes import admin_routes
import logging


app=FastAPI()

##Create tables
#print("Sqlalchemy knows about the following tables:",
#Base.metadata.tables.keys())

Base.metadata.create_all(bind=engine)
#Base.metadata.drop_all(bind=engine)

origins = FRONT_END_URL

#CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed the admin user
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def seed_admin():
    db: Session = SessionLocal()
    admin_email = "admin@example.com"

    existing = db.query(User).filter(User.email == admin_email).first()
    if not existing:
        admin = User(
            full_name="Peter",
            user_name="admin",
            email=admin_email,
            password=pwd_context.hash(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            email_verified=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Admin seeded: {admin.email}")
    else:
        print("Admin already exists")
seed_admin()

#routes
@app.get("/")
def root():
    return {"message":"Server is running"}



@app.get("/admin/dashboard")
def admin_dashboard(user=Depends(admin_required)):
    return {"message":f"Welcome Admin {user.full_name}!"}

app.include_router(router)
app.include_router(admin_routes.router)
