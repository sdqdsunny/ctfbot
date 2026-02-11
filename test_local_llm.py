import openai
import os

client = openai.OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

try:
    print("Testing connection to google/gemma-3-27b...")
    response = client.chat.completions.create(
        model="google/gemma-3-27b",
        messages=[{"role": "user", "content": "Say hello!"}],
        stream=False
    )
    print(f"Success: {response.choices[0].message.content}")
except Exception as e:
    print(f"Failed: {e}")
