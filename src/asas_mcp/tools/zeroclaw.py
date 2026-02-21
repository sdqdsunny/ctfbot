import subprocess

async def zeroclaw_open_vnc(vm_name: str) -> str:
    """
    Opens a NoVNC session to the specified VM using ZeroClaw's browser capabilities.
    """
    # 1. Get VM IP using vmrun (simplified mock logic for now)
    vm_ip = "127.0.0.1" # Default fallback
    
    try:
        # Try to use vmrun getGuestIPAddress if available
        result = subprocess.run(["vmrun", "getGuestIPAddress", f"/Users/Shared/Virtual Machines.localized/{vm_name}.vmwarevm/{vm_name}.vmx"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            vm_ip = result.stdout.strip()
    except FileNotFoundError:
        pass # vmrun not installed or VM not found, use fallback
        
    novnc_url = f"http://{vm_ip}:6080/vnc.html"
    
    # 2. Invoke ZeroClaw CLI to open the browser
    cmd = ["zeroclaw", "agent", "-m", f"打开浏览器访问 {novnc_url}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if proc.returncode == 0:
        return f"✅ ZeroClaw browser launched for {vm_name} at {novnc_url}"
    else:
        return f"❌ Failed to launch ZeroClaw browser: {proc.stderr}"
