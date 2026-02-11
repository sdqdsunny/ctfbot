from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
import requests
import os

class LMStudioLLM(BaseChatModel):
    """Custom LLM for LM Studio using requests to avoid SDK issues."""
    base_url: str
    model_name: str
    temperature: float = 0.1

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        # 如果绑定了工具且不是桥接模式，尝试在提示词中注入工具说明
        formatted_msgs = []
        for m in messages:
            role = "user"
            if m.type == "system": role = "system"
            elif m.type == "ai": role = "assistant"
            formatted_msgs.append({"role": role, "content": m.content or ""})
        
        payload = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "temperature": self.temperature
        }
        
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            msg_data = data["choices"][0]["message"]
            content = msg_data.get("content") or ""
            
            # 处理原生 Tool Calls (如果模型输出了)
            tool_calls = []
            if "tool_calls" in msg_data and msg_data["tool_calls"]:
                for tc in msg_data["tool_calls"]:
                    tool_calls.append({
                        "name": tc["function"]["name"],
                        "args": json.loads(tc["function"]["arguments"]),
                        "id": tc["id"],
                        "type": "tool_call"
                    })
            
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content, tool_calls=tool_calls))])
        except Exception as e:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=f"Error connecting to LM Studio: {str(e)}"))])

    def bind_tools(self, tools: List[Any], **kwargs: Any) -> Any:
        # 简单返回自身，目前本地模型主要靠 Prompt-based 桥接或模型自发输出
        return self

    @property
    def _llm_type(self) -> str:
        return "lmstudio"

def create_llm(config: Dict[str, Any]) -> Any:
    """Create LLM instance based on configuration."""
    provider = config.get("provider", "anthropic").lower()
    model_name = config.get("model")
    
    if provider == "lmstudio":
        base_url = config.get("base_url") or "http://localhost:1234/v1"
        return LMStudioLLM(base_url=base_url, model_name=model_name, temperature=config.get("temperature", 0.1))
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        return ChatAnthropic(model=model_name, api_key=api_key, temperature=config.get("temperature", 0))
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        return ChatOpenAI(model=model_name, api_key=api_key, temperature=config.get("temperature", 0))
    elif provider == "mock":
        from .mock_react import ReActMockLLM
        return ReActMockLLM()
    else:
        raise ValueError(f"Unsupported provider: {provider}")
