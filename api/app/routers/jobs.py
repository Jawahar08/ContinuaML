from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.db import get_db
from app.models import Job, Log, JobStatus, WorkspaceRole
from app.auth import WorkspaceAuth
from app.queue import job_queue

router = APIRouter(prefix="/{workspace_id}/jobs", tags=["Background Jobs"])

def require_viewer(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.VIEWER))):
    return auth

def require_researcher(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.RESEARCHER))):
    return auth

@router.get("/{job_id}", response_model=Job)
def get_job_status(
    workspace_id: str,
    job_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    stmt = select(Job).where(Job.workspace_id == workspace_id, Job.id == job_id)
    job = db.exec(stmt).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/logs", response_model=List[Log])
def get_job_logs(
    workspace_id: str,
    job_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    # Verify job exists
    stmt = select(Job).where(Job.workspace_id == workspace_id, Job.id == job_id)
    if not db.exec(stmt).first():
        raise HTTPException(status_code=404, detail="Job not found")
        
    logs_stmt = select(Log).where(Log.job_id == job_id).order_by(Log.created_at)
    return db.exec(logs_stmt).all()

@router.post("/{job_id}/cancel")
def cancel_job(
    workspace_id: str,
    job_id: str,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    stmt = select(Job).where(Job.workspace_id == workspace_id, Job.id == job_id)
    job = db.exec(stmt).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status in [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.RETRYING]:
        job_queue.transition_job(job_id, JobStatus.CANCELLING, db, "Cancellation requested by user")
        # In a real engine, we would send cancellation signals to the executing subprocess/thread
        # Here we just mark it cancelled directly for demonstration
        job_queue.transition_job(job_id, JobStatus.CANCELLED, db, "Cancelled successfully")
        return {"message": "Job cancelled successfully"}
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job in state {job.status.value}"
        )

@router.post("/{job_id}/retry")
def retry_job(
    workspace_id: str,
    job_id: str,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    stmt = select(Job).where(Job.workspace_id == workspace_id, Job.id == job_id)
    job = db.exec(stmt).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status in [JobStatus.FAILED, JobStatus.CANCELLED]:
        job.retries += 1
        job.progress = 0.0
        db.add(job)
        db.commit()
        
        job_queue.transition_job(job_id, JobStatus.QUEUED, db, "Retrying job")
        job_queue.enqueue(job_id, db)
        return {"message": "Job retried successfully"}
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot retry job in state {job.status.value}"
        )
