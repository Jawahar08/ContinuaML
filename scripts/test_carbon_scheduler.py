import requests
import time
import sys

print("=== STARTING GREEN AI CARBON-AWARE SCHEDULER INTEGRATION TEST ===")

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

# Step 2: Query Carbon Forecast API
print("\n[Step 2] Querying Carbon Emissions Grid Forecast endpoint...")
forecast_res = requests.get(f"{BASE_URL}/workspace_default/carbon/forecast", headers=headers)
if forecast_res.status_code != 200:
    print(f"FAILED: Could not retrieve carbon forecast, status {forecast_res.status_code}")
    sys.exit(1)

forecast_data = forecast_res.json()
print(f"SUCCESS: Carbon forecast fetched. Sample data for hour 1: {forecast_data[0]}")

# Step 3: Trigger an experiment with Carbon Scheduler enabled
print("\n[Step 3] Launching experiment with Carbon-Aware Scheduler enabled (Limit = 250 gCO2/kWh)...")
exp_payload = {
    "name": "Green AI Carbon Deferral Verification Run",
    "model_version_id": "tinyllama-1.1b-v1",
    "dataset_version_id": "dataset_triviaqa-v1",
    "strategy_id": "ewc",
    "config_id": "cfg_default",
    "protocol_id": "proto_standard",
    "seed": 42,
    "safety_gate_enabled": False,
    "carbon_aware_enabled": True,
    "carbon_intensity_threshold": 250.0
}

exp_res = requests.post(f"{BASE_URL}/workspace_default/experiments", json=exp_payload, headers=headers)
if exp_res.status_code != 201:
    print(f"FAILED: Could not create experiment, status {exp_res.status_code}, response: {exp_res.text}")
    sys.exit(1)

exp_info = exp_res.json()
exp_id = exp_info["id"]
print(f"SUCCESS: Experiment launched. ID: {exp_id}")

# Step 4: Poll the job logs for the scheduler deferral and resumption log strings
print("\n[Step 4] Polling job execution logs for carbon-aware delay and green-window resume...")
scheduler_logs_verified = False
attempts = 0
max_attempts = 15

while attempts < max_attempts:
    attempts += 1
    print(f"Attempt {attempts}: checking execution logs...")
    
    # Get jobs for this experiment directly from sqlite3
    import sqlite3
    import os
    db_path = os.path.abspath("continuaml.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM job WHERE experiment_id = ? AND job_type = 'fine-tune'", (exp_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        job_id = row[0]
        # Fetch logs for this job
        logs_res = requests.get(f"{BASE_URL}/workspace_default/jobs/{job_id}/logs", headers=headers)
        if logs_res.status_code == 200:
            logs_text = logs_res.text
            if "Deferring execution" in logs_text and "GREEN WINDOW ACTIVE" in logs_text:
                print("\nSUCCESS: Carbon-Aware Scheduler logged deferral and clean energy window resumption successfully!")
                scheduler_logs_verified = True
                break
                
    time.sleep(1.5)

if not scheduler_logs_verified:
    print("FAILED: Carbon-aware scheduler wait and resumption logs not found within timeout.")
    sys.exit(1)

print("\n=== GREEN AI CARBON-AWARE SCHEDULER VERIFIED SUCCESSFULLY ===")
