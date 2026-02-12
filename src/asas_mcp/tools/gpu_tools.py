from langchain_core.tools import tool
import subprocess
import logging
import json
import os

logger = logging.getLogger(__name__)

@tool
async def gpu_hashcat_crack(hash_value: str, hash_type: str, wordlist_path: str = "/usr/share/wordlists/rockyou.txt") -> str:
    """
    Use GPU-accelerated Hashcat to crack a hash.
    
    Args:
        hash_value: The hash string to crack.
        hash_type: Hashcat mode (e.g., '0' for MD5, '100' for SHA1, '1400' for SHA256).
        wordlist_path: Path to the wordlist file.
        
    Returns:
        The cracked password or status message.
    """
    # 0. Check if Hashcat is available
    try:
        subprocess.run(["hashcat", "--version"], check=True, capture_output=True)
    except Exception:
        return "Error: Hashcat is not installed on this node."

    # 1. Write hash to a temporary file
    hash_file = f"/tmp/hash_{hash_type}.txt"
    with open(hash_file, "w") as f:
        f.write(hash_value)

    # 2. Run Hashcat
    # -m: hash type, -a 0: straight attack (wordlist)
    # --force: sometimes needed in VMs/containers
    cmd = ["hashcat", "-m", hash_type, "-a", "0", hash_file, wordlist_path, "--force", "--potfile-disable"]
    
    logger.info(f"Running GPU Hashcat: {' '.join(cmd)}")
    try:
        # We run it and wait (CTF hashes are usually quick if solvable)
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # 3. Read result
        # Hashcat usually outputs the result to stdout when finished
        # Or we can run with --show
        show_cmd = ["hashcat", "-m", hash_type, hash_file, "--show"]
        show_process = subprocess.run(show_cmd, capture_output=True, text=True)
        
        if show_process.stdout.strip():
            return f"Success! Cracked result: {show_process.stdout.strip()}"
        else:
            return f"Hashcat finished. Password not found in wordlist. \nStderr: {process.stderr}"
            
    except Exception as e:
        return f"Error during Hashcat execution: {str(e)}"
    finally:
        if os.path.exists(hash_file):
            os.remove(hash_file)

@tool
async def gpu_status() -> str:
    """Check NVIDIA GPU status using nvidia-smi."""
    try:
        output = subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT, text=True)
        return f"GPU Status:\n{output}"
    except Exception:
        return "NVIDIA GPU or nvidia-smi not detected."
