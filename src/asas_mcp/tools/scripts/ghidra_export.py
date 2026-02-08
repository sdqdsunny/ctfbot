# Ghidra Headless Script: Decompile and Export Functions
# This script runs inside Ghidra's Jython environment

from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
import json
import os

def run():
    # Get current program info
    program = currentProgram
    name = program.getName()
    print("Analyzing program: " + name)
    
    # Initialize decompiler
    iface = DecompInterface()
    iface.openProgram(program)
    
    results = {}
    
    # Iterate through all functions
    fm = program.getFunctionManager()
    funcs = fm.getFunctions(True) # True for forward
    
    for func in funcs:
        func_name = func.getName()
        # Decompile
        res = iface.decompileFunction(func, 0, ConsoleTaskMonitor())
        if res.decompileCompleted():
            results[func_name] = res.getDecompiledFunction().getC()
            
    # Save to a fixed location in the container/volume
    # The MCP tool will pick it up
    try:
        output_path = os.environ.get("GHIDRA_OUTPUT_PATH", "/tmp/ghidra_output.json")
        with open(output_path, 'w') as f:
            json.dump(results, f)
        print("Success: Exported " + str(len(results)) + " functions to " + output_path)
    except Exception as e:
        print("Error saving results: " + str(e))

if __name__ == "__main__":
    run()
