from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, select
from typing import List, Any
import uuid
from datetime import datetime
from app.db import get_db
from app.models import Model, ModelVersion, ModelCard, WorkspaceRole, ModelMerge, Job, JobStatus
from app.auth import WorkspaceAuth
from app.queue import job_queue

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

@router.post("/merge", response_model=Any, status_code=status.HTTP_201_CREATED)
def merge_models(
    workspace_id: str,
    merge_data: ModelMerge,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    parent_a = db.exec(select(ModelVersion).where(ModelVersion.id == merge_data.parent_a_version_id)).first()
    parent_b = db.exec(select(ModelVersion).where(ModelVersion.id == merge_data.parent_b_version_id)).first()
    if not parent_a or not parent_b:
        raise HTTPException(status_code=404, detail="One or both parent model versions not found")

    if not merge_data.id:
        merge_data.id = f"merge-{uuid.uuid4()}"

    merge_data.workspace_id = workspace_id
    merge_data.status = JobStatus.QUEUED

    # Enqueue background job
    job_id = f"job-merge-{uuid.uuid4()}"
    job = Job(
        id=job_id,
        workspace_id=workspace_id,
        job_type="model-merge",
        status=JobStatus.QUEUED,
        progress=0.0
    )
    db.add(job)
    db.commit()

    merge_data.job_id = job_id
    db.add(merge_data)
    db.commit()
    db.refresh(merge_data)

    job_queue.enqueue(job_id, db)
    return {
        "id": merge_data.id,
        "workspace_id": merge_data.workspace_id,
        "name": merge_data.name,
        "parent_a_version_id": merge_data.parent_a_version_id,
        "parent_b_version_id": merge_data.parent_b_version_id,
        "merged_model_version_id": merge_data.merged_model_version_id,
        "merge_method": merge_data.merge_method,
        "merge_ratio": merge_data.merge_ratio,
        "status": merge_data.status,
        "job_id": merge_data.job_id,
        "created_at": merge_data.created_at.isoformat() if merge_data.created_at else None,
        "completed_at": merge_data.completed_at.isoformat() if merge_data.completed_at else None
    }

@router.get("/merges", response_model=List[Any])
def list_merges(
    workspace_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    statement = select(ModelMerge).where(ModelMerge.workspace_id == workspace_id)
    merges = db.exec(statement).all()
    
    res_list = []
    for m in merges:
        res_list.append({
            "id": m.id,
            "workspace_id": m.workspace_id,
            "name": m.name,
            "parent_a_version_id": m.parent_a_version_id,
            "parent_b_version_id": m.parent_b_version_id,
            "merged_model_version_id": m.merged_model_version_id,
            "merge_method": m.merge_method,
            "merge_ratio": m.merge_ratio,
            "status": m.status,
            "job_id": m.job_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "completed_at": m.completed_at.isoformat() if m.completed_at else None
        })
    return res_list

@router.get("/merges/{merge_id}", response_model=Any)
def get_merge(
    workspace_id: str,
    merge_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    statement = select(ModelMerge).where(ModelMerge.workspace_id == workspace_id, ModelMerge.id == merge_id)
    merge = db.exec(statement).first()
    if not merge:
        raise HTTPException(status_code=404, detail="Merge record not found")

    logs = []
    if merge.job_id:
        from app.models import Log
        logs = db.exec(select(Log).where(Log.job_id == merge.job_id).order_by(Log.created_at)).all()

    return {
        "merge": {
            "id": merge.id,
            "workspace_id": merge.workspace_id,
            "name": merge.name,
            "parent_a_version_id": merge.parent_a_version_id,
            "parent_b_version_id": merge.parent_b_version_id,
            "merged_model_version_id": merge.merged_model_version_id,
            "merge_method": merge.merge_method,
            "merge_ratio": merge.merge_ratio,
            "status": merge.status,
            "job_id": merge.job_id,
            "created_at": merge.created_at.isoformat() if merge.created_at else None,
            "completed_at": merge.completed_at.isoformat() if merge.completed_at else None
        },
        "logs": [{"content": l.content, "level": l.level, "created_at": l.created_at.isoformat()} for l in logs]
    }
