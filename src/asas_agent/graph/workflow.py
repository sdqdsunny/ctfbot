from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from .state import AgentState
from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage

def create_react_agent_graph(llm, tools: List[BaseTool]):
    """
    Create a ReAct agent graph with LLM and tools.
    
    Args:
        llm: LangChain-compatible LLM with bind_tools support
        tools: List of LangChain tools
        
    Returns:
        Compiled LangGraph workflow
    """
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    def agent_node(state: AgentState):
        """Agent reasoning node - decides whether to call tools or respond"""
        result = llm_with_tools.invoke(state["messages"])
        return {"messages": [result]}
        
    # Build graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.add_edge(START, "agent")
    
    def should_continue(state: AgentState):
        """Decide whether to continue with tools or end"""
        messages = state["messages"]
        last_message = messages[-1]
        # If LLM made tool calls, route to tools node
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        # Otherwise, end the conversation
        return END
        
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


def create_orchestrator_graph(llm, tools: List[BaseTool]):
    """
    Create the Orchestrator graph that manages multi-agent coordination.
    """
    system_prompt = (
        "你是 CTF-ASAS v3.0 总指挥 (Orchestrator) 决策脑。\n"
        "你的主要职责：\n"
        "1. 使用 `platform_get_challenge` 获取题目列表。\n"
        "2. 对每道题进行分类，并使用 `dispatch_to_agent` 将任务分配给专业的子代理解答。\n"
        "3. 在收到子代理返回的 Flag 后，使用 `platform_submit_flag` 进行提交。\n"
        "4. 管理解题的整体策略与状态，汇总结果生成最终报告。\n"
        "5. 如果解题失败，根据子代理的反馈决定是否重试或分配给其他代理。"
    )
    
    llm_with_tools = llm.bind_tools(tools)
    
    def orchestrator_node(state: AgentState):
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_prompt)] + messages
            
        result = llm_with_tools.invoke(messages)
        return {"messages": [result]}

    workflow = StateGraph(AgentState)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.add_edge(START, "orchestrator")
    
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return END
        
    workflow.add_conditional_edges("orchestrator", should_continue, ["tools", END])
    workflow.add_edge("tools", "orchestrator")
    
    return workflow.compile()


# Keep backward compatibility with v1 API for gradual migration
def create_agent_graph(llm):
    """
    Legacy v1 API - will be deprecated.
    For v2, use create_react_agent_graph directly.
    """
    from ..mcp_client.client import MCPToolClient
    from .nodes import AgentNodes
    
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
        
        if state.get("error"):
            return "end"
        
        if last_tool == "platform_get_challenge":
            return "understand"

        if last_tool == "reverse_ghidra_decompile":
            return "understand"
            
        if last_tool == "kali_sqlmap" and "注入已确认" in str(state.get("user_input")):
            return "understand"
            
        if last_tool != "platform_submit_flag" and state.get("challenge_id"):
            res_str = str(result).lower()
            if "flag{" in res_str:
                return "plan"
        
        pending = state.get("pending_tasks", [])
        if pending:
            next_task = pending.pop(0)
            state["pending_tasks"] = pending
            state["user_input"] = next_task["description"]
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

