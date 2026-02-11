import requests
import json

url = "http://127.0.0.1:1234/v1/chat/completions"
headers = {"Content-Type": "application/json"}
data = {
    "model": "google/gemma-3-27b",
    "messages": [{"role": "user", "content": "Say hello!"}]
}

try:
    print("Testing connection with requests (matching curl)...")
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Failed: {e}")
