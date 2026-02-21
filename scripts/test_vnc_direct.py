import asyncio
import os
import sys

# Ensure correct path
sys.path.insert(0, os.path.abspath("src"))

from asas_agent.mcp_client.client import MCPToolClient

import asyncio
import os
import sys

# Ensure correct path
sys.path.insert(0, os.path.abspath("src"))

from asas_mcp.tools.vms_vnc import open_vm_vnc

async def test_vms_vnc_kali():
    print("Calling open_vm_vnc('kali')...")
    result = await open_vm_vnc("kali")
    print(f"\nResult for Kali:\n{result}\n")

async def test_vms_vnc_windows():
    print("Calling open_vm_vnc('pentest-windows')...")
    result = await open_vm_vnc("pentest-windows")
    print(f"\nResult for Windows:\n{result}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "win":
        asyncio.run(test_vms_vnc_windows())
    else:
        asyncio.run(test_vms_vnc_kali())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "win":
        asyncio.run(test_vms_vnc_windows())
    else:
        asyncio.run(test_vms_vnc_kali())
