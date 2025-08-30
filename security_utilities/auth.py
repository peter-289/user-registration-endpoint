import jwt
from datetime import datetime, timedelta, timezone
from config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES,ALGORITHIM

def create_access_token(data:dict):
   to_encode= data.copy()
   expire= datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
   to_encode.update({"exp":expire})
   encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHIM)
   return encoded_jwt