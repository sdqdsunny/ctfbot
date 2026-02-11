
import asyncio
from asas_mcp.tools import kali

async def test_kali_sqlmap():
    url = "http://10.255.1.2:81/Less-1/?id=1"
    args = "--batch --dbs"
    print(f"Running sqlmap on {url} with args {args}...")
    result = kali.sqlmap(url, args)
    print("--- SQLMap Output ---")
    print(result)
    print("--- End of Output ---")

if __name__ == "__main__":
    asyncio.run(test_kali_sqlmap())
