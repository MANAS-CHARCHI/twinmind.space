import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
REFRESH_SECRET_KEY = settings.REFRESH_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_tokens(user_email: str):
    # 1. Create Access Token
    access_expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({"sub": user_email, "exp": access_expire}, SECRET_KEY, algorithm=ALGORITHM)
    
    # 2. Create Refresh Token
    refresh_expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = jwt.encode({"sub": user_email, "exp": refresh_expire}, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    
    return access_token, refresh_token, refresh_expire