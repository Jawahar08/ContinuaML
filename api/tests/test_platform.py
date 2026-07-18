import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from app.main import app
from app.db import get_db, init_db
from app.auth import get_password_hash
from app.models import User, Workspace, Membership, WorkspaceRole, ContinualLearningStrategy
from app.sandbox import execute_code_sandboxed

# Setup an in-memory SQLite database for tests
DATABASE_URL = "sqlite:///test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session):
    def get_db_override():
        return session
    app.dependency_overrides[get_db] = get_db_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_signup_and_login(client, session):
    # Test Signup
    email = "test@continuaml.com"
    signup_resp = client.post(f"/api/v1/auth/signup?email={email}&password=TestPass123!")
    assert signup_resp.status_code == 201
    
    # Test Duplicate Signup
    signup_dup = client.post(f"/api/v1/auth/signup?email={email}&password=TestPass123!")
    assert signup_dup.status_code == 400
    
    # Test Login
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "TestPass123!"}
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()
    assert login_resp.json()["token_type"] == "bearer"

def test_rbac_boundaries(client, session):
    # Register 2 users
    u1_email = "admin@continuaml.com"
    u2_email = "viewer@continuaml.com"
    
    client.post(f"/api/v1/auth/signup?email={u1_email}&password=AdminPass123!")
    client.post(f"/api/v1/auth/signup?email={u2_email}&password=ViewerPass123!")
    
    # Login admin
    admin_login = client.post("/api/v1/auth/login", data={"username": u1_email, "password": "AdminPass123!"})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create workspace
    ws_resp = client.post("/api/v1/auth/workspaces?name=WorkspaceOne", headers=admin_headers)
    print("WORKSPACE RESPONSE:", ws_resp.json())
    assert ws_resp.status_code == 200, f"Create workspace failed: {ws_resp.status_code} - {ws_resp.json()}"
    ws_id = ws_resp.json()["id"]


    
    # Viewers shouldn't be able to register models. Login viewer.
    viewer_login = client.post("/api/v1/auth/login", data={"username": u2_email, "password": "ViewerPass123!"})
    viewer_token = viewer_login.json()["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    
    # Viewer tries to post to model registry (should fail with 403 Forbidden since not member of WorkspaceOne)
    model_payload = {
        "id": "tinyllama-1.1b",
        "name": "TinyLlama",
        "architecture": "LlamaForCausalLM",
        "param_count": 1100000000,
        "context_length": 2048,
        "license": "Apache-2.0",
        "source": "HuggingFace"
    }
    
    res = client.post(f"/api/v1/{ws_id}/models", json=model_payload, headers=viewer_headers)
    assert res.status_code == 403  # Forbidden
    
    # Admin tries to post (should succeed since creator is Admin)
    res_admin = client.post(f"/api/v1/{ws_id}/models", json=model_payload, headers=admin_headers)
    assert res_admin.status_code == 201

def test_code_sandbox():
    # Simple math task
    code = "x = 5 + 10\nprint(f'Result: {x}')"
    res = execute_code_sandboxed(code)
    assert res.returncode == 0
    assert "Result: 15" in res.stdout
    assert not res.timeout_expired
    
    # Infinite loop task
    infinite_code = "import time\nwhile True:\n    time.sleep(0.1)"
    res_inf = execute_code_sandboxed(infinite_code)
    assert res_inf.timeout_expired
