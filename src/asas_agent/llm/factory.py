from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
import requests
import os
import json

import logging
logger = logging.getLogger(__name__)

# 本地模型在 CPU 上推理很慢，单次请求要给足时间。代价是上游真的挂死时，
# 也要等这么久才会失败——想更快失败就调小它（原来是写死在调用处的 1200）。
_REQUEST_TIMEOUT_S = 2400.0

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
            # 注意是 "human" 不是 "user"：LangChain 的 HumanMessage.type == "human"。
            # 这里原先写死 m.type == "user"，条件永不成立，于是系统提示被上面的
            # continue 跳过后再没人合并——整份系统提示（含工具用法说明）从没发给过
            # 模型。本地模型"不听话"的真正原因是这个，而不是提示词不够强硬。
            if m.type in ("human", "user") and system_content:
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
        
        logger.debug(f"DEBUG [LMStudio]: Sending {len(formatted_msgs)} messages to {self.model_name}")
        
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, timeout=_REQUEST_TIMEOUT_S)
            resp.raise_for_status()
            data = resp.json()
            msg_data = data["choices"][0]["message"]
            content = msg_data.get("content") or ""
            
            # 处理原生 Tool Calls (如果模型输出了标准的 JSON format)
            tool_calls = []
            if "tool_calls" in msg_data and msg_data["tool_calls"]:
                for tc in msg_data["tool_calls"]:
                    tool_calls.append({
                        "name": tc["function"]["name"],
                        "args": json.loads(tc["function"]["arguments"]),
                        "id": tc["id"],
                        "type": "tool_call"
                    })
            else:
                import re
                import uuid
                # Pattern to catch <tool_call> blocks
                tc_pattern = re.compile(r"<tool_call>.*?</tool_call>", re.DOTALL)
                func_pattern = re.compile(r"<function=([^>]+)>")
                param_pattern = re.compile(r"<parameter=([^>]+)>(.*?)</parameter>", re.DOTALL)
                
                for tc_block in tc_pattern.findall(content):
                    func_match = func_pattern.search(tc_block)
                    if func_match:
                        func_name = func_match.group(1).strip()
                        args = {}
                        for p_match in param_pattern.finditer(tc_block):
                            args[p_match.group(1).strip()] = p_match.group(2).strip()
                            
                        tool_calls.append({
                            "name": func_name,
                            "args": args,
                            "id": f"call_{uuid.uuid4().hex[:8]}",
                            "type": "tool_call"
                        })
                        
                        # Remove the parsed tool call from the text content so it isn't just spit out
                        content = content.replace(tc_block, "").strip()

                # Pattern to catch [TOOL_REQUEST] blocks
                tr_pattern = re.compile(r"\[TOOL_REQUEST\](.*?)\[END_TOOL_REQUEST\]", re.DOTALL)
                for tr_block in tr_pattern.findall(content):
                    try:
                        tr_json = json.loads(tr_block.strip())
                        tool_calls.append({
                            "name": tr_json.get("name"),
                            "args": tr_json.get("arguments", {}),
                            "id": f"call_{uuid.uuid4().hex[:8]}",
                            "type": "tool_call"
                        })
                        # Remove the parsed blocks
                        content = content.replace(f"[TOOL_REQUEST]{tr_block}[END_TOOL_REQUEST]", "").strip()
                    except json.JSONDecodeError:
                        pass
            
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

class GeminiLLM(BaseChatModel):
    """Custom LLM adapter for Google Gemini using native google-generativeai SDK.
    
    Supports multi-modal input (text + images) and function calling,
    bypassing the langchain-google-genai version conflict.
    """
    api_key: str
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.0
    _client: Any = None
    _bound_tools: List[Any] = []

    def model_post_init(self, __context: Any) -> None:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self._client = genai.GenerativeModel(self.model_name)
        self._bound_tools = []

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        import google.generativeai as genai
        
        # Convert LangChain messages to Gemini format
        gemini_contents = []
        for m in messages:
            if m.type == "system":
                gemini_contents.append({"role": "user", "parts": [f"[System Instructions]\n{m.content}"]})
                gemini_contents.append({"role": "model", "parts": ["Understood. I will follow these instructions."]})
            elif m.type == "human" or m.type == "user":
                parts = []
                content = m.content
                # Handle multimodal content (list of dicts with text/image_url)
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                parts.append(item["text"])
                            elif item.get("type") == "image_url":
                                url = item.get("image_url", {}).get("url", "")
                                if url.startswith("data:"):
                                    # Parse data URI: data:image/png;base64,<data>
                                    import base64
                                    header, b64data = url.split(",", 1)
                                    mime = header.split(":")[1].split(";")[0]
                                    img_bytes = base64.b64decode(b64data)
                                    parts.append({"mime_type": mime, "data": img_bytes})
                        elif isinstance(item, str):
                            parts.append(item)
                else:
                    parts.append(str(content))
                gemini_contents.append({"role": "user", "parts": parts})
            elif m.type == "ai":
                parts = []
                if m.content:
                    parts.append(str(m.content))
                # Handle tool calls in AI messages
                if hasattr(m, 'tool_calls') and m.tool_calls:
                    from google.protobuf.struct_pb2 import Struct
                    for tc in m.tool_calls:
                        s = Struct()
                        s.update(tc.get("args", {}))
                        parts.append(genai.protos.Part(
                            function_call=genai.protos.FunctionCall(
                                name=tc["name"], args=s
                            )
                        ))
                if parts:
                    gemini_contents.append({"role": "model", "parts": parts})
            elif m.type == "tool":
                # Tool response
                from google.protobuf.struct_pb2 import Struct
                s = Struct()
                try:
                    result = json.loads(m.content) if isinstance(m.content, str) else m.content
                except (json.JSONDecodeError, TypeError):
                    result = {"result": str(m.content)}
                if not isinstance(result, dict):
                    result = {"result": str(result)}
                s.update(result)
                gemini_contents.append({
                    "role": "user",
                    "parts": [genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=m.name, response=s
                        )
                    )]
                })

        # Build tools for Gemini if bound
        gemini_tools = None
        if self._bound_tools:
            func_declarations = []
            for tool in self._bound_tools:
                # Build a simple schema from tool description
                func_declarations.append(genai.protos.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description or "No description",
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={},  # Gemini will infer params from description
                    )
                ))
            if func_declarations:
                gemini_tools = [genai.protos.Tool(function_declarations=func_declarations)]

        try:
            generation_config = genai.GenerationConfig(temperature=self.temperature)
            response = self._client.generate_content(
                gemini_contents,
                tools=gemini_tools,
                generation_config=generation_config,
            )
            
            # Parse response
            candidate = response.candidates[0]
            text_parts = []
            tool_calls = []
            
            for part in candidate.content.parts:
                if part.text:
                    text_parts.append(part.text)
                if part.function_call:
                    fc = part.function_call
                    tool_calls.append({
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                        "id": f"call_{fc.name}_{id(fc)}",
                        "type": "tool_call"
                    })
            
            content = "\n".join(text_parts)
            return ChatResult(generations=[ChatGeneration(
                message=AIMessage(content=content, tool_calls=tool_calls)
            )])
        except Exception as e:
            print(f"ERROR [GeminiLLM]: {e}")
            import traceback
            traceback.print_exc()
            return ChatResult(generations=[ChatGeneration(
                message=AIMessage(content=f"Error calling Gemini: {str(e)}")
            )])
    
    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "GeminiLLM":
        """Bind tools for function calling. Returns a new instance with tools bound."""
        bound = GeminiLLM(
            api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.temperature
        )
        bound._bound_tools = list(tools)
        return bound

    @property
    def _llm_type(self) -> str:
        return "gemini"

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
        
        if provider == "deepseek":
            api_key = config.get("api_key") or os.environ.get("DEEPSEEK_API_KEY")
            base_url = config.get("base_url") or "https://api.deepseek.com/v1"
        else:
            api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
            base_url = config.get("base_url")

        if not api_key:
            raise ValueError(f"Missing API key for provider {provider}")
            
        return ChatOpenAI(
            model=model_name, 
            openai_api_key=api_key, 
            base_url=base_url,
            temperature=config.get("temperature", 0.1)
        )
    elif provider == "google":
        api_key = config.get("api_key") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(f"Missing API key for provider {provider}")
        return GeminiLLM(
            api_key=api_key,
            model_name=model_name or "gemini-2.5-flash",
            temperature=config.get("temperature", 0)
        )
    elif provider == "zhipu" or provider == "glm":
        from langchain_openai import ChatOpenAI
        api_key = config.get("api_key") or os.environ.get("ZHIPU_API_KEY")
        if not api_key:
            raise ValueError(f"Missing API key for provider {provider}")
        base_url = config.get("base_url") or "https://open.bigmodel.cn/api/paas/v4/"
        return ChatOpenAI(
            model=model_name or "glm-4-plus",
            api_key=api_key,
            base_url=base_url,
            temperature=config.get("temperature", 0.1)
        )
    elif provider == "mock":
        from .mock_react import ReActMockLLM
        return ReActMockLLM()
    else:
        raise ValueError(f"Unsupported provider: {provider}")
