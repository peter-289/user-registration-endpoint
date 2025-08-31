from dotenv import load_dotenv
import os
from slowapi import Limiter
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from limits.storage import RedisStorage
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from fastapi_mail import ConnectionConfig

load_dotenv()

##Env variables
DATABASE_URL= os.getenv("DATABASE_URL")
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHIM=os.getenv("ALGORITHM")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD")
FRONT_END_URL=os.getenv("FRONTEND_URL")
REDIS_STORAGE=os.getenv("REDIS_STORAGE","memory://")
REFRESH_TOKEN_EXPIRE_DAYS=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS",30))
EMAIL_VERIFICATION_TOKEN=int(os.getenv("EMAIL_VERIFICATION_TOKEN",30))
EMAIL_VERIFICATION_TOKEN_EXPIRY=int(os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRY",30))


if DATABASE_URL:
    print(f"Database url loaded:{DATABASE_URL}")
else:
    print("Database url not loaded")

if ALGORITHIM:
    print("Algorithim loaded")
else:
    print("Algorithim not loaded")
if SECRET_KEY:
    print("key loaded")
else:
    print("key not loaded")
if ACCESS_TOKEN_EXPIRE_MINUTES:
    print("Token expiry time loaded")
else:
    print("Token expiry time not loaded")




##Rate limiter
limiter=Limiter(
    key_func = lambda request: request.client.host,
    storage_uri="memory://"
)





app = FastAPI()
app.state.limiter = limiter

#Rate limiter
#Custom JSON handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "retry_after": exc.detail,
            "path": request.url.path
        },
    )


##Email configurations

mail_config = ConnectionConfig(
    MAIL_USERNAME="",
    MAIL_PASSWORD="",
    MAIL_FROM="tech_pulse@gmail.com",  # any fake address works
    MAIL_PORT=1025,
    MAIL_SERVER="127.0.0.1",
    MAIL_STARTTLS=False,   # make sure this is False
    MAIL_SSL_TLS=False,    # and this is False too
    USE_CREDENTIALS=False, # No login
    VALIDATE_CERTS=False 
)
