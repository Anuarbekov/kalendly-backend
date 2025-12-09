from datetime import datetime, timedelta
import os
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status
from authlib.integrations.starlette_client import OAuth
import httpx
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/calendar.events',
        'prompt': 'consent',
        'access_type': 'offline'
    }
)

class GoogleLoginRequest(BaseModel):
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str
    email: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    # 'exp' is a standard JWT claim for expiration
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login/google")
async def login_via_google(
    request: GoogleLoginRequest, 
    db: Session = Depends(get_db)
):
    async with httpx.AsyncClient() as client:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": request.code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": "postmessage",
            "grant_type": "authorization_code",
        }
        response = await client.post(token_url, data=data)
        
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get tokens from Google")
        
    tokens = response.json()
    google_access_token = tokens["access_token"]
    google_refresh_token = tokens.get("refresh_token")

    # 2. Get User Email
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {google_access_token}"}
        user_info = await client.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers)
        profile = user_info.json()
    
    email = profile.get("email")
    if not email:
         raise HTTPException(status_code=400, detail="Google account has no email")

    # 3. DB Logic
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(email=email)
        db.add(user)
    
    user.google_access_token = google_access_token
    if google_refresh_token:
        user.google_refresh_token = google_refresh_token
    
    db.commit()

    # 4. CREATE THE REAL JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": email
    }

@router.post("/login") # This matches your tokenUrl="auth/login" (prefix is /auth)
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    DEV ONLY: Logs in a user by email (ignores password).
    Allows Swagger UI to authorize using existing DB users.
    """
    # 1. Find user by email (Swagger sends email in the 'username' field)
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # 2. Create the JWT Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    
    # 3. Return exact format Swagger expects
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    
    email = user_info.get("email")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(email=email)
        db.add(user)
    
    user.google_access_token = token.get('access_token')
    
    if token.get('refresh_token'):
        user.google_refresh_token = token.get('refresh_token')
        
    db.commit()
    
    return {"status": "success", "email": email, "msg": "Tokens stored in DB"}