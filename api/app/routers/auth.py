from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.db import get_db
from app.models import User, Workspace, Membership, WorkspaceRole
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(email: str, password: str, db: Session = Depends(get_db)):
    # Check if user exists
    statement = select(User).where(User.email == email)
    existing_user = db.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already registered"
        )
        
    # Create user
    user = User(email=email, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create default workspace for user
    ws_id = f"workspace_{email.split('@')[0]}"
    workspace = Workspace(id=ws_id, name=f"{email.split('@')[0]}'s Workspace")
    db.add(workspace)
    
    membership = Membership(
        user_id=user.id,
        workspace_id=ws_id,
        role=WorkspaceRole.ADMIN
    )
    db.add(membership)
    db.commit()
    
    return {"message": "User registered successfully", "workspace_id": ws_id}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    statement = select(User).where(User.email == form_data.username)
    user = db.exec(statement).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/workspaces", response_model=List[Workspace])
def list_workspaces(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    statement = (
        select(Workspace)
        .join(Membership)
        .where(Membership.user_id == user.id)
    )
    workspaces = db.exec(statement).all()
    return workspaces

@router.post("/workspaces", response_model=Workspace)
def create_workspace(name: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = f"workspace_{name.lower().replace(' ', '_')}"
    existing_ws = db.exec(select(Workspace).where(Workspace.id == ws_id)).first()
    if existing_ws:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace ID already exists"
        )
        
    workspace = Workspace(id=ws_id, name=name)
    db.add(workspace)
    
    membership = Membership(
        user_id=user.id,
        workspace_id=ws_id,
        role=WorkspaceRole.ADMIN
    )
    db.add(membership)
    db.commit()
    db.refresh(workspace)
    return workspace

