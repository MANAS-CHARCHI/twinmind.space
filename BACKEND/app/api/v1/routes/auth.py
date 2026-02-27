from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

# Internal imports
from app.db.session import get_db
from app.db.models.user_model import User, RefreshToken
from app.pydentic.user_type import UserCreate, UserLogin
from app.core.config import settings
from app.functions.users.jwt_provider import create_tokens
from app.functions.users.auth_functions import (
    register_user, 
    authenticate_user_manually, 
    get_current_user
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# This is the "Simple Way" for Swagger
security = HTTPBearer()

@router.post("/register")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = await register_user(db, user_data)
    return {"message": "User registered successfully", "user_id": user.id}

@router.post("/login")
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user_manually(db, login_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Ensure your create_tokens returns (access, refresh, expires_at)
    access_token, refresh_token, refresh_expire = create_tokens(user.email)
    
    new_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=refresh_expire
    )
    db.add(new_refresh_token)
    await db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
async def refresh_token_endpoint(refresh_token: str, db: AsyncSession = Depends(get_db)):
    try:
        # 1. Decode refresh token
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        
        # 2. Check DB for token existence (and join with user)
        stmt = select(User).join(RefreshToken).where(
            User.email == email, 
            RefreshToken.token == refresh_token
        )
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # 3. Rotate tokens: Delete old one, create new one
        # Fetch the actual token entry to delete it
        token_stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        token_result = await db.execute(token_stmt)
        old_token = token_result.scalars().first()
        await db.delete(old_token)

        new_access, new_refresh, new_expire = create_tokens(user.email)
        
        db.add(RefreshToken(user_id=user.id, token=new_refresh, expires_at=new_expire))
        await db.commit()
        
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer"
        }
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.post("/logout")    
async def logout(
    refresh_token: str, 
    db: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_user)
):    
    stmt = select(RefreshToken).where(
        RefreshToken.token == refresh_token,
        RefreshToken.user_id == user.id
    )
    result = await db.execute(stmt)
    token_entry = result.scalars().first()
    
    if token_entry:
        await db.delete(token_entry)
        await db.commit()
        return {"message": "Logged out successfully"}
    
    raise HTTPException(status_code=400, detail="Invalid or expired refresh token")

@router.get("/profile")
async def profile(user: User = Depends(get_current_user)):
        
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active
    }