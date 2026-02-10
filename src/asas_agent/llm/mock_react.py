from typing import List, Dict, Any, Union, Sequence
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool
import uuid

class ReActMockLLM:
    """
    Mock LLM that simulates a ReAct agent for testing v2 architecture.
    Returns AIMessage with tool_calls instead of raw strings.
    """
    
    def __init__(self):
        self.tools = {}
        
    def bind_tools(self, tools: Sequence[BaseTool]):
        """Bind tools to the LLM (simulated)."""
        self.tools = {t.name: t for t in tools}
        return self
        
    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        """Process messages and return an AIMessage with tool calls or content."""
        last_msg = messages[-1]
        content = last_msg.content if isinstance(last_msg.content, str) else ""
        
        # Determine intent based on content logic (similar to v1 MockLLM)
        intent = self._determine_intent(content, messages)
        
        if intent == "final_answer":
            return AIMessage(content="Mission accomplished. The flag is flag{mock_flag}.")
            
        if intent:
            tool_call = self._create_tool_call(intent, content)
            return AIMessage(content="", tool_calls=[tool_call])
            
        return AIMessage(content="I don't know what to do.")

    async def ainvoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """Async version of invoke."""
        return self.invoke(messages)

    def _determine_intent(self, user_msg: str, history: List[BaseMessage]) -> str:
        """Simple rule-based intent detection."""
        user_msg = user_msg.lower()
        
        # Check history to avoid loops
        # If last message was a ToolMessage, we should check its result
        if isinstance(history[-1], ToolMessage):
            tool_result = history[-1].content
            if "flag{" in tool_result:
                return "platform_submit_flag"
                
            if history[-1].name == "platform_submit_flag":
                return "final_answer"
                
            # If we just fetched challenge, maybe we decode?
            if history[-1].name == "platform_get_challenge":
                if "encoded" in tool_result or "base64" in tool_result:
                    return "crypto_decode"
                    
        # Initial triggers
        if "start" in user_msg or "fetch" in user_msg:
             # Only if we haven't fetched yet
             if not any(isinstance(m, ToolMessage) and m.name == "platform_get_challenge" for m in history):
                return "platform_get_challenge"
                
        if "decode" in user_msg:
            return "crypto_decode"
            
        if "submit" in user_msg:
            return "platform_submit_flag"
            
        return None

    def _create_tool_call(self, intent: str, context: str) -> Dict[str, Any]:
        """Generate tool call payload."""
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        
        if intent == "platform_get_challenge":
            # Extract URL if present, otherwise mock
            url = "http://mock-ctf.local/api/v1/challenges/1"
            if "http" in context:
                parts = context.split()
                for p in parts:
                    if p.startswith("http"):
                        url = p
            return {
                "name": "platform_get_challenge",
                "args": {"url": url},
                "id": call_id
            }
            
        elif intent == "crypto_decode":
            # Extract content to decode
            content = "ZmxhZ3ttb2NrX2ZsYWd9" # default mock
            if ":" in context:
                content = context.split(":")[-1].strip()
            return {
                "name": "crypto_decode",
                "args": {"content": content, "method": "base64"},
                "id": call_id
            }
            
        elif intent == "platform_submit_flag":
            return {
                "name": "platform_submit_flag",
                "args": {
                    "challenge_id": "1", # Mock ID
                    "flag": "flag{mock_flag}",
                    "base_url": "http://mock-ctf.local"
                },
                "id": call_id
            }
            
        return {}
