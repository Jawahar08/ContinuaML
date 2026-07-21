import requests
import time
import sys

print("=== STARTING AUTO-ROLLBACK SAFETY GATE INTEGRATION TEST ===")

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

# Step 2: Trigger an experiment with safety gate enabled
print("\n[Step 2] Launching experiment with strict safety limits (max_forgetting = 5%)...")
exp_payload = {
    "name": "Safety Gate Violation E2E Test",
    "model_version_id": "tinyllama-1.1b-v1",
    "dataset_version_id": "dataset_triviaqa-v1",
    "strategy_id": "ewc",
    "config_id": "cfg_default",
    "protocol_id": "proto_standard",
    "seed": 42,
    "safety_gate_enabled": True,
    "max_forgetting_threshold": 0.05,
    "min_accuracy_threshold": 0.50
}

exp_res = requests.post(f"{BASE_URL}/workspace_default/experiments", json=exp_payload, headers=headers)
if exp_res.status_code != 201:
    print(f"FAILED: Could not create experiment, status {exp_res.status_code}, response: {exp_res.text}")
    sys.exit(1)

exp_info = exp_res.json()
print(f"DEBUG: Response body is: {exp_info}")
exp_id = exp_info.get("id")
if not exp_id:
    print(f"FAILED: 'id' key is missing from response: {exp_info}")
    sys.exit(1)
print(f"SUCCESS: Experiment launched. ID: {exp_id}")

# Step 3: Poll the safety-events endpoint and wait for gate trigger
print("\n[Step 3] Polling safety-events endpoint for gate breach alerts...")
gate_triggered = False
attempts = 0
max_attempts = 15

while attempts < max_attempts:
    attempts += 1
    print(f"Attempt {attempts}: checking safety events...")
    
    events_res = requests.get(f"{BASE_URL}/workspace_default/experiments/{exp_id}/safety-events", headers=headers)
    if events_res.status_code == 200:
        events = events_res.json()
        if len(events) > 0:
            print("\nSUCCESS: Safety gate event detected!")
            for evt in events:
                print(f" - Metric: {evt['metric_name']}")
                print(f" - Threshold Limit: {evt['threshold_value']}")
                print(f" - Observed Value: {evt['observed_value']:.4f}")
                print(f" - Action Taken: {evt['action_taken']}")
            gate_triggered = True
            break
            
    time.sleep(1.5)

if not gate_triggered:
    print("FAILED: Safety gate did not trigger within timeout.")
    sys.exit(1)

# Step 4: Verify experiment status is FAILED (rolled back/halted)
print("\n[Step 4] Verifying final experiment status in registry...")
exps_res = requests.get(f"{BASE_URL}/workspace_default/experiments", headers=headers)
experiments = exps_res.json()
target_exp = next((e for e in experiments if e["id"] == exp_id), None)

if not target_exp:
    print("FAILED: Launched experiment not found in list.")
    sys.exit(1)

print(f"Experiment Status in database: {target_exp['status']}")
if target_exp["status"].lower() != "failed":
    print(f"FAILED: Experiment status is '{target_exp['status']}', expected 'FAILED' (case-insensitive).")
    sys.exit(1)

print("\n=== AUTO-ROLLBACK SAFETY GATE VERIFIED SUCCESSFULLY ===")
