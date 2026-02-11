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
    extracted_facts: Dict[str, Any] = Field(default_factory=dict, description="Structured facts found (e.g. {port: 80})")
    artifacts: List[str] = Field(default_factory=list, description="Paths to extracted files or data")
    error: Optional[str] = Field(None, description="Error message if any")

# Registry of agent creation functions
from ..agents.crypto import create_crypto_agent
from ..agents.web import create_web_agent
from ..agents.reverse import create_reverse_agent
from ..agents.recon import create_recon_agent
from ..agents.writeup import create_writeup_agent
from ..agents.memory import create_memory_agent

from ..utils.config import config_loader
from ..llm.factory import create_llm
from .tools_factory import get_tools_for_agent
from langchain_core.messages import HumanMessage, AIMessage

AGENT_CREATORS = {
    "crypto": create_crypto_agent,
    "web": create_web_agent,
    "reverse": create_reverse_agent,
    "recon": create_recon_agent,
    "writeup": create_writeup_agent,
    "memory": create_memory_agent
}

@tool
async def dispatch_to_agent(agent_type: str, task: str, platform_url: Optional[str] = None, challenge_id: Optional[str] = None) -> str:
    """
    Dispatch a task to a specialized agent.
    
    Args:
        agent_type: One of 'crypto', 'web', 'reverse', 'recon'
        task: Detailed description of the task
        platform_url: URL of the CTF platform (optional)
        challenge_id: ID of the challenge (optional)
        
    Returns:
        A JSON string containing the AgentResult.
    """
    if agent_type not in AGENT_CREATORS:
        return json.dumps({
            "status": "failure",
            "reasoning": f"Unknown agent type: {agent_type}",
            "error": f"Agent type '{agent_type}' is not registered."
        })
        
    # 1. Load agent configuration
    agent_config = config_loader.get_agent_config(agent_type)
    if not agent_config:
        # Fallback to a default if not found in YAML
        agent_config = config_loader.get_orchestrator_config()
        
    print(f"--- [Dispatch] Creating {agent_type} agent with model: {agent_config.get('model')} ---")
    
    # 2. Instantiate LLM
    try:
        llm = create_llm(agent_config)
    except Exception as e:
        return json.dumps({
            "status": "failure",
            "reasoning": f"Failed to initialize LLM for {agent_type}",
            "error": str(e)
        })

    # 3. Get domain tools
    tools = get_tools_for_agent(agent_type)
    
    # 4. Create and compile the sub-agent graph
    agent_creator = AGENT_CREATORS[agent_type]
    graph = agent_creator(llm, tools)
    
    # 5. Invoke sub-agent
    try:
        # Construct initial state with platform context and task message
        inputs = {
            "messages": [HumanMessage(content=task)],
            "platform_url": platform_url,
            "challenge_id": challenge_id
        }
        
        print(f"--- [Sub-Agent: {agent_type}] Mission Start ---")
        
        # Run graph and trace progress
        # Run graph and trace progress
        final_state = inputs
        async for event in graph.astream(inputs, stream_mode="updates"):
            # DEBUG: print raw event
            print(f"DEBUG [Dispatcher] raw event: {str(event)[:300]}")
            
            # event is {node_name: {updates}}
            if not isinstance(event, dict):
                print(f"⚠️ [Dispatcher] Unexpected event type: {type(event)}. Content: {str(event)[:200]}")
                if isinstance(event, list) and len(event) > 0 and isinstance(event[0], dict):
                    # Fallback for unexpected list of dicts
                    event = event[0]
                else:
                    continue

            for node, update in event.items():
                if node == "__start__": continue
                print(f"   [{agent_type}] Update from Node: {node}")
                
                if isinstance(update, dict):
                    # For messages, usually it's addition (reducer)
                    if "messages" in update:
                        if "messages" not in final_state: final_state["messages"] = []
                        msgs = update["messages"]
                        if not isinstance(msgs, list): msgs = [msgs]
                        final_state["messages"].extend(msgs)
                        
                        # Logging
                        for m in msgs:
                            role_name = type(m).__name__
                            content_snippet = str(m.content).replace("\n", " ")[:150]
                            print(f"   [{agent_type}] 📝 {role_name}: {content_snippet}...")
                            if hasattr(m, 'tool_calls') and m.tool_calls:
                                print(f"   [{agent_type}] 🔧 调用工具: {m.tool_calls[0].get('name')}")
                            
                    # For other fields
                    for k, v in update.items():
                        if k != "messages": final_state[k] = v
                else:
                    # Fallback for non-dict updates
                    final_state[node] = update
        
        print(f"--- [Sub-Agent: {agent_type}] Mission Finished ---")
        
        # 6. Extract result from final state
        # The goal is to return a meaningful string (the last AI message)
        messages = final_state.get("messages", [])
        if not messages:
            return json.dumps({"status": "failure", "reasoning": "Sub-agent returned no messages."})
            
        # Find the last AI message that is not just tool calls
        last_message = None
        for m in reversed(messages):
            if isinstance(m, AIMessage) and m.content:
                last_message = m
                break
        
        if not last_message:
            last_message = messages[-1]
        
        reasoning = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # 7. Post-process to find Flag and Facts
        flag = None
        extracted_facts = {}
        import re
        
        # Extract Flag
        flag_match = re.search(r"flag\{.*?\}", reasoning, re.IGNORECASE)
        if flag_match:
            flag = flag_match.group(0)
            status = "success"
        else:
            status = "indeterminate"
            
        # Extract Facts (Look for JSON block or specific tag)
        # Pattern: FACTS: { ... }
        facts_match = re.search(r"FACTS:\s*(\{.*?\})", reasoning, re.DOTALL)
        if facts_match:
            try:
                extracted_facts = json.loads(facts_match.group(1))
            except:
                pass

        result = AgentResult(
            status=status,
            flag=flag,
            reasoning=reasoning,
            extracted_facts=extracted_facts,
            artifacts=[]
        )
        return result.model_dump_json()

    except Exception as e:
        print(f"Error during sub-agent execution: {str(e)}")
        return json.dumps({
            "status": "failure", 
            "reasoning": f"Execution error in {agent_type} agent",
            "error": str(e)
        })
