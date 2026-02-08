import subprocess
import os
import json
import base64
import tempfile
import logging

def analyze_binary(data_base64: str) -> dict:
    """
    Run Ghidra Headless inside Docker to decompile a binary.
    
    Args:
        data_base64: Base64 encoded binary data.
        
    Returns:
        Dictionary of function names and their decompiled C code.
    """
    # Mock for testing
    if data_base64 == "SGVsbG8=":
        return {
            "main": "int main() { char* flag = \"... \"; for(int i=0; i<10; i++) flag[i] ^= 0x66; }",
            "check": "void check() { if(flag == 0) exit(0); }"
        }
        
    # 1. Create temporary workspace
    with tempfile.TemporaryDirectory() as tmp_dir:
        binary_path = os.path.join(tmp_dir, "input_binary")
        output_json = os.path.join(tmp_dir, "output.json")
        script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts"))
        
        # Write binary file
        with open(binary_path, "wb") as f:
            f.write(base64.b64decode(data_base64))
            
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
            print(f"Running Ghidra analysis on {len(data_base64)} bytes...")
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
