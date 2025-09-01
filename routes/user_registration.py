import secrets
import datetime as dt
import jwt as pwjt
from urllib3 import request
from config import limiter
from fastapi import  BackgroundTasks,APIRouter, Request, Response
from sqlalchemy.orm import Session
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY, ALGORITHIM
from models.user_model import User
from passlib.context import CryptContext
from datetime import timedelta, timezone
from database.database_setup import get_db
from fastapi import HTTPException, status, Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from security_utilities.auth import create_access_token
from security_utilities.dependencies import create_refresh_token, get_current_user
from schemas.user_schema import UserCreate
from security_utilities.pass_hash import hash_password, verify_password
from security_utilities.email_verification import create_email_token
from services.email_service import send_verification_email, send_reset_email
from security_utilities.email_verification import verify_email_token
from fastapi_mail import FastMail, MessageSchema
from config import mail_config
from passlib.hash import bcrypt
from fastapi import Form
import fastapi.templating as Jinja

templates = Jinja.Jinja2Templates(directory="templates/email_templates")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/users")


##Registration endpoint
@router.post("/register")
@limiter.limit("5/minute")
async def register_user(
    request:Request,
    user: UserCreate, 
    background_tasks:BackgroundTasks,
    db: Session = Depends(get_db)):

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
         password = hashed_password,
         email_verified = False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_email_token(new_user.email)
    background_tasks.add_task(send_verification_email, new_user.email, token)

    return {
        "message": "User registered successfully! Please check your email to verify your account.",
        
    }


##Login route
@router.post("/login")
@limiter.limit("4/minute")
def login(request:Request, response:Response,form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_name == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if not user.email_verified:
        raise HTTPException(
            status_code=401,
            detail="Email not verified, please verify your email first!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_data = {
        "sub": user.email,
        "role": user.role.value,
        "exp": dt.datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,       
        secure=True,         
        samesite="Strict",  
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
         httponly=True,       
        secure=True,         
        samesite="Strict",  
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    return {
       "message":"Login successfull!"
    }


##User profile
@router.get("/my-profile")
def get_my_profile(current_user: User= Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.user_name,
        "email": current_user.email,
        "role": current_user.role.value
    }

##User Logout
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,      # same flags as login
        samesite="Strict"
    )
    return {"message": "Logged out successfully"}


##Token refresh
@router.post("/refresh")
def refresh_token(response: Response, refresh_token: str = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    try:
        payload = pwjt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHIM])
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except pwjt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except pwjt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # create new access token
    new_access_token = create_access_token({"sub": user_email})
    response.set_cookie(
        "access_token", 
        new_access_token, 
        httponly=True, 
        secure=True,
        samesite="Strict"
    )

    return {"message": "Token refreshed"}


##email verification
@router.get("/verify")
def verify_account(token: str, db: Session = Depends(get_db)):
    email = verify_email_token(token)
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email_verified:
        return {"message": "Account already verified"}

    user.email_verified = True
    db.commit()
    return {"message": "Account verified successfully"}

##Resend verification
@router.get("/resend-verification")
async def resend_verification(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user and not user.email_verified:
        token = create_email_token(user)
        await send_verification_email(user.email, token)
        return {"message": "Verification email resent!"}
    return {"message": "User already verified or not found."}


##reset password
@router.post("/forgot-password")
def forgot_password(request: Request, background_tasks: BackgroundTasks, email: str=Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"message": "User not found."}

    token = secrets.token_urlsafe(3)
    expiry = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
    user.password_reset_token = token
    user.password_reset_token_expiry = expiry
    db.commit()

    background_tasks.add_task(send_reset_email, user.email, token)  # send email with reset link
    return templates.TemplateResponse(
        "reset_password_request.html",
        {"request": request, "message": "Password reset email sent if the email is registered."}
    )

    
##Reset password form
@router.get("/reset-password")
def reset_password_form(request: Request, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.password_reset_token == token).first()
    if not user:
        return templates.TemplateResponse(
            "reset_password_request.html",
            {"request": request, "error": "Invalid or expired token"}
        )

    # Render the reset form
    return templates.TemplateResponse(
        "reset_password_form.html",
        {"request": request, "token": token}  # token goes into hidden input
    )

##Reset Password
@router.post("/reset-password")
def reset_password_post(request: Request, token: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(get_db)):
    # Step 1: Validate token
    user = db.query(User).filter(User.password_reset_token == token).first()
    if not user:
        return templates.TemplateResponse("reset_password_request.html", {"request": request, "valid_token": False})

    # Step 2: Check password match
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "reset_password_request.html",
            {"request": request, "valid_token": True, "error": "Passwords do not match"}
        )
    # Step 3: Hash new password
    
    hashed_password = bcrypt.hash(new_password)

    # Step 4: Update user password in DB
    update_user_password(user.id, hashed_password, db)

    # Step 5: Invalidate token
    invalidate_token(token, db)

    return templates.TemplateResponse(
        "password_reset_success.html",
        {"request": request, "valid_token": True}
    )
    # Step 6: Show success page or redirect to login
  

async def update_user_password(user_id: int, hashed_password: str, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.password = hashed_password
        user.password_reset_token = None
        user.password_reset_token_expiry = None
        db.commit()

async def invalidate_token(token: str, db: Session):
    user = db.query(User).filter(User.password_reset_token == token).first()
    if user:
        user.password_reset_token = None
        user.password_reset_token_expiry = None
        db.commit()


##Testmail
@router.get("/test-email")
async def test_email():
    message = MessageSchema(
        subject="Hello from Tech Pulse 🚀",
        recipients=["test@receiver.com"],  # Doesn’t matter, MailHog catches everything
        body="<h3>This is a test email from FastAPI-Mail ✅</h3>",
        subtype="html"
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)