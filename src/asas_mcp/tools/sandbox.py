import subprocess
import os
import tempfile
import logging

def run_in_sandbox(code: str, language: str = "python") -> str:
    """
    Runs untrusted code in a highly restricted Docker container.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Prepare the script file
        ext = "py" if language == "python" else "sh"
        script_name = f"script.{ext}"
        script_path = os.path.join(tmp_dir, script_name)
        
        with open(script_path, 'w') as f:
            f.write(code)
            
        # 2. Build Docker command with security constraints
        # Image: python:3.11-slim (small and safe)
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",           # NO network access
            "--memory", "128m",            # Limit memory
            "--cpus", "0.5",               # Limit CPU
            "--pids-limit", "50",          # Prevent fork bombs
            "--read-only",                 # Read-only filesystem
            "-v", f"{tmp_dir}:/mnt:ro",    # Mount script as read-only
            "--tmpfs", "/tmp:rw,size=10m", # Allow small writable /tmp
            "--tmpfs", "/run:rw,size=1m",  # Some tools need /run
            "python:3.11-slim",
            "python", f"/mnt/{script_name}"
        ]
        
        if language == "bash":
            docker_cmd[-2:] = ["bash", f"/mnt/{script_name}"]

        try:
            logging.info(f"Sandbox executing {language} code...")
            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Sandbox Error (Code {result.returncode}):\n{result.stderr}\n{result.stdout}"
        except subprocess.TimeoutExpired:
            return "Sandbox Error: Execution timed out (Limit: 15s)."
        except Exception as e:
            return f"Sandbox System Error: {str(e)}"

def run_python(code: str) -> str:
    return run_in_sandbox(code, "python")

def run_bash(code: str) -> str:
    return run_in_sandbox(code, "bash")
