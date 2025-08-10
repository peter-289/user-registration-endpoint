from fastapi import Header, HTTPException, status
from app.config import settings

def admin_auth(x_admin_password: str = Header(..., alias="X-Admin-Password")):
    if x_admin_password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
