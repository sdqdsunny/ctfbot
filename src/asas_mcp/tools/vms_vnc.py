import os
import subprocess
import asyncio
from dotenv import load_dotenv

async def get_vm_ip(vm_name: str) -> str:
    """
    Dynamically find the IP address of a running VM by partial name match.
    Runs `vmrun list` to find the correct .vmx path, then `vmrun getGuestIPAddress`.
    """
    try:
        # 1. Get list of running VMs
        list_proc = subprocess.run(["vmrun", "list"], capture_output=True, text=True, check=True)
        running_vms = list_proc.stdout.strip().split('\n')[1:] # Skip the first line "Total running VMs: X"
        
        vmx_path = None
        for path in running_vms:
            # Case-insensitive partial match on the vmx file name or path
            if vm_name.lower() in path.lower():
                vmx_path = path.strip()
                break
                
        if not vmx_path:
            return f"Error: No running VM found containing '{vm_name}' in its path. Running VMs: {running_vms}"

        # 2. Get IP for the matched VM
        ip_proc = subprocess.run(["vmrun", "getGuestIPAddress", vmx_path], capture_output=True, text=True, check=True)
        ip = ip_proc.stdout.strip()
        
        # If the result is not a valid IP (e.g., "unknown" or error message)
        if not ip or len(ip.split('.')) != 4:
            return f"Error: Could not retrieve a valid IP for {vmx_path}. Returned: {ip}"
            
        return ip
        
    except subprocess.CalledProcessError as e:
        return f"Error executing vmrun: {e.stderr}"
    except Exception as e:
        return f"Unexpected error getting VM IP: {str(e)}"

async def open_vm_vnc(vm_name: str) -> str:
    """
    Opens a Browser-based VNC (NoVNC) session for the specified virtual machine.
    This bypasses any LLM layers and uses native macOS 'open' command for reliability.
    """
    print(f"DEBUG: Attempting to dynamically get IP for VM: {vm_name}")
    vm_ip = await get_vm_ip(vm_name)
    
    # If the returned string starts with "Error", return it immediately
    if vm_ip.startswith("Error"):
        return vm_ip
        
    print(f"DEBUG: Found IP {vm_ip} for VM {vm_name}")
    
    # 1. Prepare NoVNC URL
    # Assuming standard setup: 6080 for NoVNC websockify
    # Use autoconnect=true so the user doesn't have to click "Connect"
    novnc_url = f"http://{vm_ip}:6080/vnc.html?autoconnect=true"
    
    # 2. Invoke browser directly to open NoVNC
    # Using macOS native 'open' command
    cmd = ["open", novnc_url]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if proc.returncode == 0:
        return f"✅ Browser launched for {vm_name} at {novnc_url}"
    else:
        return f"❌ Failed to launch browser: {proc.stderr}"

# --- Native VNC Interaction (C2 Phase) ---
# Used for Agent autonomous Computer Use interactions
async def _execute_vnc_do_command(vm_name: str, commands: list) -> str:
    """Helper to execute vncdotool CLI commands against the VM's VNC port (5900)"""
    ip = await get_vm_ip(vm_name)
    if "Error" in ip:
        return ip
        
    server_address = f"{ip}:5900" 
    
    # Run vncdotool as a subprocess to keep the MCP server robust
    try:
        # vncdotool -s <ip>:5900 <commands>
        cli_args = ["vncdo", "-s", server_address] + commands
        print(f"DEBUG: VNC command executing -> {' '.join(cli_args)}")
        
        proc = await asyncio.create_subprocess_exec(
            *cli_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            return stdout.decode('utf-8') or "VNC sequence executed successfully"
        else:
            return f"VNC Execution Error: {stderr.decode('utf-8')}"
    except Exception as e:
        return f"Unexpected VNC Error: {e}"

async def vnc_capture_screen(vm_name: str, output_path: str = "/tmp/vnc_screenshot.png") -> str:
    """
    Captures the current VNC screen of the specified VM and saves it to a file.
    """
    res = await _execute_vnc_do_command(vm_name, ["capture", output_path])
    if "Error" in res:
        return res
    return f"Screenshot saved to {output_path}"

async def vnc_mouse_click(vm_name: str, x: int, y: int, button: int = 1, double: bool = False) -> str:
    """
    Moves the mouse to (x,y) and clicks the specified button.
    button: 1=Left, 2=Middle, 3=Right, 4=ScrollUp, 5=ScrollDown
    """
    cmd = ["move", str(x), str(y)]
    if double:
        cmd.extend(["pause", "0.1", "click", str(button), "click", str(button)])
    else:
        cmd.extend(["pause", "0.1", "click", str(button)])
        
    return await _execute_vnc_do_command(vm_name, cmd)

async def vnc_keyboard_type(vm_name: str, text: str, append_enter: bool = False) -> str:
    """
    Types literal text into the VNC session.
    """
    cmd = ["type", text]
    if append_enter:
        cmd.extend(["key", "enter"])
    return await _execute_vnc_do_command(vm_name, cmd)

async def vnc_send_key(vm_name: str, key: str) -> str:
    """
    Sends a special key (e.g. enter, esc, ctrl-c, f1, etc.)
    """
    return await _execute_vnc_do_command(vm_name, ["key", key])
