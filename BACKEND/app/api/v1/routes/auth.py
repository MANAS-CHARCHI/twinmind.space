import urllib.parse
import jwt
import requests
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import BackgroundTasks
from app.functions.emails.process_email_to_vector import scan_user_emails
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

router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer()

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

# --- STANDARD AUTH ENDPOINTS ---

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token, refresh_token, refresh_expire = create_tokens(user.email)
    new_refresh_token = RefreshToken(user_id=user.id, token=refresh_token, expires_at=refresh_expire)
    db.add(new_refresh_token)
    await db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh")
async def refresh_token_endpoint(refresh_token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        stmt = select(User).join(RefreshToken).where(User.email == email, RefreshToken.token == refresh_token)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        token_stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        token_result = await db.execute(token_stmt)
        await db.delete(token_result.scalars().first())

        new_access, new_refresh, new_expire = create_tokens(user.email)
        db.add(RefreshToken(user_id=user.id, token=new_refresh, expires_at=new_expire))
        await db.commit()
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# --- GOOGLE OAUTH ENDPOINTS ---

@router.get("/login/google") # Changed to GET so you can visit it in browser
async def google_login():
    """
    Manually builds the URL to avoid the PKCE 'code_verifier' requirement 
    imposed by the google-auth-oauthlib library.
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent", # Forces refresh_token every time during testing
    }
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return {"url": auth_url}

@router.get("/callback/google")
async def google_callback(request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")

    # 1. Exchange the code for tokens manually using requests
    # By providing client_secret and NOT using Flow, we solve the 'Missing code verifier' error.
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    response = requests.post(token_url, data=data, timeout=10)
    token_data = response.json()

    if "error" in token_data:
        raise HTTPException(
            status_code=400, 
            detail=f"Google Auth Error: {token_data.get('error_description')}"
        )

    g_access_token = token_data.get("access_token")
    g_refresh_token = token_data.get("refresh_token")

    # 2. Get User Info from Google
    user_info_response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {g_access_token}"},
        timeout=10
    )
    user_info = user_info_response.json()
    email = user_info.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from Google")

    # 3. Find or Create User in DB
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        from app.functions.users.auth_functions import register_user
        new_user_data = UserCreate(
            email=email, 
            username=email.split('@')[0], 
            password="google_authenticated_user",
            full_name=user_info.get("name", "")
        )
        user = await register_user(db, new_user_data)

    # 4. Update Google Tokens in User Record
    user.google_access_token = g_access_token
    # We only save the refresh_token if it's provided (it's often missing on repeat logins)
    if g_refresh_token:
        user.google_refresh_token = g_refresh_token
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user tokens")

    # 5. Generate application JWT for the session
    access_token, refresh_token, _ = create_tokens(user.email)
    if not user.is_scanned:
        # Trigger the scan in the background so the response is still fast
        background_tasks.add_task(scan_user_emails, background_tasks, user.id)
        user.is_scanned = True
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer",
        "google_connected": True
    }

@router.get("/profile")
async def profile(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active
    }