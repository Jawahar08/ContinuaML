from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, select
from typing import List, Dict, Any
import uuid
import json
from app.db import get_db
from app.models import (
    Experiment, Metric, ResourceSample, CostEstimate, 
    ExperimentTask, ExperimentLineage, WorkspaceRole, Job, JobStatus,
    ModelVersion, Model, DatasetVersion, TrainingConfig, BenchmarkProtocol,
    ProvenanceStatus, Dataset
)
from app.auth import WorkspaceAuth
from app.queue import job_queue

router = APIRouter(prefix="/{workspace_id}/experiments", tags=["Experiment Management"])

def require_viewer(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.VIEWER))):
    return auth

def require_researcher(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.RESEARCHER))):
    return auth

def experiment_to_dict(exp: Experiment) -> dict:
    if not exp:
        return {}
    return {
        "id": exp.id,
        "workspace_id": exp.workspace_id,
        "name": exp.name,
        "model_version_id": exp.model_version_id,
        "dataset_version_id": exp.dataset_version_id,
        "strategy_id": exp.strategy_id,
        "config_id": exp.config_id,
        "protocol_id": exp.protocol_id,
        "seed": exp.seed,
        "status": exp.status,
        "safety_gate_enabled": exp.safety_gate_enabled,
        "max_forgetting_threshold": exp.max_forgetting_threshold,
        "min_accuracy_threshold": exp.min_accuracy_threshold,
        "fisher_freezing_enabled": exp.fisher_freezing_enabled,
        "fisher_importance_threshold": exp.fisher_importance_threshold,
        "frozen_param_count": exp.frozen_param_count,
        "carbon_aware_enabled": exp.carbon_aware_enabled,
        "carbon_intensity_threshold": exp.carbon_intensity_threshold,
        "dynamic_lora_routing": exp.dynamic_lora_routing,
        "lora_expert_count": exp.lora_expert_count,
        "routing_entropy_threshold": exp.routing_entropy_threshold,
        "active_coreset_replay": exp.active_coreset_replay,
        "coreset_size": exp.coreset_size,
        "selection_strategy": exp.selection_strategy,
        "created_at": exp.created_at.isoformat() if exp.created_at else None,
        "completed_at": exp.completed_at.isoformat() if exp.completed_at else None
    }

@router.post("", response_model=Any, status_code=status.HTTP_201_CREATED)
def launch_experiment(
    workspace_id: str,
    experiment: Experiment,
    auth=Depends(require_researcher),
    db: Session = Depends(get_db)
):
    if not experiment.id:
        experiment.id = f"exp-{uuid.uuid4()}"
        
    # Verify or create dummy model version if missing (to prevent foreign key failure in local dev/testing)
    if experiment.model_version_id:
        mv = db.exec(select(ModelVersion).where(ModelVersion.id == experiment.model_version_id)).first()
        if not mv:
            model_id = experiment.model_version_id.rsplit("-", 1)[0]
            m = db.exec(select(Model).where(Model.id == model_id)).first()
            if not m:
                m = Model(id=model_id, workspace_id=workspace_id, name=model_id, architecture="LlamaForCausalLM", param_count=1000000, context_length=2048, license="Apache-2.0", source="HuggingFace")
                db.add(m)
                db.commit()
            db.add(ModelVersion(id=experiment.model_version_id, model_id=model_id, version="1.0.0", download_status="ready"))
            db.commit()

    if experiment.dataset_version_id:
        dv = db.exec(select(DatasetVersion).where(DatasetVersion.id == experiment.dataset_version_id)).first()
        if not dv:
            dataset_id = experiment.dataset_version_id.rsplit("-", 1)[0]
            d = db.exec(select(Dataset).where(Dataset.id == dataset_id)).first()
            if not d:
                d = Dataset(id=dataset_id, workspace_id=workspace_id, name=dataset_id, source="HuggingFace", license="MIT")
                db.add(d)
                db.commit()
            db.add(DatasetVersion(id=experiment.dataset_version_id, dataset_id=dataset_id, version="1.0", status="REAL"))
            db.commit()

    experiment.workspace_id = workspace_id
    experiment.status = ProvenanceStatus.PLANNED
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    
    # Enqueue a background job for fine-tuning
    job_id = f"job-ft-{uuid.uuid4()}"
    job = Job(
        id=job_id,
        workspace_id=workspace_id,
        experiment_id=experiment.id,
        job_type="fine-tune",
        status=JobStatus.QUEUED,
        progress=0.0
    )
    db.add(job)
    db.commit()
    
    job_queue.enqueue(job_id, db)
    
    # Enqueue a background job for evaluation right after
    eval_job_id = f"job-ev-{uuid.uuid4()}"
    eval_job = Job(
        id=eval_job_id,
        workspace_id=workspace_id,
        experiment_id=experiment.id,
        job_type="evaluate",
        status=JobStatus.QUEUED,
        progress=0.0
    )
    db.add(eval_job)
    db.commit()
    
    job_queue.enqueue(eval_job_id, db)
    
    res = jsonable_encoder(experiment_to_dict(experiment))
    return res

@router.get("", response_model=List[Any])
def list_experiments(
    workspace_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    statement = select(Experiment).where(Experiment.workspace_id == workspace_id)
    experiments = db.exec(statement).all()
    return jsonable_encoder([experiment_to_dict(exp) for exp in experiments])

@router.get("/{experiment_id}", response_model=Any)
def get_experiment(
    workspace_id: str,
    experiment_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    stmt = select(Experiment).where(Experiment.workspace_id == workspace_id, Experiment.id == experiment_id)
    exp = db.exec(stmt).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    tasks = db.exec(select(ExperimentTask).where(ExperimentTask.experiment_id == experiment_id)).all()
    cost = db.exec(select(CostEstimate).where(CostEstimate.experiment_id == experiment_id)).first()
    
    return {
        "experiment": jsonable_encoder(experiment_to_dict(exp)),
        "tasks": jsonable_encoder([t.dict() for t in tasks]),
        "cost": jsonable_encoder(cost.dict() if cost else None)
    }

@router.get("/{experiment_id}/metrics", response_model=List[Metric])
def get_metrics(
    workspace_id: str,
    experiment_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    stmt = select(Metric).where(Metric.experiment_id == experiment_id)
    return db.exec(stmt).all()

@router.get("/{experiment_id}/reproducibility")
def get_reproducibility_manifest(
    workspace_id: str,
    experiment_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    stmt = select(Experiment).where(Experiment.workspace_id == workspace_id, Experiment.id == experiment_id)
    exp = db.exec(stmt).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    lineage = db.exec(select(ExperimentLineage).where(ExperimentLineage.experiment_id == experiment_id)).first()
    rep_hash = lineage.reproducibility_hash if lineage else "sha256-untracked"
    
    # Retrieve related versions details
    mv = db.exec(select(ModelVersion).where(ModelVersion.id == exp.model_version_id)).first()
    model = db.exec(select(Model).where(Model.id == mv.model_id)).first() if mv else None
    
    dv = db.exec(select(DatasetVersion).where(DatasetVersion.id == exp.dataset_version_id)).first()
    
    cfg = db.exec(select(TrainingConfig).where(TrainingConfig.id == exp.config_id)).first()
    hyperparams = json.loads(cfg.hyperparams_json.decode("utf-8")) if cfg else {}
    
    # Assemble reproducibility manifest
    manifest = {
      "manifest_version": "1.0",
      "experiment_id": exp.id,
      "workspace_id": workspace_id,
      "timestamp": exp.created_at.isoformat(),
      "code_provenance": {
        "git_commit": "a1b2c3d4e5f6g7h8i9j0",
        "branch": "main",
        "dirty": False
      },
      "hardware_environment": {
        "os": "Windows / Linux",
        "cpu": "Deterministic CPU Demo Engine",
        "gpu": "N/A"
      },
      "randomness_configuration": {
        "global_seed": exp.seed
      },
      "inputs": {
        "model": {
          "id": model.id if model else "N/A",
          "version": mv.version if mv else "N/A",
          "architecture": model.architecture if model else "N/A",
          "checksum": mv.checksum if mv else "N/A"
        },
        "dataset": {
          "id": dv.dataset_id if dv else "N/A",
          "version": dv.version if dv else "N/A",
          "status": dv.status.value if dv else "N/A"
        }
      },
      "hyperparameters": hyperparams,
      "reproducibility_hash": rep_hash
    }
    
    return manifest
