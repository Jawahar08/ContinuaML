import requests
import time
import sys
import sqlite3
import os

print("=== STARTING CONTINUAL STRATEGIES (LORA ROUTER & CORESET REPLAY) INTEGRATION TEST ===")

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@continuaml.com"
ADMIN_PASS = "AdminPass123!"

# Step 1: Authenticate
print("\n[Step 1] Authenticating session (admin login)...")
login_payload = {
    "username": ADMIN_EMAIL,
    "password": ADMIN_PASS
}
login_res = requests.post(f"{BASE_URL}/auth/login", data=login_payload)
if login_res.status_code != 200:
    print(f"FAILED: Authentication failed with status {login_res.status_code}")
    sys.exit(1)

token = login_res.json().get("access_token")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
print("SUCCESS: Authenticated successfully.")

# Step 2: Trigger experiment with LoRA Router & Coreset Replay enabled
print("\n[Step 2] Launching experiment with MoE LoRA Routing (4 experts) and Active Coreset (1500 samples)...")
exp_payload = {
    "name": "Continual Strategies E2E Verification Run",
    "model_version_id": "tinyllama-1.1b-v1",
    "dataset_version_id": "dataset_triviaqa-v1",
    "strategy_id": "ewc",
    "config_id": "cfg_default",
    "protocol_id": "proto_standard",
    "seed": 42,
    "safety_gate_enabled": False,
    "dynamic_lora_routing": True,
    "lora_expert_count": 4,
    "routing_entropy_threshold": 0.75,
    "active_coreset_replay": True,
    "coreset_size": 1500,
    "selection_strategy": "herding"
}

exp_res = requests.post(f"{BASE_URL}/workspace_default/experiments", json=exp_payload, headers=headers)
if exp_res.status_code != 201:
    print(f"FAILED: Could not create experiment, status {exp_res.status_code}, response: {exp_res.text}")
    sys.exit(1)

exp_info = exp_res.json()
exp_id = exp_info["id"]
print(f"SUCCESS: Experiment launched. ID: {exp_id}")

# Step 3: Poll sqlite for job ID and fetch logs
print("\n[Step 3] Polling execution logs for Coreset coverage selection and Dynamic LoRA gating...")
strategies_verified = False
attempts = 0
max_attempts = 15

while attempts < max_attempts:
    attempts += 1
    print(f"Attempt {attempts}: querying sqlite & logs...")
    
    # Query sqlite directly to get the job_id
    db_path = os.path.abspath("continuaml.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM job WHERE experiment_id = ? AND job_type = 'fine-tune'", (exp_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        job_id = row[0]
        # Fetch logs for this job via API
        logs_res = requests.get(f"{BASE_URL}/workspace_default/jobs/{job_id}/logs", headers=headers)
        if logs_res.status_code == 200:
            logs_text = logs_res.text
            
            # Look for active coreset replay logs and lora router logs
            has_coreset_log = "Active Coreset populated with 1,500 exemplars" in logs_text
            has_lora_log = "routing_gate.weight" in logs_text
            has_epoch_router_log = "router allocation: E0:" in logs_text
            
            if has_coreset_log and has_lora_log and has_epoch_router_log:
                print("\nSUCCESS: LoRA Router gating metrics and Active Coreset coverage selection logged successfully!")
                strategies_verified = True
                break
                
    time.sleep(1.5)

if not strategies_verified:
    print("FAILED: Strategies logs were not generated/found within timeout.")
    sys.exit(1)

# Step 4: Verify experiment database fields
print("\n[Step 4] Verifying experiment configuration fields in database registry...")
res = requests.get(f"{BASE_URL}/workspace_default/experiments", headers=headers)
experiments = res.json()
target_exp = next((e for e in experiments if e["id"] == exp_id), None)

if not target_exp:
    print("FAILED: Experiment not found in list.")
    sys.exit(1)

assert target_exp["dynamic_lora_routing"] is True
assert target_exp["lora_expert_count"] == 4
assert target_exp["routing_entropy_threshold"] == 0.75
assert target_exp["active_coreset_replay"] is True
assert target_exp["coreset_size"] == 1500
assert target_exp["selection_strategy"] == "herding"

print("SUCCESS: Experiment database fields verified successfully.")
print("\n=== DYNAMIC LORA ROUTER & ACTIVE CORESET REPLAY VERIFIED SUCCESSFULLY ===")
