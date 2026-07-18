import os
import shutil
import hashlib
from typing import Tuple
from app.config import settings

class StorageProvider:
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_workspace_path(self, workspace_id: str, category: str) -> str:
        # Sanitize workspace_id to prevent path traversal
        clean_ws = os.path.basename(workspace_id)
        path = os.path.join(self.base_dir, clean_ws, category)
        os.makedirs(path, exist_ok=True)
        return path

    def save_artifact(self, workspace_id: str, category: str, filename: str, content: bytes) -> Tuple[str, str, int]:
        """Saves a file, returning its storage URI, checksum, and size in bytes."""
        ws_path = self._get_workspace_path(workspace_id, category)
        # Sanitize filename
        safe_filename = os.path.basename(filename)
        dest_path = os.path.join(ws_path, safe_filename)
        
        with open(dest_path, "wb") as f:
            f.write(content)
            
        checksum = hashlib.sha256(content).hexdigest()
        size_bytes = len(content)
        uri = f"local://{workspace_id}/{category}/{safe_filename}"
        return uri, checksum, size_bytes

    def get_artifact(self, workspace_id: str, category: str, filename: str) -> bytes:
        ws_path = self._get_workspace_path(workspace_id, category)
        safe_filename = os.path.basename(filename)
        src_path = os.path.join(ws_path, safe_filename)
        
        if not os.path.exists(src_path):
            raise FileNotFoundError("Artifact not found")
            
        with open(src_path, "rb") as f:
            return f.read()

    def delete_artifact(self, workspace_id: str, category: str, filename: str):
        ws_path = self._get_workspace_path(workspace_id, category)
        safe_filename = os.path.basename(filename)
        src_path = os.path.join(ws_path, safe_filename)
        if os.path.exists(src_path):
            os.remove(src_path)

storage_provider = StorageProvider()
