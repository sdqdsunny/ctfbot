
from asas_mcp.tools import kali

def test_sqlmap_banner():
    executor = kali.get_executor()
    target = "http://10.255.1.2:81/Less-1/?id=1"
    print(f"Running sqlmap banner scan on {target}...")
    result = executor.execute(f"sqlmap -u '{target}' --batch --banner")
    print("--- Output ---")
    print(result)
    print("--- End ---")

if __name__ == "__main__":
    test_sqlmap_banner()
