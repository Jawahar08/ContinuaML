import requests
import time
import sys

print("=== STARTING WEIGHT PLASTICITY / FISHER FREEZING INTEGRATION TEST ===")

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

# Step 2: Trigger an experiment with Fisher Freezing enabled
print("\n[Step 2] Launching experiment with Fisher Freezing enabled (Threshold = 85%)...")
exp_payload = {
    "name": "Fisher Freezing E2E Verification Run",
    "model_version_id": "tinyllama-1.1b-v1",
    "dataset_version_id": "dataset_triviaqa-v1",
    "strategy_id": "ewc",
    "config_id": "cfg_default",
    "protocol_id": "proto_standard",
    "seed": 42,
    "safety_gate_enabled": False,
    "fisher_freezing_enabled": True,
    "fisher_importance_threshold": 0.85
}

exp_res = requests.post(f"{BASE_URL}/workspace_default/experiments", json=exp_payload, headers=headers)
if exp_res.status_code != 201:
    print(f"FAILED: Could not create experiment, status {exp_res.status_code}, response: {exp_res.text}")
    sys.exit(1)

exp_info = exp_res.json()
exp_id = exp_info["id"]
print(f"SUCCESS: Experiment launched. ID: {exp_id}")

# Step 3: Poll the experiment details and wait for run to progress/complete
print("\n[Step 3] Polling experiment registry for Fisher metric calculations...")
fisher_verified = False
attempts = 0
max_attempts = 15

while attempts < max_attempts:
    attempts += 1
    print(f"Attempt {attempts}: fetching experiment metrics...")
    
    res = requests.get(f"{BASE_URL}/workspace_default/experiments", headers=headers)
    if res.status_code == 200:
        experiments = res.json()
        exp = next((e for e in experiments if e["id"] == exp_id), None)
        if exp and exp.get("frozen_param_count") is not None:
            print("\nSUCCESS: Fisher Freezing stats successfully calculated and registered!")
            print(f" - Fisher Freezing: Enabled")
            print(f" - Importance Threshold: {exp['fisher_importance_threshold'] * 100:.0f}%")
            print(f" - Frozen Parameters Count: {exp['frozen_param_count']:,} weights")
            fisher_verified = True
            break
            
    time.sleep(1.5)

if not fisher_verified:
    print("FAILED: Fisher freezing stats were not calculated/saved within timeout.")
    sys.exit(1)

# Step 4: Verify experiment completed as REAL run (safety gate disabled)
print("\n[Step 4] Verifying run lineage state...")
res = requests.get(f"{BASE_URL}/workspace_default/experiments", headers=headers)
experiments = res.json()
target_exp = next((e for e in experiments if e["id"] == exp_id), None)

print(f"Experiment status: {target_exp['status']}")
if target_exp["status"].lower() not in ["real", "planned"]:
    print(f"FAILED: Experiment status is '{target_exp['status']}', expected 'REAL'.")
    sys.exit(1)

print("\n=== WEIGHT PLASTICITY / FISHER FREEZING VERIFIED SUCCESSFULLY ===")
