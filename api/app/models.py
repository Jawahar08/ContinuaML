from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON
from enum import Enum

# --- ENUMS ---
class WorkspaceRole(str, Enum):
    ADMIN = "admin"
    RESEARCHER = "researcher"
    VIEWER = "viewer"

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
    QUARANTINED = "quarantined"

class ProvenanceStatus(str, Enum):
    REAL = "REAL"
    DEMO = "DEMO"
    ESTIMATE = "ESTIMATE"
    PLANNED = "PLANNED"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"

# --- CORE TENANCY & AUTH ---

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Workspace(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Membership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    role: WorkspaceRole = Field(default=WorkspaceRole.VIEWER)

class APIKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    key_hash: str = Field(index=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    created_by: int = Field(foreign_key="user.id")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Session(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- MODELS REGISTRY ---

class Model(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    architecture: str
    param_count: int
    context_length: int
    license: str
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ModelVersion(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    model_id: str = Field(foreign_key="model.id", index=True)
    version: str
    download_status: str  # e.g., "ready", "pending", "failed"
    checksum: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ModelCard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: str = Field(foreign_key="model.id", index=True)
    intended_use: str
    limitations: str
    license_restrictions: str
    evaluation_summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ModelArtifact(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    model_version_id: str = Field(foreign_key="modelversion.id", index=True)
    uri: str
    size_bytes: int
    checksum: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- DATASETS REGISTRY ---

class Dataset(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    source: str
    license: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DatasetVersion(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    dataset_id: str = Field(foreign_key="dataset.id", index=True)
    version: str
    status: ProvenanceStatus = Field(default=ProvenanceStatus.REAL)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DatasetCard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: str = Field(foreign_key="dataset.id", index=True)
    provenance: str
    collection_date: str
    known_limitations: str
    validation_summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PreprocessingRecipe(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    recipe_json: bytes = Field(default=b"{}")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ContaminationCheck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_version_id: str = Field(foreign_key="datasetversion.id", index=True)
    benchmark_overlap_rate: float
    pii_risk_score: float
    malformed_rows_count: int
    quarantine_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- RESEARCH PLANS & EXPERIMENTS ---

class ResearchPlan(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    hypothesis: str
    baseline_model_id: str = Field(foreign_key="model.id")
    target_dataset_id: str = Field(foreign_key="dataset.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Hypothesis(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    plan_id: str = Field(foreign_key="researchplan.id", index=True)
    statement: str
    metric: str
    expected_value: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AblationFactor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: str = Field(foreign_key="researchplan.id", index=True)
    factor_name: str  # e.g., "learning_rate", "replay_ratio", "strategy"
    values_json: bytes = Field(default=b"[]")  # list of values tested

class PlannedRun(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    plan_id: str = Field(foreign_key="researchplan.id", index=True)
    config_summary: str
    status: ProvenanceStatus = Field(default=ProvenanceStatus.PLANNED)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TrainingConfig(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    hyperparams_json: bytes = Field(default=b"{}")  # stores lr, batch_size, epochs, lora_r, lora_alpha, etc.

class ContinualLearningStrategy(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str  # e.g., "EWC", "ReservoirSampling", "FineTuningBaseline"
    description: str
    citation: str
    parameters_schema_json: bytes = Field(default=b"{}")


# --- BENCHMARKS & EVALUATION ---

class BenchmarkTask(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    dataset_version_id: str = Field(foreign_key="datasetversion.id")
    metric_type: str  # accuracy, pass@k, loss, perplexity
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BenchmarkProtocol(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    tasks_order_json: bytes = Field(default=b"[]")  # List of Task IDs in evaluation sequence


# --- EXPERIMENTS & RUNS ---

class Experiment(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    model_version_id: str = Field(foreign_key="modelversion.id", index=True)
    dataset_version_id: str = Field(foreign_key="datasetversion.id", index=True)
    strategy_id: Optional[str] = Field(default=None, foreign_key="continuallearningstrategy.id")
    config_id: str = Field(foreign_key="trainingconfig.id")
    protocol_id: str = Field(foreign_key="benchmarkprotocol.id")
    seed: int
    status: ProvenanceStatus = Field(default=ProvenanceStatus.PLANNED)
    safety_gate_enabled: bool = Field(default=False)
    max_forgetting_threshold: float = Field(default=0.20)
    min_accuracy_threshold: float = Field(default=0.50)
    fisher_freezing_enabled: bool = Field(default=False)
    fisher_importance_threshold: float = Field(default=0.85)
    frozen_param_count: Optional[int] = Field(default=None)
    carbon_aware_enabled: bool = Field(default=False)
    carbon_intensity_threshold: float = Field(default=250.0)
    dynamic_lora_routing: bool = Field(default=False)
    lora_expert_count: int = Field(default=4)
    routing_entropy_threshold: float = Field(default=0.75)
    active_coreset_replay: bool = Field(default=False)
    coreset_size: int = Field(default=1000)
    selection_strategy: str = Field(default="herding")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class ExperimentTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: str = Field(foreign_key="experiment.id", index=True)
    task_id: str = Field(foreign_key="benchmarktask.id", index=True)
    score: float
    status: ProvenanceStatus = Field(default=ProvenanceStatus.REAL)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

class ExperimentLineage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: str = Field(foreign_key="experiment.id", index=True)
    parent_experiment_id: Optional[str] = Field(default=None, foreign_key="experiment.id")
    plan_id: Optional[str] = Field(default=None, foreign_key="researchplan.id")
    reproducibility_hash: str


# --- JOBS MACHINE ---

class Job(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    experiment_id: Optional[str] = Field(default=None, foreign_key="experiment.id", index=True)
    job_type: str  # e.g., "fine-tune", "evaluate", "import-dataset"
    status: JobStatus = Field(default=JobStatus.QUEUED)
    progress: float = 0.0  # 0 to 100
    retries: int = 0
    idempotency_key: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class JobEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="job.id", index=True)
    from_state: str
    to_state: str
    transition_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="job.id", index=True)
    content: str
    level: str = "INFO"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Checkpoint(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    experiment_id: str = Field(foreign_key="experiment.id", index=True)
    step: int
    uri: str
    checksum: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Metric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: str = Field(foreign_key="experiment.id", index=True)
    name: str  # e.g., "train_loss", "forgetting_score", "learning_rate", "avg_accuracy"
    value: float
    step: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ResourceSample(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="job.id", index=True)
    cpu_percent: float
    ram_used_mb: float
    gpu_percent: float
    vram_used_mb: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CostEstimate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: str = Field(foreign_key="experiment.id", index=True)
    gpu_hours: float
    kwh_estimate: float
    co2_kg_estimate: float
    cloud_cost_usd: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- COLLABORATION & REPORTING ---

class Schedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    cron_expr: str
    payload_json: bytes = Field(default=b"{}")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Webhook(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    url: str
    secret: str
    events_json: bytes = Field(default=b"[]")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    experiment_id: Optional[str] = Field(default=None, foreign_key="experiment.id", index=True)
    report_id: Optional[str] = Field(default=None, foreign_key="report.id", index=True)
    user_id: int = Field(foreign_key="user.id")
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Report(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    title: str
    abstract: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReportVersion(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    report_id: str = Field(foreign_key="report.id", index=True)
    version: int
    content: str  # Markdown/LaTeX content
    reproducibility_manifest_uri: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    action: str  # e.g., "register-model", "delete-dataset", "view-manifest"
    target_id: Optional[str] = None
    details: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Quota(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", unique=True)
    max_storage_bytes: int = 10 * 1024 * 1024 * 1024  # 10GB
    max_gpu_hours: float = 100.0
    used_storage_bytes: int = 0
    used_gpu_hours: float = 0.0

class FeatureFlag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    flag_key: str
    is_enabled: bool = False

class ModelMerge(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    parent_a_version_id: str = Field(foreign_key="modelversion.id")
    parent_b_version_id: str = Field(foreign_key="modelversion.id")
    merged_model_version_id: Optional[str] = Field(default=None, foreign_key="modelversion.id")
    merge_method: str  # "slerp", "ties", "dare"
    merge_ratio: float  # 0.0 to 1.0 (weight of parent B)
    status: JobStatus = Field(default=JobStatus.QUEUED)
    job_id: Optional[str] = Field(default=None, foreign_key="job.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class SafetyGateEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    experiment_id: str = Field(foreign_key="experiment.id", index=True)
    metric_name: str  # e.g., "forgetting_score", "avg_accuracy"
    threshold_value: float
    observed_value: float
    action_taken: str  # "halt", "rollback_to_checkpoint"
    created_at: datetime = Field(default_factory=datetime.utcnow)
