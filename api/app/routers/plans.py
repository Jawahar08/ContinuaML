from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
import uuid
from app.db import get_db
from app.models import ResearchPlan, Hypothesis, AblationFactor, PlannedRun, WorkspaceRole
from app.auth import WorkspaceAuth

router = APIRouter(prefix="/{workspace_id}/plans", tags=["Research Plans"])

def require_viewer(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.VIEWER))):
    return auth

def require_researcher(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.RESEARCHER))):
    return auth

@router.post("", response_model=ResearchPlan, status_code=status.HTTP_201_CREATED)
def create_plan(
    workspace_id: str,
    plan: ResearchPlan,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    plan.workspace_id = workspace_id
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@router.get("", response_model=List[ResearchPlan])
def list_plans(
    workspace_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    statement = select(ResearchPlan).where(ResearchPlan.workspace_id == workspace_id)
    return db.exec(statement).all()

@router.post("/{plan_id}/hypotheses", response_model=Hypothesis)
def create_hypothesis(
    workspace_id: str,
    plan_id: str,
    hypothesis: Hypothesis,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    stmt = select(ResearchPlan).where(ResearchPlan.workspace_id == workspace_id, ResearchPlan.id == plan_id)
    if not db.exec(stmt).first():
        raise HTTPException(status_code=404, detail="Research plan not found")
        
    hypothesis.plan_id = plan_id
    db.add(hypothesis)
    db.commit()
    db.refresh(hypothesis)
    return hypothesis

@router.post("/{plan_id}/ablation", response_model=AblationFactor)
def create_ablation_factor(
    workspace_id: str,
    plan_id: str,
    factor: AblationFactor,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    stmt = select(ResearchPlan).where(ResearchPlan.workspace_id == workspace_id, ResearchPlan.id == plan_id)
    if not db.exec(stmt).first():
        raise HTTPException(status_code=404, detail="Research plan not found")
        
    factor.plan_id = plan_id
    db.add(factor)
    db.commit()
    db.refresh(factor)
    return factor

@router.get("/{plan_id}/runs", response_model=List[PlannedRun])
def list_planned_runs(
    workspace_id: str,
    plan_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    # Verify plan exists
    stmt = select(ResearchPlan).where(ResearchPlan.workspace_id == workspace_id, ResearchPlan.id == plan_id)
    if not db.exec(stmt).first():
        raise HTTPException(status_code=404, detail="Research plan not found")
        
    # Check if runs already generated, otherwise generate some planned runs based on ablation
    runs_stmt = select(PlannedRun).where(PlannedRun.plan_id == plan_id)
    runs = db.exec(runs_stmt).all()
    
    if not runs:
        # Create default baseline and ablation runs
        r1 = PlannedRun(id=f"run-{uuid.uuid4()}", plan_id=plan_id, config_summary="FineTuningBaseline | LR=5e-5 | Seed=42")
        r2 = PlannedRun(id=f"run-{uuid.uuid4()}", plan_id=plan_id, config_summary="EWC | LR=5e-5 | Lambda=100 | Seed=42")
        db.add(r1)
        db.add(r2)
        db.commit()
        db.refresh(r1)
        db.refresh(r2)
        runs = [r1, r2]
        
    return runs
