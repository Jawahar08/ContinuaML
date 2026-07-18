# Reproducibility Guidelines & Lineage Tracking

To ensure that any machine learning training or evaluation result can be audited and repeated, **ForgetGuard AI** generates a downloadable **Reproducibility Manifest** for every completed run.

---

## 1. Reproducibility Manifest Schema

The manifest is an immutable JSON structure exported from an experiment. It tracks:

```json
{
  "manifest_version": "1.0",
  "experiment_id": "exp-uuid-12345",
  "workspace_id": "ws-uuid-abcde",
  "timestamp": "2026-07-18T00:00:00Z",
  "code_provenance": {
    "git_commit": "a1b2c3d4e5f6...",
    "branch": "main",
    "dirty": false,
    "lock_file_hash": "sha256-..."
  },
  "hardware_environment": {
    "os": "windows / linux",
    "cpu": "Intel Core i7 / AMD EPYC",
    "gpu": "NVIDIA RTX 4090 / A100",
    "vram_allocated_bytes": 25769803776,
    "cuda_version": "12.2"
  },
  "randomness_configuration": {
    "global_seed": 42,
    "pytorch_seed": 42,
    "numpy_seed": 42,
    "cuda_deterministic": true
  },
  "inputs": {
    "model": {
      "id": "model-123",
      "version": "v1.0.0",
      "huggingface_repo": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
      "checksum": "sha256-..."
    },
    "dataset": {
      "id": "dataset-456",
      "version": "v2.1",
      "preprocessing_recipe_hash": "sha256-...",
      "split_manifest": {
        "train_samples": 8000,
        "val_samples": 1000,
        "test_samples": 1000
      }
    }
  },
  "hyperparameters": {
    "strategy": "elastic_weight_consolidation",
    "learning_rate": 5e-5,
    "batch_size": 8,
    "epochs": 3,
    "ewc_lambda": 100.0
  }
}
```

---

## 2. Deterministic Seed Enforcement

Every stochastic operation in ForgetGuard AI must explicitly accept a seed parameter.
On run initialization:
1. `random.seed(config.seed)`
2. `np.random.seed(config.seed)`
3. `torch.manual_seed(config.seed)`
4. If CUDA is used:
   - `torch.cuda.manual_seed_all(config.seed)`
   - `torch.backends.cudnn.deterministic = True`
   - `torch.backends.cudnn.benchmark = False`
