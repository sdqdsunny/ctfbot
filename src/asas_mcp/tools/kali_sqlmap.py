import subprocess
import shlex
from typing import Optional

async def run_sqlmap_scan(url: str, params: Optional[str] = None) -> str:
    """
    Execute sqlmap inside the Kali Docker container against a target URL.
    
    Args:
        url: The target URL to scan.
        params: Optional extra parameters for sqlmap (e.g. --batch --dump).
        
    Returns:
        The standard output from the sqlmap execution.
    """
    cmd = [
        "docker", "exec", "ctfbot-kali", 
        "sqlmap", "-u", url, "--batch", "--random-agent"
    ]
    
    if params:
        # Be careful with shell injection here in a real scenario
        # Ideally, validate params or use structured args
        extra_args = shlex.split(params)
        cmd.extend(extra_args)
        
    try:
        # Run synchronous subprocess in executor to avoid blocking async loop
        # For simplicity in this demo, we use basic subprocess.run
        # In production, use asyncio.create_subprocess_exec
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300 # 5 minute timeout
        )
        
        if result.returncode != 0:
            return f"SQLMap Error: {result.stderr}"
            
        return result.stdout
        
    except subprocess.TimeoutExpired:
        return "Error: SQLMap scan timed out after 5 minutes."
    except Exception as e:
        return f"Error executing SQLMap: {str(e)}"
