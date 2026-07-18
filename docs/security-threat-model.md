# Security Threat Model & Data Governance Policy

This document outlines the security posture, threat vectors, and mitigation rules for **ForgetGuard AI**.

---

## 1. Threat Matrix & Mitigations

### Threat 1: Remote Code Execution via Untrusted Models (Pickle Bombing)
- **Vector**: Hugging Face models containing standard PyTorch checkpoints (`.bin`/`pytorch_model.bin`) utilize Python's `pickle` serialization. Malicious model files can execute arbitrary code upon deserialization (`pickle.load`).
- **Mitigation**: 
  1. Default loading strictly to `safetensors` format, which is fully serialization-safe and does not support arbitrary code execution.
  2. Block PyTorch standard pickle weights by default unless an administrator explicitly records a signed exception.
  3. Disable `trust_remote_code=True` in Hugging Face loaders. Any model requiring remote code must be vetted and whitelisted.

### Threat 2: Host File System Access via Code Evaluation (HumanEval / MBPP)
- **Vector**: Benchmarking coding abilities of models requires executing model-generated Python scripts. A model could generate code that deletes files, reads environment variables, or contacts external servers.
- **Mitigation**:
  1. Code execution is isolated using a dedicated subprocess boundary.
  2. Implement strict resource limits (limits on maximum VRAM, RAM, CPU time, and file size limits).
  3. Filesystem isolation: The subprocess is run in a temp directory with zero access to API environment variables, secrets, or system resources.
  4. Network isolation: Subprocess network interfaces are disabled during run.

### Threat 3: Tenant Boundary Leakage (Multi-Tenancy)
- **Vector**: Users in Workspace A access or modify datasets, models, or experiment metrics in Workspace B.
- **Mitigation**:
  1. All database queries accessing models, datasets, plans, or experiments must filter by `workspace_id`.
  2. JWT claims contain active roles (`Admin`, `Researcher`, `Viewer`) scoped strictly to a specific workspace ID.
  3. API middleware validates the path's `workspace_id` against the JWT token payload.

---

## 2. PII Validation & Contamination Rules

### 2.1 PII Check
Before importing any dataset, the platform scans text fields for:
- Email addresses (via standard regex)
- Phone numbers (via standard regex)
- Credit card sequences
- IP addresses
Any file containing suspicious content is flagged and put in `QUARANTINED` status with details provided in the dataset validation card.

### 2.2 Leakage/Contamination Check
- **Vector**: Validation or test dataset overlap with the training set.
- **Mitigation**: The import job performs exact match and near-duplicate (MinHash LSH / n-gram overlap) calculations between training and evaluation splits, generating a contamination percentage. If duplicate rates exceed 5%, the dataset is flagged.
