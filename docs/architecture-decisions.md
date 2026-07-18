# Architecture Decision Records (ADRs)

This document details the architectural decisions for **ForgetGuard AI**.

## ADR 01: Multi-Environment Database Strategy (SQLite + PostgreSQL)

### Context
ForgetGuard AI must support two distinct deployment paradigms:
1. Local offline development & deterministic evaluation (requiring zero database setup, zero credentials, running on a standard laptop).
2. Production enterprise deployment (requiring multi-tenant isolation, concurrent background worker processes, and high availability).

### Decision
We will use **SQLModel** (an ORM combining SQLAlchemy and Pydantic) to write database schemas once.
- **Local Dev/Demo**: The application defaults to a file-based SQLite database (`sqlite:///forgetguard.db`).
- **Production**: SQLite is swapped for PostgreSQL via the `DATABASE_URL` environment variable. Swapping is transparent to the codebase since SQLAlchemy handles dialect abstraction.

---

## ADR 02: Background Job Orchestration (Redis + Custom Light Job Queue)

### Context
ML fine-tuning, dataset verification, and benchmark evaluation are long-running tasks. We need a stateful queue supporting:
- Queueing, cancellation, retries, and job resumption.
- Storing real-time progress and incremental log outputs.
- No heavy distributed process managers when running a simple local developer demo.

### Decision
We implement a lightweight, robust **Redis-backed stateful queue** (with an **in-memory thread-safe fallback** for SQLite-only local dev environments without Redis installed).
- The queue stores job states (`queued`, `running`, `cancelling`, `cancelled`, `retrying`, `succeeded`, `failed`, `unsupported`, `quarantined`).
- Mutating endpoints verify idempotency tokens.
- Worker threads capture `sys.stdout` and write it directly to the database logs/Redis buffer.

---

## ADR 03: Workspace-Isolated Storage (Local Filesystem + S3/MinIO Adapter)

### Context
Datasets, models, and checkpoints are large binary files. They must be stored in workspace-specific paths with check-sums, quarantine options, and tenant boundary enforcement.

### Decision
We create a storage abstraction interface (`StorageProvider`) supporting:
- `save_artifact(workspace_id: str, file_path: str, content: bytes) -> str` (returns artifact URI)
- `get_artifact(workspace_id: str, uri: str) -> bytes`
- `delete_artifact(workspace_id: str, uri: str)`

Adapters:
- `LocalStorageProvider`: Stores files under a workspace subdirectory inside the repository (`gi/data/workspaces/{workspace_id}/...`).
- `S3StorageProvider`: Connects to S3 or MinIO bucket using `boto3` with presigned URLs.

---

## ADR 04: Next.js 15 Web Client & Charting

### Context
A premium user experience is required, complete with forgetting curves, radar charts, retention heatmaps, and a PDF/LaTeX article exporter.

### Decision
- **Framework**: Next.js 15 (App Router, Tailwind CSS, TypeScript, and shadcn/ui components).
- **Charting**: **Recharts** (a React charting library using SVG) is selected as the primary visual engine due to its excellent out-of-the-box reactivity and accessibility support (we also render text tables as alternatives under every chart for screen reader accessibility).
