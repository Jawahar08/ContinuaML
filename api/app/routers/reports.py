from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
import uuid
from app.db import get_db
from app.models import Report, ReportVersion, Comment, WorkspaceRole, User
from app.auth import WorkspaceAuth, get_current_user

router = APIRouter(prefix="/{workspace_id}/reports", tags=["Research Reports"])

def require_viewer(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.VIEWER))):
    return auth

def require_researcher(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.RESEARCHER))):
    return auth

@router.post("", response_model=Report, status_code=status.HTTP_201_CREATED)
def create_report(
    workspace_id: str,
    report: Report,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    report.workspace_id = workspace_id
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

@router.get("", response_model=List[Report])
def list_reports(
    workspace_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    statement = select(Report).where(Report.workspace_id == workspace_id)
    return db.exec(statement).all()

@router.get("/{report_id}")
def get_report(
    workspace_id: str,
    report_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    stmt = select(Report).where(Report.workspace_id == workspace_id, Report.id == report_id)
    report = db.exec(stmt).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    versions = db.exec(select(ReportVersion).where(ReportVersion.report_id == report_id)).all()
    return {
        "report": report,
        "versions": versions
    }

@router.post("/{report_id}/versions", response_model=ReportVersion)
def save_report_version(
    workspace_id: str,
    report_id: str,
    content: str,
    manifest_uri: Optional[str] = None,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    stmt = select(Report).where(Report.workspace_id == workspace_id, Report.id == report_id)
    if not db.exec(stmt).first():
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Get highest version
    v_stmt = select(ReportVersion).where(ReportVersion.report_id == report_id).order_by(ReportVersion.version.desc())
    highest_v = db.exec(v_stmt).first()
    next_v = (highest_v.version + 1) if highest_v else 1
    
    r_ver = ReportVersion(
        id=f"rep-ver-{uuid.uuid4()}",
        report_id=report_id,
        version=next_v,
        content=content,
        reproducibility_manifest_uri=manifest_uri
    )
    db.add(r_ver)
    db.commit()
    db.refresh(r_ver)
    return r_ver

@router.post("/{report_id}/comments", response_model=Comment)
def add_comment(
    workspace_id: str,
    report_id: str,
    text: str,
    auth=Depends(require_viewer),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = Comment(
        workspace_id=workspace_id,
        report_id=report_id,
        user_id=user.id,
        text=text
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

@router.get("/{report_id}/comments", response_model=List[Comment])
def get_comments(
    workspace_id: str,
    report_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    stmt = select(Comment).where(Comment.workspace_id == workspace_id, Comment.report_id == report_id)
    return db.exec(stmt).all()
