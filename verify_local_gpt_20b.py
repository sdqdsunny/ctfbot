import os
import sys

# 1. 强制清理代理
for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]:
    if key in os.environ:
        del os.environ[key]

# 2. 配置
os.environ["OPENAI_API_KEY"] = "lm-studio"
os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:1234/v1"
os.environ["OPENAI_MODEL_NAME"] = "openai/gpt-oss-20b"

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    print("❌ 缺少 langchain_openai 或相关依赖，请先 pip install")
    sys.exit(1)

print(f"🚀 [Verification-GPT-20B] 连接本地 LLM: {os.environ['OPENAI_API_BASE']}")
print(f"🤖 模型: {os.environ['OPENAI_MODEL_NAME']}")

# 3. 初始化 LLM
llm = ChatOpenAI(
    model=os.environ["OPENAI_MODEL_NAME"],
    openai_api_key=os.environ["OPENAI_API_KEY"],
    openai_api_base=os.environ["OPENAI_API_BASE"],
    temperature=0.1,
    streaming=True, # 开启流式
    request_timeout=240, # 20B 模型生成慢，给足 4 分钟
    max_retries=1
)

# 4. 发起纯对话请求
query = "What is SQL Injection? Explain in one short sentence."
print(f"\n🗣️ 用户指令: {query}")
print("Wait for response (Streaming)...")

try:
    # 流式输出
    full_content = ""
    for chunk in llm.stream([
        SystemMessage(content="You are a hacker assistant."),
        HumanMessage(content=query)
    ]):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_content += chunk.content
            
    print("\n\n✅ 流式接收完成。")
    print(f"Total Length: {len(full_content)}")

except Exception as e:
    print(f"\n❌ 请求失败: {e}")
    # 打印更详细的 debug
    import traceback
    traceback.print_exc()

print("\n✅ 验证结束")
