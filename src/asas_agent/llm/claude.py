from typing import List, Dict
import anthropic
from .base import LLMProvider

class ClaudeLLM(LLMProvider):
    """Anthropic Claude LLM Provider."""
    
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=messages
        )
        return response.content[0].text
