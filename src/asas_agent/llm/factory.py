from typing import Any, Dict
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
import os

def create_llm(config: Dict[str, Any]) -> Any:
    """
    Create a LangChain-compatible LLM instance based on configuration.
    
    Args:
        config: Dictionary containing 'provider', 'model', and optional 'api_key', 'base_url', etc.
        
    Returns:
        An instance of a LangChain ChatModel.
    """
    provider = config.get("provider", "anthropic").lower()
    model_name = config.get("model")
    
    if provider == "anthropic":
        api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        return ChatAnthropic(
            model=model_name,
            api_key=api_key,
            temperature=config.get("temperature", 0)
        )
    elif provider == "lmstudio":
        # LM Studio is OpenAI-compatible
        base_url = config.get("base_url") or "http://localhost:1234/v1"
        return ChatOpenAI(
            model=model_name,
            openai_api_base=base_url,
            openai_api_key="not-needed",  # LM Studio usually doesn't need a key
            temperature=config.get("temperature", 0)
        )
    elif provider == "openai":
        api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            temperature=config.get("temperature", 0)
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
