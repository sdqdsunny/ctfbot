from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import AgentNodes
from ..llm.base import LLMProvider
from ..mcp_client.client import MCPToolClient

def create_agent_graph(llm: LLMProvider):
    # Note: creating a new MCPToolClient here means we create a new stdio connection per graph usage.
    # In a long running service we might want to pass this in, but for CLI MVP this is fine.
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
    
    def should_continue(state: AgentState):
        last_tool = state.get("planned_tool")
        result = state.get("tool_result")
        print(f"--- [Workflow] Last Tool: {last_tool}, Challenge ID: {state.get('challenge_id')} ---")
        
        if state.get("error"):
            return "end"
        
        # If we just fetched a challenge, go back to understand its description
        if last_tool == "platform_get_challenge":
            return "understand"

        # If we just decompiled, we need to analyze the code
        if last_tool == "reverse_ghidra_decompile":
            return "understand"
            
        # If we just confirmed SQLi, we need to decide next move (like extract flag)
        if last_tool == "kali_sqlmap" and "注入已确认" in str(state.get("user_input")):
            return "understand"
            
        # If we have a potential flag and haven't submitted it yet
        if last_tool != "platform_submit_flag" and state.get("challenge_id"):
            res_str = str(result).lower()
            if "flag{" in res_str:
                print(f"--- [Workflow] Flag detected in result, looping to plan submission ---")
                return "plan"
        
        # Backtracking: If we have pending tasks, try the next one
        pending = state.get("pending_tasks", [])
        if pending:
            next_task = pending.pop(0)
            state["pending_tasks"] = pending
            state["user_input"] = next_task["description"]
            print(f"--- [Workflow] Backtracking to pending task: {state['user_input']} ---")
            return "understand"

        return "end"

    workflow.add_conditional_edges(
        "execute",
        should_continue,
        {
            "understand": "understand",
            "plan": "plan",
            "end": "format"
        }
    )
    
    workflow.add_edge("format", END)
    
    return workflow.compile()
