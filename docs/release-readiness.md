# Release Readiness Report

This document outlines the validation criteria, pre-release checklists, and smoke test procedures for **ForgetGuard AI**.

---

## 1. Release Readiness Gate

Before tagging a version or deploying to production, the repository must pass all the following verification checkpoints:

- **Verification Check 1**: Standard unit, integration, and contract tests pass with 0 failures (`pytest`).
- **Verification Check 2**: Frontend type checks and code builds complete successfully (`npm run build`).
- **Verification Check 3**: Linting and formatting checks pass (`ruff` or `flake8` for python, `eslint` and `prettier` for frontend).
- **Verification Check 4**: Database migrations validate and execute cleanly.
- **Verification Check 5**: The deterministic demo workflow runs successfully end-to-end, producing a valid reproducibility manifest.

---

## 2. Release Checklist

- [ ] All environment variables are documented in `.env.example`.
- [ ] No hardcoded passwords, credentials, or development JWT secrets exist in code.
- [ ] Feature matrix is fully updated with current implementation statuses.
- [ ] Sandbox code execution environments verify containment rules on CPU limits.
- [ ] Database indexes exist for workspaces, experiments, jobs, and audit logs.
- [ ] Audit logs and status logs persist trace information.
