import datetime
import jwt as pwjt
from config import limiter
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from models.user_model import User
from passlib.context import CryptContext
from datetime import timedelta, timezone
from database.database_setup import get_db
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from security_utilities.auth import create_access_token
from security_utilities.dependencies import get_current_user
from schemas.user_schema import UserCreate, UserResponse
from security_utilities.pass_hash import hash_password, verify_password



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/users")



@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")
async def register_user(request:Request, user: UserCreate, db: Session = Depends(get_db)):
    #Existing user
    existing_user = db.query(User).filter(User.email == user.email).first()
    user_name_exists=db.query(User).filter(User.user_name == user.user_name).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    elif user_name_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Username {user.user_name} exists, choose another one!"
        )
    # Hash the password
    hashed_password = hash_password(user.password)
    

    new_user = User(
         full_name =user.full_name,
         user_name =user.user_name,
         email =user.email,
         password = hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


##Login route
@router.post("/login")
@limiter.limit("4/minute")
def login(request:Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_name == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_data = {
        "sub": user.email,
        "role": user.role.value,
        "exp": datetime.datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = create_access_token(token_data)
    return {
        "access_token": token,
        "token_type": "bearer"
    }

