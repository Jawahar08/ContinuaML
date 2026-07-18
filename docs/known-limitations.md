# Known Limitations

This document lists the limitations, hardware restrictions, and missing features in the current release of **ForgetGuard AI**.

---

## 1. Hardware & Execution Constraints

### 1.1 Multi-GPU Execution
- **Limitation**: The platform is optimized for single-GPU setups (or CPU execution under local demo mode).
- **Status**: `UNSUPPORTED` for multi-GPU distribution (e.g., FSDP, DeepSpeed) in the base slice due to host hardware mapping boundaries.
- **Requirement**: Full multi-GPU integration requires configuring PyTorch Accelerate on multi-node instances.

### 1.2 Model Sizes
- **Limitation**: Running fine-tuning on consumer hardware (e.g. <16GB VRAM) for models larger than 3B parameters (like Llama 3 8B, Mistral 7B) requires quantization (QLoRA) or gradient accumulation/checkpointing.
- **Status**: Models larger than 7B are marked `UNSUPPORTED` unless quantization configurations are activated.

---

## 2. Sandbox Execution Constraints

### 2.1 File-System Access
- **Limitation**: The code evaluation sandbox does not currently enforce a full Linux gVisor/Docker container in the default Windows setup.
- **Status**: `DEMO` containment. It runs code in a separate process with time, memory, and path limits, but lacks virtual kernel sandboxing on non-Linux host operating systems.

---

## 3. Real vs. Demo Stratification
- Evaluators and strategy executors fallback to `DEMO` status when running on CPU without PyTorch/Hugging Face packages installed or when missing internet connectivity for weights download.
