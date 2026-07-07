"""Authentication routes."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from api.models.request import LoginRequest, UserCreate
from api.models.response import TokenResponse, UserResponse
from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from database.metadata_store import MetadataStore

metadata_store = MetadataStore()


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=config.jwt_expiration)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        config.api_secret_key,
        algorithm=config.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            config.api_secret_key,
            algorithms=[config.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login and get access token."""
    user = metadata_store.get_user_by_username(request.username)
    
    if not user or not pwd_context.verify(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": request.username})
    
    return TokenResponse(
        access_token=access_token,
        expires_in=config.jwt_expiration
    )


@router.post("/register", response_model=UserResponse)
async def register(request: UserCreate):
    """Register a new user."""
    if metadata_store.get_user_by_username(request.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = pwd_context.hash(request.password)
    
    metadata_store.add_user(
        username=request.username,
        hashed_password=hashed_password,
        email=request.email,
        full_name=request.full_name
    )
    
    return UserResponse(
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        created_at=datetime.utcnow()
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(username: str = Depends(verify_token)):
    """Get current user information."""
    user = metadata_store.get_user_by_username(username)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        username=user["username"],
        email=user.get("email"),
        full_name=user.get("full_name"),
        created_at=datetime.utcnow()
    )