from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException
from config import ALGORITHIM, SECRET_KEY, EMAIL_VERIFICATION_TOKEN_EXPIRY

def create_email_token(email: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=EMAIL_VERIFICATION_TOKEN_EXPIRY)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHIM)

def verify_email_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHIM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Verification link expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid verification link")
