# Feature and Support Matrix

This matrix maps every requirement of ForgetGuard AI to its technical ownership, routes, models, tests, documentation, and support status.

## Status Enums
- `REAL`: Executed by a supported real implementation with recorded inputs/outputs.
- `DEMO`: Processed by a deterministic local demo adapter.
- `ESTIMATE`: Calculated from assumptions.
- `PLANNED`: Defined in a research plan but not executed.
- `UNSUPPORTED`: Recognized by the platform but unavailable for selected model/task/hardware.
- `FAILED`: Execution started or validation ran but failed.
- `QUARANTINED`: Blocked by security, privacy, license, contamination, or validation policy.

| Feature / Requirement | Frontend Component/Page | Backend API Route | Database Model | Background Job | Tests | Documentation | Status |
|---|---|---|---|---|---|---|---|
| **User Sign-in / JWT Auth** | `/auth` Page | `/api/v1/auth/login` | `User`, `Session` | None | `tests/test_auth.py` | `docs/architecture-decisions.md` | **REAL** |
| **Workspace RBAC** | Workspace Selector | `/api/v1/auth/workspaces` | `Workspace`, `Membership` | None | `tests/test_rbac.py` | `docs/architecture-decisions.md` | **REAL** |
| **Model Registration** | `/models` List / Card | `/api/v1/models` | `Model`, `ModelVersion` | Fetch/Register Model | `tests/test_models.py` | `docs/reproducibility.md` | **REAL** |
| **Dataset Import / Cards** | `/datasets` Upload / Details | `/api/v1/datasets` | `Dataset`, `DatasetVersion`, `DatasetCard` | Validate Dataset | `tests/test_datasets.py` | `docs/security-threat-model.md` | **REAL** |
| **Dataset Contamination Check** | `/datasets` Validation Detail | `/api/v1/datasets/{id}/validate` | `ContaminationCheck` | Contamination Analyzer | `tests/test_datasets.py` | `docs/security-threat-model.md` | **REAL** |
| **Research Plans / Ablations** | `/plans` Designer | `/api/v1/plans` | `ResearchPlan`, `AblationFactor` | None | `tests/test_plans.py` | `docs/research-methodology.md` | **REAL** |
| **Fine-Tuning Configuration** | `/experiments/new` Form | `/api/v1/experiments` | `TrainingConfig` | None | `tests/test_experiments.py` | `docs/reproducibility.md` | **REAL** |
| **Continual Learning Strategy Engine** | Strategy Registry Selector | `/api/v1/strategies` | `ContinualLearningStrategy` | Strategy execution | `tests/test_strategies.py` | `docs/research-methodology.md` | **DEMO** / **REAL** |
| **Evaluation Suite** | Evaluation Metrics Graph | `/api/v1/experiments/{id}/evaluate` | `BenchmarkTask`, `ExperimentTask` | Sandbox Eval Job | `tests/test_sandbox.py` | `docs/research-methodology.md` | **DEMO** / **REAL** |
| **Sandboxed Code Execution** | Code Execution Panel | `/api/v1/sandbox/run` | None | Sandbox Process | `tests/test_sandbox.py` | `docs/security-threat-model.md` | **REAL** |
| **Resource / Cost / Carbon Monitor** | Metrics / Carbon Widget | `/api/v1/experiments/{id}/resources` | `ResourceSample`, `CostEstimate` | Resource sampler | `tests/test_experiments.py` | `docs/reproducibility.md` | **ESTIMATE** / **REAL** |
| **Reproducibility Manifest** | Download JSON Button | `/api/v1/experiments/{id}/reproducibility` | `ExperimentLineage` | None | `tests/test_experiments.py` | `docs/reproducibility.md` | **REAL** |
| **AI Research Assistant** | Chatbot / Analysis Pane | `/api/v1/assistant/analyze` | `Comment` | LLM Analysis Job | `tests/test_assistant.py` | `docs/architecture-decisions.md` | **DEMO** |
| **Research Paper Generator** | `/reports` Exporter | `/api/v1/reports` | `Report`, `ReportVersion` | Compile PDF/LaTeX Job | `tests/test_reports.py` | `docs/research-methodology.md` | **REAL** |
| **Leaderboard / Compare** | `/leaderboard` Page | `/api/v1/leaderboard` | None | None | `tests/test_leaderboard.py` | `docs/research-methodology.md` | **REAL** |
| **Multi-GPU / FSDP / DeepSpeed** | Strategy Config Panel | `/api/v1/strategies` | None | None | None | `docs/known-limitations.md` | **UNSUPPORTED** (Host hardware limited) |
