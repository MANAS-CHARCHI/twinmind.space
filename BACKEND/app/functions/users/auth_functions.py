from fastapi.params import Depends
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user_model import User
from pydantic import BaseModel
from passlib.context import CryptContext
from app.pydentic.user_type import UserCreate, UserLogin
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
async def register_user(db: Session, user: UserCreate):
    new_user = User(
        email=user.email,
        hashed_password=pwd_context.hash(user.password.encode("utf-8")[:72]),
        username=user.username,
        full_name=user.full_name
    )
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        await db.rollback()
        raise e

async def authenticate_user_manually(db: Session, user: UserLogin):
    stmt=select(User).where(User.email == user.email)
    result= await db.execute(stmt)
    db_user = result.scalars().first()
    if not db_user:
        return None
    if not db_user.verify_password(user.password[:72]):
        return None
    return db_user

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security), 
    db: AsyncSession = Depends(get_db)
):
    # The token is automatically extracted from the "Bearer <token>" header
    token = auth.credentials 
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Fetch user from DB
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user