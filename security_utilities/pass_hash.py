import bcrypt
from datetime import datetime, timedelta
import secrets

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


##password resest


async def save_reset_token(user_id, token, expiry):
    # TODO: Implement saving the token and expiry to the database for the user
    pass

async def create_reset_token(user):
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)
    # Save token and expiry to DB associated with user
    await save_reset_token(user.id, token, expiry)
    return token
