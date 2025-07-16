from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .database import get_db, User, UserApiKey
from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
bearer_scheme = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(*, subject: str, expires_delta: timedelta | None = None):
    """Create a JWT access token"""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str = Depends(bearer_scheme), db: Session = Depends(get_db)) -> str:
    """Verify JWT token and return username"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        
        # Check if user exists in database
        user = db.query(User).filter(User.username == username, User.is_active == 1).first()
        if not user:
            raise credentials_exception
            
        return username
    except JWTError:
        raise credentials_exception

def get_user_by_username(db: Session, username: str) -> User:
    """Get user by username"""
    return db.query(User).filter(User.username == username, User.is_active == 1).first()

def get_user_by_email(db: Session, email: str) -> User:
    """Get user by email"""
    return db.query(User).filter(User.email == email, User.is_active == 1).first()

def authenticate_user(db: Session, username: str, password: str) -> User:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_user(db: Session, username: str, email: str, password: str) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_api_keys(db: Session, user_id: int) -> list[UserApiKey]:
    """Get all API keys for a user"""
    return db.query(UserApiKey).filter(UserApiKey.user_id == user_id).all()

def get_user_api_key(db: Session, user_id: int, model_name: str) -> UserApiKey:
    """Get specific API key for a user and model"""
    return db.query(UserApiKey).filter(
        UserApiKey.user_id == user_id,
        UserApiKey.model_name == model_name
    ).first()

def create_or_update_api_key(db: Session, user_id: int, model_name: str, api_key: str) -> UserApiKey:
    """Create or update API key for a user and model"""
    existing_key = get_user_api_key(db, user_id, model_name)
    
    if existing_key:
        existing_key.api_key = api_key
        existing_key.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_key)
        return existing_key
    else:
        new_key = UserApiKey(
            user_id=user_id,
            model_name=model_name,
            api_key=api_key
        )
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        return new_key

def delete_api_key(db: Session, user_id: int, model_name: str) -> bool:
    """Delete API key for a user and model"""
    api_key = get_user_api_key(db, user_id, model_name)
    if api_key:
        db.delete(api_key)
        db.commit()
        return True
    return False
