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
