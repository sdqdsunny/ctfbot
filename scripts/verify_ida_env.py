import socket
import sys

def check_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        try:
            s.connect((host, port))
            return True
        except:
            return False

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8745
    if check_port(host, port):
        print(f"✅ IDA MCP Server is RUNNING on {host}:{port}")
        sys.exit(0)
    else:
        print(f"❌ IDA MCP Server is NOT reachable on {host}:{port}")
        sys.exit(1)
