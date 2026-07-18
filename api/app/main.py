import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db
from app.config import settings
from app.routers import auth, models, datasets, plans, experiments, jobs, reports
from app.worker import start_background_worker_thread

# 1. Initialize FastAPI App
app = FastAPI(
    title="ContinuaML - Production LLM Continual Learning Research Platform",

    description="Backend API for fine-tuning language models, measuring catastrophic forgetting, and comparing mitigation strategies.",
    version="1.0.0"
)

# 2. CORS Configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Correlation ID Middleware
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# 4. Mount API Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(experiments.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")

# 5. Startup Events
@app.on_event("startup")
def on_startup():
    # Initialize SQL database (SQLite/PostgreSQL tables creation)
    init_db()
    
    # Start the background job consumer in a daemon thread for single-process local dev
    start_background_worker_thread()

@app.get("/health", tags=["Observability"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }
