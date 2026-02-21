import os
import sys

# 1. 强制清理代理
for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]:
    if key in os.environ:
        del os.environ[key]

# 2. 配置 (请根据您当前的 LM Studio 模型调整)
os.environ["OPENAI_API_KEY"] = "lm-studio"
os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:1234/v1"
os.environ["OPENAI_MODEL_NAME"] = "openai/gpt-oss-20b"

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    print("❌ 缺少 langchain_openai 或相关依赖，请先 pip install")
    sys.exit(1)

print(f"🚀 [Last Verification - NoStream] 连接本地 LLM: {os.environ['OPENAI_API_BASE']}")
print(f"🤖 模型: {os.environ['OPENAI_MODEL_NAME']}")

# 3. 初始化 LLM - 最稳妥的非流式配置
llm = ChatOpenAI(
    model=os.environ["OPENAI_MODEL_NAME"],
    openai_api_key=os.environ["OPENAI_API_KEY"],
    openai_api_base=os.environ["OPENAI_API_BASE"],
    temperature=0.7,
    streaming=False, # 关键点：关闭流式！
    request_timeout=300, # 5分钟给它慢慢跑
    max_retries=1
)

# 4. 发起纯对话请求
query = "What is SQL Injection? Explain in one short sentence."
print(f"\n🗣️ 用户指令: {query}")
print("Wait for response (Synchronous)...")

try:
    # 纯同步 invoke
    response = llm.invoke([
        SystemMessage(content="You are a hacker assistant."),
        HumanMessage(content=query)
    ])
    
    print("\n📩 LLM 响应:")
    print(f"Content: {response.content}")
    print(f"\n✅ 成功接收！")

except Exception as e:
    print(f"\n❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 验证结束")
