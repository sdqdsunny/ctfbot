
from asas_mcp.tools import kali

def test_sqlmap_version():
    executor = kali.get_executor()
    print("Checking sqlmap version in Kali VM...")
    result = executor.execute("sqlmap --version")
    print("--- Output ---")
    print(result)
    print("--- End ---")

if __name__ == "__main__":
    test_sqlmap_version()
