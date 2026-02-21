from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
import requests
import os
import json

class LMStudioLLM(BaseChatModel):
    """Custom LLM for LM Studio using requests to avoid SDK issues."""
    base_url: str
    model_name: str
    temperature: float = 0.1

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        # Merge system prompt into first human message for better local model compliance
        system_content = ""
        for m in messages:
            if m.type == "system":
                system_content = m.content
                break
                
        formatted_msgs = []
        for m in messages:
            # Skip system message as we'll merge it
            if m.type == "system":
                continue
                
            content = m.content or ""
            if m.type == "user" and system_content:
                content = f"{system_content}\n\nUSER COMMAND: {content}"
                system_content = "" # Only do it once
                
            if m.type == "ai":
                msg = {"role": "assistant", "content": content}
                formatted_msgs.append(msg)
            elif m.type == "tool":
                formatted_msgs.append({"role": "user", "content": f"🛠️ Tool Output ({m.name}):\n{content}"})
            else:
                formatted_msgs.append({"role": "user", "content": content})
        
        payload = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "temperature": self.temperature
        }
        
        print(f"DEBUG [LMStudio]: Sending {len(formatted_msgs)} messages to {self.model_name}")
        
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, timeout=1200)
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
        return self

    @property
    def _llm_type(self) -> str:
        return "lmstudio"

from dotenv import load_dotenv
load_dotenv()

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
    elif provider == "openai" or provider == "deepseek":
        from langchain_openai import ChatOpenAI
        api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(f"Missing API key for provider {provider}")
        base_url = config.get("base_url")
        if provider == "deepseek" and not base_url:
            base_url = "https://api.deepseek.com/v1"
        return ChatOpenAI(
            model=model_name, 
            api_key=api_key, 
            base_url=base_url,
            temperature=config.get("temperature", 0.1)
        )
    elif provider == "mock":
        from .mock_react import ReActMockLLM
        return ReActMockLLM()
    else:
        raise ValueError(f"Unsupported provider: {provider}")
