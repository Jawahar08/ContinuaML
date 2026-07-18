import subprocess
import tempfile
import os
import sys
from typing import Dict, Any
from app.config import settings

class SandboxResult:
    def __init__(self, stdout: str, stderr: str, returncode: int, timeout_expired: bool):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.timeout_expired = timeout_expired

def execute_code_sandboxed(code: str) -> SandboxResult:
    """Executes untrusted python code in an isolated subprocess with limits."""
    # Write code to a temporary file in an isolated directory
    with tempfile.TemporaryDirectory() as temp_dir:
        code_file = os.path.join(temp_dir, "unsafe_script.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)
            
        # Clean environment to prevent access to system keys and configuration
        clean_env = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),  # Required for python on Windows
            "PATH": os.environ.get("PATH", ""),
        }
        
        try:
            # Execute subprocess with timeout
            process = subprocess.Popen(
                [sys.executable, code_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=clean_env,
                cwd=temp_dir,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=settings.SANDBOX_TIMEOUT_SEC)
            return SandboxResult(
                stdout=stdout,
                stderr=stderr,
                returncode=process.returncode,
                timeout_expired=False
            )
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return SandboxResult(
                stdout=stdout,
                stderr=stderr,
                returncode=-1,
                timeout_expired=True
            )
        except Exception as e:
            return SandboxResult(
                stdout="",
                stderr=str(e),
                returncode=-2,
                timeout_expired=False
            )
