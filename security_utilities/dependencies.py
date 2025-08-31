import jwt
from sqlalchemy.orm import Session
from jwt.exceptions import PyJWTError
from config import SECRET_KEY, ALGORITHIM, REFRESH_TOKEN_EXPIRE_DAYS
from database.database_setup import get_db
from fastapi import Depends, HTTPException, Request
from models.user_model import User, UserRole
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timezone, timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


def get_current_user(request:Request,token:str = Depends(oauth2_scheme),db:Session=Depends(get_db)):
    token=request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token!")
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHIM])
        email:str=payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="invalid token payload")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token!")

    user=db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    return user

def admin_required(current_user:User=Depends(get_current_user)):
    if not current_user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required!")
    return current_user


def create_refresh_token(data: dict):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": data["sub"], "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHIM)

