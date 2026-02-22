from typing import List, Any
from ..graph.workflow import create_react_agent_graph

def create_pwn_agent(llm, tools: List[Any]):
    """
    Creates a specialized PwnAgent for binary exploitation tasks.
    
    This agent is equipped with tools for:
    - Protection analysis (checksec)
    - Static analysis (ghidra)
    - Dynamic debugging (gdb/gef)
    - Exploit generation (pwntools)
    """
    system_prompt = (
        "## PWN EXPLOITATION SPECIALIST\n"
        "You are an elite Pwn Engineer. Your goal is to exploit binary vulnerabilities.\n\n"
        
        "### PWN SOP (Standard Operating Procedure)\n"
        "1. **RECON**: Use `kali_checksec` to check for NX, ASLR, PIE, Canary. Use `kali_file` for architecture.\n"
        "2. **STATIC ANALYSIS**: Use `ghidra_list_functions` and `ghidra_decompile_function` to find vulnerabilities (gets, scanf, strcpy, etc.).\n"
        "3. **VULN DISCOVERY**: Identify the exact buffer size and return address offset.\n"
        "4. **DYNAMIC VALIDATION**: If unsure of the offset, use `kali_pwn_cyclic(length=200)` to generate a pattern, run it in `kali_pwn_gdb` (e.g., 'run < pattern'), and check the crashing address.\n"
        "5. **EXPLOIT DEV**: Write a Python script using `pwntools`. Execute it with `sandbox_execute` or `kali_exec`.\n"
        "6. **VERIFICATION**: Confirm the exploit works (e.g., spawns a shell or cat flag).\n\n"
        
        "### GUIDELINES\n"
        "- Think step-by-step. Don't rush into writing exploit code before confirming offsets.\n"
        "- Use `cyclic -l <crash_value>` to find the exact offset from GDB output.\n"
        "- Prefer `pwntools` for payload construction as it handles alignment and endianness correctly.\n"
        "- If `NX` is disabled, shellcode on stack is viable. If `NX` is enabled, use ROP or `ret2libc`.\n\n"
        "Let's win this CTF."
    )
    
    return create_react_agent_graph(llm, tools, system_prompt=system_prompt)
