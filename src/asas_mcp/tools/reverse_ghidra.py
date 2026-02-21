import subprocess
import os
import json
import base64
import tempfile
import logging

def analyze_binary(file_path: str) -> dict:
    """
    Run Ghidra Headless inside Docker to decompile a binary.
    
    Args:
        file_path: Absolute path to the binary file on the host.
        
    Returns:
        Dictionary of function names and their decompiled C code.
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
        
    # 1. Create temporary workspace
    with tempfile.TemporaryDirectory() as tmp_dir:
        binary_path = os.path.join(tmp_dir, "input_binary")
        output_json = os.path.join(tmp_dir, "output.json")
        script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts"))
        
        # Copy binary file
        import shutil
        shutil.copy2(file_path, binary_path)
            
        # 2. Build Docker Command
        # We use blacktop/ghidra which is a well-maintained image
        # Command syntax: analyzeHeadless <project_path> <project_name> -import <file> -postScript <script_path>
        
        # Mounts:
        # - tmp_dir -> /data
        # - script_dir -> /scripts
        
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{tmp_dir}:/data",
            "-v", f"{script_dir}:/scripts",
            "-e", "GHIDRA_OUTPUT_PATH=/data/output.json",
            "blacktop/ghidra",
            "analyzeHeadless", "/data", "temp_proj",
            "-import", "/data/input_binary",
            "-postScript", "/scripts/ghidra_export.py",
            "-deleteProject" # Clean up project files after run
        ]
        
        try:
            print(f"Running Ghidra analysis on {file_path}...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # 3. Read result
            if os.path.exists(output_json):
                with open(output_json, "r") as f:
                    return json.load(f)
            else:
                return {"error": "Ghidra analysis failed to produce output", "stdout": result.stdout, "stderr": result.stderr}
                
        except subprocess.CalledProcessError as e:
            return {
                "error": "Docker Ghidra execution failed",
                "stderr": e.stderr,
                "stdout": e.stdout
            }
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Test with a simple dummy base64 (this will likely fail inside Ghidra but tests the docker flow)
    # In real use, we'd pass a real ELF/PE
    pass
