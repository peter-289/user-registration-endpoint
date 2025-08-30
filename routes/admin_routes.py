from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from database.database_setup import get_db
from models.user_model import User
from security_utilities.dependencies import admin_required
from schemas.user_schema import UserResponse



router = APIRouter(prefix="/admin", tags=["Admin"])




@router.get("/users", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db), current_admin: User = Depends(admin_required), skip: int = Query(0), limit: int = Query(10)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/users/{email}")
def get_user_by_email(email: str, db: Session = Depends(get_db), current_admin: User = Depends(admin_required)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/users/{email}")
def delete_user(email: str, db: Session = Depends(get_db), current_admin: User = Depends(admin_required)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User '{email}' deleted successfully"}
