from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, select
from typing import List, Any
from app.db import get_db
from app.models import SafetyGateEvent, WorkspaceRole
from app.auth import WorkspaceAuth

router = APIRouter(prefix="/{workspace_id}/experiments", tags=["Safety Gate Management"])

def require_viewer(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.VIEWER))):
    return auth

@router.get("/{experiment_id}/safety-events", response_model=Any)
def get_safety_events(
    workspace_id: str,
    experiment_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    statement = select(SafetyGateEvent).where(
        SafetyGateEvent.workspace_id == workspace_id,
        SafetyGateEvent.experiment_id == experiment_id
    )
    events = db.exec(statement).all()
    return jsonable_encoder(events)
