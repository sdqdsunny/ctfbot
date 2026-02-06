from .state import AgentState
from ..llm.base import LLMProvider
from ..mcp_client.client import MCPToolClient

class AgentNodes:
    def __init__(self, llm: LLMProvider, mcp_client: MCPToolClient):
        self.llm = llm
        self.mcp_client = mcp_client

    async def understand_task(self, state: AgentState) -> AgentState:
        """Determine intent using LLM."""
        messages = [{"role": "user", "content": state["user_input"]}]
        understanding = self.llm.chat(messages)
        return {"task_understanding": understanding}

    async def plan_actions(self, state: AgentState) -> AgentState:
        """Map understanding to tool args (Simplified for MVP)."""
        intent = state.get("task_understanding", "")
        
        # Simple extraction for MVP - Replace with LLM extraction later
        user_input = state["user_input"]
        
        if intent == "crypto_decode":
            # Extract content after colon or just use input if testing
            content = user_input.split(":")[-1].strip() if ":" in user_input else "SGVsbG8="
            return {
                "planned_tool": "crypto_decode",
                "tool_args": {"content": content, "method": "base64"}
            }
        elif intent == "recon_scan":
            target = user_input.split("IP")[-1].strip() if "IP" in user_input else "127.0.0.1"
            return {
                "planned_tool": "recon_scan", 
                "tool_args": {"target": target, "ports": "80"}
            }
        
        # Fallback for unknown intent
        if not intent or intent == "unknown":
             return {"error": "Unknown intent"}

        return {"error": f"No plan for intent: {intent}"}

    async def execute_tool(self, state: AgentState) -> AgentState:
        """Execute the planned tool."""
        if state.get("error"):
            # Skip execution if error
            return {"tool_result": None}
            
        tool = state["planned_tool"]
        args = state["tool_args"]
        
        if not tool:
             return {"error": "No tool planned"}

        try:
            result = await self.mcp_client.call_tool(tool, args)
            return {"tool_result": result}
        except Exception as e:
            return {"error": str(e)}

    async def format_result(self, state: AgentState) -> AgentState:
        """Format final answer."""
        if state.get("error"):
            return {"final_answer": f"Error: {state['error']}"}
        
        if state.get("tool_result") is None:
             return {"final_answer": "No result produced."}

        return {"final_answer": str(state["tool_result"]).strip()}
