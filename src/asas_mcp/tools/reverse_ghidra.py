import subprocess
import os
import json
import tempfile
import shutil

# Timeout for Ghidra analysis (seconds)
GHIDRA_TIMEOUT = 120

# Library function prefixes to filter out (noise reduction for LLM)
LIBRARY_PREFIXES = [
    "_init", "_fini", "_start", "__libc", "__do_global",
    "deregister_tm_clones", "register_tm_clones",
    "frame_dummy", "__frame_dummy_init",
    "_dl_", "__cxa_", "__gmon_start__",
    ".plt", ".got", "_ITM_", "__x86."
]

def _is_user_function(name: str) -> bool:
    """Filter out compiler/library generated functions to save LLM tokens."""
    for prefix in LIBRARY_PREFIXES:
        if name.startswith(prefix):
            return False
    return True


def analyze_binary(file_path: str) -> dict:
    """
    Run Ghidra Headless inside Docker to decompile ALL user functions.
    
    Args:
        file_path: Absolute path to the binary file on the host.
        
    Returns:
        Dictionary with 'functions' (list of {name, address, code}) and 'summary'.
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
        
    with tempfile.TemporaryDirectory() as tmp_dir:
        binary_path = os.path.join(tmp_dir, "input_binary")
        output_json = os.path.join(tmp_dir, "output.json")
        script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts"))
        
        shutil.copy2(file_path, binary_path)
            
        cmd = [
            "docker", "run", "--rm",
            "--entrypoint", "",
            "-v", f"{tmp_dir}:/data",
            "-v", f"{script_dir}:/scripts",
            "-e", "GHIDRA_OUTPUT_PATH=/data/output.json",
            "blacktop/ghidra",
            "/ghidra/support/analyzeHeadless", "/data", "temp_proj",
            "-scriptPath", "/scripts",
            "-import", "/data/input_binary",
            "-postScript", "GhidraExport.java",
            "-deleteProject"
        ]
        
        try:
            print(f"[Ghidra] Analyzing {file_path} (timeout={GHIDRA_TIMEOUT}s)...")
            result = subprocess.run(
                cmd, capture_output=True, text=True, 
                timeout=GHIDRA_TIMEOUT
            )
            
            if os.path.exists(output_json):
                with open(output_json, "r") as f:
                    raw = json.load(f)
                
                # Filter and format
                user_funcs = []
                for entry in raw:
                    name = entry.get("name", "")
                    if _is_user_function(name):
                        user_funcs.append({
                            "name": name,
                            "address": entry.get("address", "unknown"),
                            "code": entry.get("code", "")
                        })
                
                return {
                    "total_functions": len(raw),
                    "user_functions": len(user_funcs),
                    "functions": user_funcs
                }
            else:
                return {
                    "error": "Ghidra produced no output",
                    "stderr": result.stderr[-500:] if result.stderr else ""
                }
                
        except subprocess.TimeoutExpired:
            return {"error": f"Ghidra analysis timed out after {GHIDRA_TIMEOUT}s"}
        except subprocess.CalledProcessError as e:
            return {"error": "Docker Ghidra execution failed", "stderr": e.stderr[-500:] if e.stderr else ""}
        except Exception as e:
            return {"error": str(e)}


def list_functions(file_path: str) -> dict:
    """
    Lightweight: only list function names and addresses (no decompilation).
    Much faster, used for initial recon.
    """
    result = analyze_binary(file_path)
    if "error" in result:
        return result
    
    # Strip the heavy 'code' field for overview
    overview = []
    for f in result.get("functions", []):
        overview.append({"name": f["name"], "address": f["address"]})
    
    return {
        "total_functions": result["total_functions"],
        "user_functions": result["user_functions"],
        "functions": overview
    }


def decompile_function(file_path: str, function_name: str) -> dict:
    """
    Decompile a single specific function by name.
    """
    result = analyze_binary(file_path)
    if "error" in result:
        return result
    
    for f in result.get("functions", []):
        if f["name"] == function_name:
            return {"name": f["name"], "address": f["address"], "code": f["code"]}
    
    available = [f["name"] for f in result.get("functions", [])]
    return {
        "error": f"Function '{function_name}' not found",
        "available_functions": available
    }
