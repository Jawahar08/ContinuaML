from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.db import get_db
from app.models import Model, ModelVersion, ModelCard, WorkspaceRole
from app.auth import WorkspaceAuth

router = APIRouter(prefix="/{workspace_id}/models", tags=["Model Registry"])

# Dependency shortcut for auth role verification
def require_viewer(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.VIEWER))):
    return auth

def require_researcher(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.RESEARCHER))):
    return auth

@router.post("", response_model=Model, status_code=status.HTTP_201_CREATED)
def register_model(
    workspace_id: str,
    model: Model,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    model.workspace_id = workspace_id
    db.add(model)
    db.commit()
    db.refresh(model)
    return model

@router.get("", response_model=List[Model])
def list_models(
    workspace_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    statement = select(Model).where(Model.workspace_id == workspace_id)
    return db.exec(statement).all()

@router.get("/{model_id}")
def get_model(
    workspace_id: str,
    model_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    statement = select(Model).where(Model.workspace_id == workspace_id, Model.id == model_id)
    model = db.exec(statement).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
        
    versions = db.exec(select(ModelVersion).where(ModelVersion.model_id == model_id)).all()
    card = db.exec(select(ModelCard).where(ModelCard.model_id == model_id)).first()
    
    return {
        "model": model,
        "versions": versions,
        "card": card
    }

@router.post("/{model_id}/versions", response_model=ModelVersion)
def create_version(
    workspace_id: str,
    model_id: str,
    version: ModelVersion,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    # Verify model exists in workspace
    stmt = select(Model).where(Model.workspace_id == workspace_id, Model.id == model_id)
    if not db.exec(stmt).first():
        raise HTTPException(status_code=404, detail="Model not found in workspace")
        
    version.model_id = model_id
    db.add(version)
    db.commit()
    db.refresh(version)
    return version

@router.post("/{model_id}/card", response_model=ModelCard)
def create_model_card(
    workspace_id: str,
    model_id: str,
    card: ModelCard,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    # Verify model exists
    stmt = select(Model).where(Model.workspace_id == workspace_id, Model.id == model_id)
    if not db.exec(stmt).first():
        raise HTTPException(status_code=404, detail="Model not found in workspace")
        
    # Check if card exists
    existing = db.exec(select(ModelCard).where(ModelCard.model_id == model_id)).first()
    if existing:
        existing.intended_use = card.intended_use
        existing.limitations = card.limitations
        existing.license_restrictions = card.license_restrictions
        existing.evaluation_summary = card.evaluation_summary
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
        
    card.model_id = model_id
    db.add(card)
    db.commit()
    db.refresh(card)
    return card
