import os
import sys

# 1. 强制清理代理，避免干扰 localhost
for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]:
    if key in os.environ:
        del os.environ[key]

# 2. 基本配置
os.environ["OPENAI_API_KEY"] = "lm-studio"
os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:1234/v1"
os.environ["OPENAI_MODEL_NAME"] = "deepseek-r1-distill-llama-8b"

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    print("❌ 缺少 langchain_openai 或相关依赖，请先 pip install")
    sys.exit(1)

print(f"🚀 [Verification-Final] 连接本地 LLM: {os.environ['OPENAI_API_BASE']}")
print(f"🤖 模型: {os.environ['OPENAI_MODEL_NAME']}")

# 3. 初始化 LLM - 最纯净配置（不带 tools）
llm = ChatOpenAI(
    model=os.environ["OPENAI_MODEL_NAME"],
    openai_api_key=os.environ["OPENAI_API_KEY"],
    openai_api_base=os.environ["OPENAI_API_BASE"],
    temperature=0.1,
    streaming=True,
    request_timeout=60,
    max_retries=0
)

# 4. 发起纯对话请求
query = "Explain what is SSTI vulnerability briefly."
print(f"\n🗣️ 用户指令: {query}")
print("Wait for response (Pure Chat)...")

try:
    # 流式输出
    full_content = ""
    for chunk in llm.stream([
        SystemMessage(content="You are a security expert. Answer in English."),
        HumanMessage(content=query)
    ]):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_content += chunk.content
            
    print("\n\n✅ 流式接收完成。")
    print(f"Total Length: {len(full_content)}")

except Exception as e:
    print(f"\n❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 验证结束")
