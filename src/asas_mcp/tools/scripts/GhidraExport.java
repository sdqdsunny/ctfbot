// Ghidra Headless Script: Decompile and Export Functions with Addresses
// This script runs inside Ghidra's Java environment
// @category CTF-ASAS

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompiledFunction;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.FileWriter;
import java.util.Iterator;

public class GhidraExport extends GhidraScript {
    
    @Override
    public void run() throws Exception {
        println("CTF-ASAS Ghidra Export starting...");
        
        DecompInterface iface = new DecompInterface();
        iface.openProgram(currentProgram);
        
        FunctionManager fm = currentProgram.getFunctionManager();
        Iterator<Function> funcs = fm.getFunctions(true).iterator();
        
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        boolean first = true;
        int count = 0;
        
        while (funcs.hasNext()) {
            Function func = funcs.next();
            String name = func.getName();
            String addr = func.getEntryPoint().toString();
            
            // Decompile with 30s timeout per function
            DecompileResults res = iface.decompileFunction(func, 30, new ConsoleTaskMonitor());
            String code = "";
            if (res.decompileCompleted()) {
                DecompiledFunction df = res.getDecompiledFunction();
                if (df != null) {
                    code = df.getC();
                }
            }
            
            if (!first) sb.append(",");
            first = false;
            
            sb.append("{");
            sb.append("\"name\":\"").append(escapeJson(name)).append("\",");
            sb.append("\"address\":\"").append(escapeJson(addr)).append("\",");
            sb.append("\"code\":\"").append(escapeJson(code)).append("\"");
            sb.append("}");
            count++;
        }
        
        sb.append("]");
        
        String outputPath = System.getenv("GHIDRA_OUTPUT_PATH");
        if (outputPath == null || outputPath.isEmpty()) {
            outputPath = "/tmp/ghidra_output.json";
        }
        
        FileWriter fw = new FileWriter(outputPath);
        fw.write(sb.toString());
        fw.close();
        
        println("Success: Exported " + count + " functions to " + outputPath);
    }
    
    private String escapeJson(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}
