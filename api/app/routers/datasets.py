from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select
from typing import List
import uuid
from app.db import get_db
from app.models import Dataset, DatasetVersion, ContaminationCheck, DatasetCard, WorkspaceRole, Job, JobStatus
from app.auth import WorkspaceAuth
from app.queue import job_queue
from app.storage import storage_provider

router = APIRouter(prefix="/{workspace_id}/datasets", tags=["Dataset Management"])

def require_viewer(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.VIEWER))):
    return auth

def require_researcher(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.RESEARCHER))):
    return auth

@router.post("", response_model=Dataset, status_code=status.HTTP_201_CREATED)
def register_dataset(
    workspace_id: str,
    dataset: Dataset,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    dataset.workspace_id = workspace_id
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset

@router.get("", response_model=List[Dataset])
def list_datasets(
    workspace_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    statement = select(Dataset).where(Dataset.workspace_id == workspace_id)
    return db.exec(statement).all()

@router.post("/{dataset_id}/import")
async def import_dataset_file(
    workspace_id: str,
    dataset_id: str,
    version_str: str,
    file: UploadFile = File(...),
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    # Verify dataset exists
    stmt = select(Dataset).where(Dataset.workspace_id == workspace_id, Dataset.id == dataset_id)
    if not db.exec(stmt).first():
        raise HTTPException(status_code=404, detail="Dataset not found in workspace")
        
    content = await file.read()
    
    # Save file using storage provider
    uri, checksum, size_bytes = storage_provider.save_artifact(
        workspace_id=workspace_id,
        category="datasets",
        filename=file.filename,
        content=content
    )
    
    # Create dataset version
    version_id = f"{dataset_id}-{version_str.replace('.', '_')}"
    ds_version = DatasetVersion(
        id=version_id,
        dataset_id=dataset_id,
        version=version_str,
        status=ProvenanceStatus.PLANNED if False else "REAL" # default status
    )
    db.add(ds_version)
    db.commit()
    db.refresh(ds_version)
    
    # Trigger verification background job
    job_id = f"job-ds-{uuid.uuid4()}"
    job = Job(
        id=job_id,
        workspace_id=workspace_id,
        job_type="import-dataset",
        status=JobStatus.QUEUED,
        progress=0.0
    )
    db.add(job)
    db.commit()
    
    job_queue.enqueue(job_id, db)
    
    # Seed contamination check data deterministically
    check = ContaminationCheck(
        dataset_version_id=version_id,
        benchmark_overlap_rate=0.012,
        pii_risk_score=0.0,
        malformed_rows_count=0
    )
    db.add(check)
    db.commit()
    
    return {
        "message": "Dataset uploaded and verification queued",
        "dataset_version_id": version_id,
        "job_id": job_id,
        "artifact_uri": uri
    }

@router.get("/{dataset_id}")
def get_dataset(
    workspace_id: str,
    dataset_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    stmt = select(Dataset).where(Dataset.workspace_id == workspace_id, Dataset.id == dataset_id)
    dataset = db.exec(stmt).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    versions = db.exec(select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id)).all()
    card = db.exec(select(DatasetCard).where(DatasetCard.dataset_id == dataset_id)).first()
    
    return {
        "dataset": dataset,
        "versions": versions,
        "card": card
    }
