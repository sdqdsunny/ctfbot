
import asyncio
import os
import sys

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "src"))

from asas_mcp.tools.kali import get_executor

async def main():
    executor = get_executor()
    target = "http://10.255.1.2:81/Less-1/?id=1"
    print(f"Testing connectivity from Kali VM to {target}...")
    # Just run curl and see if we get the index page
    result = executor.execute(f"curl -s '{target}' | grep -o 'Welcome'")
    if "Welcome" in result:
        print("✅ Success: Kali VM can reach the host via 10.255.1.2")
    else:
        print(f"❌ Failure: Kali VM cannot reach the host. Response: {result}")
        # Try finding the gateway IP
        gateway = executor.execute("ip route show default | awk '/default/ {print $3}'").strip()
        print(f"Guest Gateway: {gateway}")
        print("Trying gateway IP...")
        target_gw = f"http://{gateway}:81/Less-1/?id=1"
        result_gw = executor.execute(f"curl -s '{target_gw}' | grep -o 'Welcome'")
        if "Welcome" in result_gw:
            print(f"✅ Success: Kali VM can reach host via gateway IP ({gateway})")
        else:
            print(f"❌ Still failed via gateway {gateway}")

if __name__ == "__main__":
    asyncio.run(main())
