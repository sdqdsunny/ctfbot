from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
import json

def OpenAICompatProvider(api_key: str, base_url: str, model: str) -> BaseChatModel:
    """Factory to create an OpenAI-compatible LangChain Chat Model."""
    
    # 增加调试回调
    from langchain_core.callbacks import BaseCallbackHandler
    
    class DebugCallback(BaseCallbackHandler):
        def on_llm_start(self, serialized, prompts, **kwargs):
            # 将提示和工具定义打印出来
            print(f"\n[LLM-DEBUG] Start Request to {base_url} (Model: {model})")
            print(f"[LLM-DEBUG] Prompts/Messages (First 500 chars): {str(prompts)[:500]}")
            if 'invocation_params' in kwargs:
                tools = kwargs['invocation_params'].get('tools')
                if tools:
                    print(f"[LLM-DEBUG] Tool Definition Count: {len(tools)}")
                    # 打印前 3 个工具名字
                    tool_names = [t.get('function', {}).get('name') for t in tools[:3]]
                    print(f"            Sample Tools: {tool_names}")
                    # 检查是否有极其庞大的 Schema
                    tool_json = json.dumps(tools)
                    print(f"[LLM-DEBUG] Total Tool Payload Size: {len(tool_json)} bytes")
                    if len(tool_json) > 100000:
                        print("⚠️ WARNING: Tool schema is HUGE (>100KB)! This might crash local LLMs.")
        
        def on_llm_error(self, error, **kwargs):
            print(f"\n❌ [LLM-ERROR]: {error}")

    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=0.1,
        # 暂时关闭 Streaming，用同步 invoke 抓取完整报错
        streaming=False, 
        callbacks=[DebugCallback()],
        # router_model_name=None # REMOVED: Causing TypeError
    )
