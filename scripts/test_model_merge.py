import requests
import time
import sys

API_BASE = "http://localhost:8000/api/v1"
WS_ID = "workspace_default"

def test_model_merge():
    print("=== STARTING MODEL MERGING PLAYGROUND INTEGRATION TEST ===")
    
    # 1. Login
    print("\n[Step 1] Authenticating session (admin login)...")
    login_url = f"{API_BASE}/auth/login"
    login_data = {"username": "admin@continuaml.com", "password": "AdminPass123!"}
    res = requests.post(login_url, data=login_data)
    if res.status_code != 200:
        print(f"FAILED: Login returned {res.status_code} - {res.text}")
        sys.exit(1)
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("SUCCESS: Authenticated successfully.")

    # 2. Trigger Model Merge
    print("\n[Step 2] Triggering model merge...")
    merge_url = f"{API_BASE}/{WS_ID}/models/merge"
    merge_payload = {
        "name": "E2E-Merged-TinyLlama-Phi-SLERP",
        "parent_a_version_id": "tinyllama-1.1b-v1",
        "parent_b_version_id": "phi-2-v1",
        "merge_method": "slerp",
        "merge_ratio": 0.3
    }
    res = requests.post(merge_url, json=merge_payload, headers=headers)
    print(f"Merge API response status: {res.status_code}")
    print(f"Merge API response body: {res.text}")
    if res.status_code != 201:
        print(f"FAILED: Merge request returned {res.status_code} - {res.text}")
        sys.exit(1)
    
    merge_info = res.json()
    merge_id = merge_info["id"]
    job_id = merge_info["job_id"]
    print(f"SUCCESS: Merge triggered. Merge ID: {merge_id}, Job ID: {job_id}")

    # 3. Poll Merge Status
    print("\n[Step 3] Polling merge progress...")
    status_url = f"{API_BASE}/{WS_ID}/models/merges/{merge_id}"
    
    max_attempts = 15
    for attempt in range(max_attempts):
        res = requests.get(status_url, headers=headers)
        if res.status_code != 200:
            print(f"FAILED: Status check returned {res.status_code}")
            sys.exit(1)
            
        data = res.json()
        merge = data["merge"]
        logs = data["logs"]
        
        status = merge["status"]
        print(f"Attempt {attempt + 1}: status = {status}")
        
        if status == "succeeded":
            print("\nSUCCESS: Merge job completed successfully!")
            print("\n--- JOB LOGS ---")
            for log in logs:
                print(f"[{log.get('level', 'INFO')}] {log.get('content')}")
            print("----------------")
            break
        elif status == "failed":
            print(f"FAILED: Merge job failed. Logs: {logs}")
            sys.exit(1)
            
        time.sleep(1.0)
    else:
        print("FAILED: Merge job timed out.")
        sys.exit(1)

    # 4. Verify Model Registry
    print("\n[Step 4] Verifying merged model is registered...")
    models_url = f"{API_BASE}/{WS_ID}/models"
    res = requests.get(models_url, headers=headers)
    if res.status_code != 200:
        print(f"FAILED: Listing models returned {res.status_code}")
        sys.exit(1)
        
    models = res.json()
    merged_models = [m for m in models if "Merged" in m["name"]]
    
    if len(merged_models) == 0:
        print("FAILED: Merged model was not found in registry.")
        sys.exit(1)
        
    print(f"SUCCESS: Found merged model in registry:")
    for m in merged_models:
        print(f" - Model ID: {m['id']}, Name: {m['name']}, Architecture: {m['architecture']}")

    print("\n=== ALL PLAYGROUND MERGE FLOWS VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_model_merge()
