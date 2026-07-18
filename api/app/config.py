import os
try:
    from pydantic_settings import BaseSettings
except ImportError:
    BaseSettings = object


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "continuaml_secret_key_change_me_in_production_12345!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours for dev convenience
    
    # Database URL: defaults to SQLite inside workspace
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///c:/Users/cjawa/Documents/Codex/2026-07-18/gi/continuaml.db"
    )
    
    # Redis URL for job worker coordination
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Storage Directory for datasets/checkpoints/artifacts
    STORAGE_DIR: str = os.getenv(
        "STORAGE_DIR", 
        "c:/Users/cjawa/Documents/Codex/2026-07-18/gi/data"
    )
    
    # Code Sandbox boundaries
    SANDBOX_TIMEOUT_SEC: int = int(os.getenv("SANDBOX_TIMEOUT_SEC", "5"))
    SANDBOX_MAX_MEMORY_MB: int = int(os.getenv("SANDBOX_MAX_MEMORY_MB", "256"))

settings = Settings()
