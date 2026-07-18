import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from passlib.context import CryptContext
from app.config import settings
from app.db import get_db
from app.models import User, Membership, WorkspaceRole

# Use bcrypt for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    statement = select(User).where(User.email == email)
    user = db.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user

class WorkspaceAuth:
    """Dependency helper to enforce workspace membership and roles."""
    def __init__(self, min_role: WorkspaceRole):
        self.min_role = min_role

    def __call__(
        self, 
        workspace_id: str, 
        user: User = Depends(get_current_user), 
        db: Session = Depends(get_db)
    ) -> Membership:
        # Check membership
        statement = select(Membership).where(
            Membership.user_id == user.id,
            Membership.workspace_id == workspace_id
        )
        membership = db.exec(statement).first()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this workspace"
            )
        
        # Enforce role hierarchy: Admin > Researcher > Viewer
        role_hierarchy = {
            WorkspaceRole.ADMIN: 3,
            WorkspaceRole.RESEARCHER: 2,
            WorkspaceRole.VIEWER: 1
        }
        
        if role_hierarchy[membership.role] < role_hierarchy[self.min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires minimum role of {self.min_role.value}"
            )
            
        return membership
