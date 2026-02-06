from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import AgentNodes
from ..llm.base import LLMProvider
from ..mcp_client.client import MCPToolClient

def create_agent_graph(llm: LLMProvider):
    # For MVP we instantiate a new client each time
    mcp_client = MCPToolClient()
    nodes = AgentNodes(llm, mcp_client)
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("understand", nodes.understand_task)
    workflow.add_node("plan", nodes.plan_actions)
    workflow.add_node("execute", nodes.execute_tool)
    workflow.add_node("format", nodes.format_result)
    
    workflow.set_entry_point("understand")
    
    workflow.add_edge("understand", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "format")
    workflow.add_edge("format", END)
    
    return workflow.compile()
