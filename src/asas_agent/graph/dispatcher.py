from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from langchain_core.tools import tool
import json
import asyncio

class AgentResult(BaseModel):
    """Standardized result from a specialized agent."""
    status: str = Field(..., description="success, failure, or indeterminate")
    flag: Optional[str] = Field(None, description="The flag if found")
    reasoning: str = Field(..., description="Summary of reasoning and actions taken")
    artifacts: List[str] = Field(default_factory=list, description="Paths to extracted files or data")
    error: Optional[str] = Field(None, description="Error message if any")

# Registry of agent creation functions
from ..agents.crypto import create_crypto_agent
from ..agents.web import create_web_agent
from ..agents.reverse import create_reverse_agent
from ..agents.recon import create_recon_agent
from ..agents.writeup import create_writeup_agent
from ..agents.memory import create_memory_agent

AGENT_CREATORS = {
    "crypto": create_crypto_agent,
    "web": create_web_agent,
    "reverse": create_reverse_agent,
    "recon": create_recon_agent,
    "writeup": create_writeup_agent,
    "memory": create_memory_agent
}

@tool
async def dispatch_to_agent(agent_type: str, task: str, platform_context: Dict[str, Any]) -> str:
    """
    Dispatch a task to a specialized agent.
    
    Args:
        agent_type: One of 'crypto', 'web', 'reverse', 'recon'
        task: Detailed description of the task to perform
        platform_context: Dictionary containing platform_url, platform_token, and challenge_id
        
    Returns:
        A JSON string containing the AgentResult.
    """
    if agent_type not in AGENT_CREATORS:
        return json.dumps({
            "status": "failure",
            "reasoning": f"Unknown agent type: {agent_type}",
            "error": f"Agent type '{agent_type}' is not registered."
        })
        
    # In a real Scenario, we would resolve the LLM and tools for this agent type
    # For now, we simulate the execution to maintain the architecture flow.
    # The actual integration with LLMFactory will be done in Task 4.
    
    # Simulating a specialized agent's reasoning
    reasoning = f"Specialized {agent_type} agent analyzed the task: {task}"
    
    # Mocking a success scenario for crypto/web with flags
    flag = None
    if "flag" in task.lower() or "decode" in task.lower():
        flag = "flag{v3_multi_agent_power}"
        status = "success"
    else:
        status = "indeterminate"
        
    result = AgentResult(
        status=status,
        flag=flag,
        reasoning=reasoning,
        artifacts=[]
    )
    
    return result.model_dump_json()
