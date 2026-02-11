
from asas_mcp.tools import kali

def test_kali_simple():
    executor = kali.get_executor()
    print("Running 'ls /' in Kali VM...")
    result = executor.execute("ls /")
    print("--- Output ---")
    print(result)
    print("--- End ---")

if __name__ == "__main__":
    test_kali_simple()
