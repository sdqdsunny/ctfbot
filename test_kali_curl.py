
from asas_mcp.tools import kali

def test_kali_curl():
    executor = kali.get_executor()
    target = "http://10.255.1.2:81/Less-1/?id=1"
    print(f"Testing connectivity to {target} from Kali VM...")
    result = executor.execute(f"curl -I {target}")
    print("--- Output ---")
    print(result)
    print("--- End ---")

if __name__ == "__main__":
    test_kali_curl()
