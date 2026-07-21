from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session
from typing import Any
import datetime
import math
from app.db import get_db
from app.models import WorkspaceRole
from app.auth import WorkspaceAuth

router = APIRouter(prefix="/{workspace_id}/carbon", tags=["Green AI Scheduler"])

def require_viewer(workspace_id: str, auth=Depends(WorkspaceAuth(WorkspaceRole.VIEWER))):
    return auth

@router.get("/forecast", response_model=Any)
def get_carbon_forecast(
    workspace_id: str,
    auth=Depends(require_viewer),
    db: Session = Depends(get_db)
):
    base_time = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    forecast = []
    
    # Generate deterministic mock curve based on hour of day
    # Peak at 19:00 (7 PM), low at 03:00 (3 AM) and 12:00 (midday solar)
    for hour in range(24):
        target_time = base_time + datetime.timedelta(hours=hour)
        hour_val = target_time.hour
        
        # Simulated double peak carbon curve
        intensity = 220 + 80 * math.sin((hour_val - 8) * math.pi / 6) + 40 * math.cos((hour_val - 2) * math.pi / 12)
        intensity = max(90.0, min(420.0, intensity))
        
        forecast.append({
            "timestamp": target_time.isoformat() + "Z",
            "hour": target_time.strftime("%H:%M"),
            "carbon_intensity": round(intensity, 1),
            "source": "solar" if hour_val in range(10, 16) else ("wind" if hour_val in range(0, 6) else "grid_mix")
        })
        
    return jsonable_encoder(forecast)
