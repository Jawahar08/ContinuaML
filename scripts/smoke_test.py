import requests
import time
import sys
import random
import string

API_BASE = "http://localhost:8000/api/v1"

def test_full_flow():
    print("=== STARTING CONTINUAML FULL PLATFORM SMOKE TEST ===")

    
    ts = int(time.time())
    email = f"e2e_researcher_{ts}@continuaml.com"

    ws_name = f"E2E_Unit_{ts}"
    model_id = f"tinyllama-e2e-{ts}"
    model_version_id = f"tinyllama-e2e-v1-{ts}"
    dataset_id = f"dataset-e2e-{ts}"
    plan_id = f"plan-e2e-{ts}"
    exp_id = f"exp-e2e-01-{ts}"
    report_id = f"report-e2e-{ts}"

    password = "".join(random.choices(string.ascii_letters + string.digits, k=12)) + "aA1!"

    # 1. Signup
    print("\n[Step 1] Creating new research user...")
    signup_url = f"{API_BASE}/auth/signup?email={email}&password={password}"
    res = requests.post(signup_url)
    if res.status_code != 201:
        print(f"FAILED: Signup returned {res.status_code} - {res.text}")
        sys.exit(1)
    ws_id = res.json()["workspace_id"]
    print(f"SUCCESS: User created. Default workspace ID: {ws_id}")

    # 2. Login
    print("\n[Step 2] Authenticating session (JWT login)...")
    login_url = f"{API_BASE}/auth/login"
    login_data = {"username": email, "password": password}
    res = requests.post(login_url, data=login_data)
    if res.status_code != 200:
        print(f"FAILED: Login returned {res.status_code} - {res.text}")
        sys.exit(1)
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("SUCCESS: Session authenticated. JWT retrieved.")

    # 3. Create Workspace
    print("\n[Step 3] Creating secondary research unit (workspace)...")
    ws_url = f"{API_BASE}/auth/workspaces?name={ws_name}"
    res = requests.post(ws_url, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Workspace creation returned {res.status_code} - {res.text}")
        sys.exit(1)
    new_ws_id = res.json()["id"]
    print(f"SUCCESS: Workspace created: {new_ws_id}")

    # 4. Register Model
    print("\n[Step 4] Registering LLM in registry...")
    model_url = f"{API_BASE}/{new_ws_id}/models"
    model_payload = {
        "id": model_id,
        "name": "TinyLlama E2E Test",
        "architecture": "LlamaForCausalLM",
        "param_count": 1100000000,
        "context_length": 2048,
        "license": "Apache-2.0",
        "source": "HuggingFace"
    }
    res = requests.post(model_url, json=model_payload, headers=headers)
    if res.status_code != 201:
        print(f"FAILED: Model registration returned {res.status_code} - {res.text}")
        sys.exit(1)
    print("SUCCESS: Model registered.")

    # 5. Create Model Version
    print("\n[Step 5] Tagging model version...")
    version_url = f"{API_BASE}/{new_ws_id}/models/{model_id}/versions"
    version_payload = {
        "id": model_version_id,
        "model_id": model_id,
        "version": "1.0.0",
        "download_status": "ready"
    }
    res = requests.post(version_url, json=version_payload, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Version creation returned {res.status_code} - {res.text}")
        sys.exit(1)
    print("SUCCESS: Model version tagged.")

    # 6. Create Model Card
    print("\n[Step 6] Saving model card spec...")
    card_url = f"{API_BASE}/{new_ws_id}/models/{model_id}/card"
    card_payload = {
        "intended_use": "E2E verification runs",
        "limitations": "CPU testing boundaries",
        "license_restrictions": "None",
        "evaluation_summary": "Passed initial diagnostics"
    }
    res = requests.post(card_url, json=card_payload, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Card creation returned {res.status_code} - {res.text}")
        sys.exit(1)
    print("SUCCESS: Model card populated.")

    # 7. Register Dataset
    print("\n[Step 7] Creating dataset registry entry...")
    ds_url = f"{API_BASE}/{new_ws_id}/datasets"
    ds_payload = {
        "id": dataset_id,
        "name": "E2E Bench Dataset",
        "source": "HuggingFace",
        "license": "MIT"
    }
    res = requests.post(ds_url, json=ds_payload, headers=headers)
    if res.status_code != 201:
        print(f"FAILED: Dataset registry returned {res.status_code} - {res.text}")
        sys.exit(1)
    print("SUCCESS: Dataset registry entry created.")

    # 8. Import/Upload Dataset
    print("\n[Step 8] Importing dataset contents (Simulating file upload)...")
    import_url = f"{API_BASE}/{new_ws_id}/datasets/{dataset_id}/import?version_str=1.0"
    files = {"file": ("e2e_dataset.csv", b"question,answer\nWhat is 5+5?,10\n")}
    res = requests.post(import_url, files=files, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Dataset import returned {res.status_code} - {res.text}")
        sys.exit(1)
    import_data = res.json()
    job_id = import_data["job_id"]
    ds_version_id = import_data["dataset_version_id"]
    print(f"SUCCESS: Import file accepted. Validation job ID: {job_id}")

    # 9. Wait for validation job
    print(f"\n[Step 9] Waiting for background validation job {job_id} to finish...")
    job_url = f"{API_BASE}/{new_ws_id}/jobs/{job_id}"
    for _ in range(10):
        job_res = requests.get(job_url, headers=headers)
        if job_res.status_code == 200:
            status = job_res.json()["status"]
            print(f"Current Job Status: {status} (Progress: {job_res.json()['progress']}%)")
            if status == "succeeded":
                print("SUCCESS: Dataset validation succeeded.")
                break
            elif status in ["failed", "cancelled"]:
                print("FAILED: Job terminated unsuccessfully.")
                sys.exit(1)
        time.sleep(1)
    else:
        print("FAILED: Job validation timeout.")
        sys.exit(1)

    # 10. Research Plan creation
    print("\n[Step 10] Formulating research plan & planned runs...")
    plan_url = f"{API_BASE}/{new_ws_id}/plans"
    plan_payload = {
        "id": plan_id,
        "name": "E2E Mitigation Study",
        "hypothesis": "EWC performs better than direct FT",
        "baseline_model_id": model_id,
        "target_dataset_id": dataset_id
    }
    res = requests.post(plan_url, json=plan_payload, headers=headers)
    if res.status_code != 201:
        print(f"FAILED: Plan creation returned {res.status_code} - {res.text}")
        sys.exit(1)
    print("SUCCESS: Research plan created.")

    # Generate planned runs
    runs_url = f"{API_BASE}/{new_ws_id}/plans/{plan_id}/runs"
    res = requests.get(runs_url, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Plan runs retrieval returned {res.status_code} - {res.text}")
        sys.exit(1)
    print(f"SUCCESS: Planned runs generated: {[r['config_summary'] for r in res.json()]}")

    # 11. Launch Experiment
    print("\n[Step 11] Launching training and evaluation experiment...")
    exp_url = f"{API_BASE}/{new_ws_id}/experiments"
    exp_payload = {
        "id": exp_id,
        "name": "E2E Fine-Tune EWC",
        "model_version_id": model_version_id,
        "dataset_version_id": ds_version_id,
        "strategy_id": "ewc",
        "config_id": "cfg_default",
        "protocol_id": "proto_standard",
        "seed": 42
    }
    res = requests.post(exp_url, json=exp_payload, headers=headers)
    if res.status_code != 201:
        print(f"FAILED: Experiment launch returned {res.status_code} - {res.text}")
        sys.exit(1)
    print("SUCCESS: Experiment launched. Background jobs registered.")

    # 12. Retrieve Reproducibility Manifest
    print("\n[Step 12] Querying reproducibility manifest...")
    manifest_url = f"{API_BASE}/{new_ws_id}/experiments/{exp_id}/reproducibility"
    # Allow some seconds for jobs to complete and generate manifest lineage
    time.sleep(8)
    res = requests.get(manifest_url, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Manifest retrieval returned {res.status_code} - {res.text}")
        sys.exit(1)
    manifest = res.json()
    print("SUCCESS: Reproducibility Manifest downloaded:")
    print(f" - Reproducibility Hash: {manifest.get('reproducibility_hash')}")
    print(f" - Base Model Architecture: {manifest['inputs']['model']['architecture']}")

    # 13. Academic Report creation
    print("\n[Step 13] Generating research report draft...")
    report_url = f"{API_BASE}/{new_ws_id}/reports"
    report_payload = {
        "id": report_id,
        "title": "E2E Validation Paper",
        "abstract": "E2E abstract testing verification framework"
    }
    res = requests.post(report_url, json=report_payload, headers=headers)
    if res.status_code != 201:
        print(f"FAILED: Report creation returned {res.status_code} - {res.text}")
        sys.exit(1)
    print("SUCCESS: Academic report draft saved.")

    print("\n=== ALL PLATFORM FLOW SYSTEMS OPERATE SUCCESSFULLY (100% DONE) ===")

if __name__ == "__main__":
    test_full_flow()
