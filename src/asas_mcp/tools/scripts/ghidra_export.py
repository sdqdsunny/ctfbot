# Ghidra Headless Script: Decompile and Export Functions with Addresses
# This script runs inside Ghidra's Jython environment

from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
import json
import os

def run():
    program = currentProgram
    name = program.getName()
    print("Analyzing program: " + name)
    
    iface = DecompInterface()
    iface.openProgram(program)
    
    results = []
    
    fm = program.getFunctionManager()
    funcs = fm.getFunctions(True)
    
    for func in funcs:
        func_name = func.getName()
        func_addr = str(func.getEntryPoint())
        
        # Decompile
        res = iface.decompileFunction(func, 30, ConsoleTaskMonitor())  # 30s per function
        code = ""
        if res.decompileCompleted():
            decomp = res.getDecompiledFunction()
            if decomp:
                code = decomp.getC()
        
        results.append({
            "name": func_name,
            "address": func_addr,
            "code": code
        })
            
    # Save output
    try:
        output_path = os.environ.get("GHIDRA_OUTPUT_PATH", "/tmp/ghidra_output.json")
        with open(output_path, 'w') as f:
            json.dump(results, f)
        print("Success: Exported " + str(len(results)) + " functions to " + output_path)
    except Exception as e:
        print("Error saving results: " + str(e))

if __name__ == "__main__":
    run()
