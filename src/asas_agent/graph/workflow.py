from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from .state import AgentState
from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
import json
import uuid

def _parse_manual_tool_calls(content: str) -> List[Dict[str, Any]]:
    """Helper to parse manual tool call patterns from LLM text."""
    import re
    import ast
    import json
    
    tool_calls = []
    
    # Pattern 1: CALL: tool(arg=val)
    call_match = re.search(r"CALL:\s*(\w+)\((.*)\)", content)
    if call_match:
        tool_name = call_match.group(1)
        args_str = call_match.group(2)
        args = {}
        try:
            if args_str.strip():
                parts = re.findall(r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|\d+)', args_str)
                for k, v in parts:
                    args[k] = ast.literal_eval(v)
            tool_calls.append({"name": tool_name.strip(), "args": args, "id": f"call_{uuid.uuid4().hex[:8]}", "type": "tool_call"})
        except: pass
        
    # Pattern 2: <|channel|> or <|message|>
    elif "<|channel|>" in content or "<|message|>" in content:
        msg_match = re.search(r"<\|message\|>(.*)", content)
        if msg_match:
            try:
                args = json.loads(msg_match.group(1))
                tool_name = "unknown"
                if "to=" in content:
                    tn_match = re.search(r"to=(\w+)", content)
                    if tn_match: tool_name = tn_match.group(1)
                tool_calls.append({"name": tool_name.strip(), "args": args, "id": f"call_{uuid.uuid4().hex[:8]}", "type": "tool_call"})
            except: pass
            
    # Pattern 3: Simple JSON block
    if not tool_calls:
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if any(k in data for k in ["tool", "action", "command"]):
                    name = data.pop("tool", data.pop("action", data.pop("command", "unknown")))
                    tool_calls.append({"name": str(name).strip(), "args": data, "id": f"call_{uuid.uuid4().hex[:8]}", "type": "tool_call"})
            except: pass
            
    return tool_calls

def create_react_agent_graph(llm, tools: List[BaseTool], system_prompt: str = None):
    """
    Create a ReAct agent graph with LLM and tools.
    
    Args:
        llm: LangChain-compatible LLM with bind_tools support
        tools: List of LangChain tools
        system_prompt: Optional system prompt to guide the agent
        
    Returns:
        Compiled LangGraph workflow
    """
    if system_prompt:
        system_prompt += "\n\n如果你需要调用工具，请使用以下格式：\nCALL: tool_name(arg1=\"value1\")"

    def agent_node(state: AgentState):
        """Agent reasoning node - decides whether to call tools or respond"""
        messages = state["messages"]
        # Inject system prompt if provided and not already present
        if system_prompt and not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_prompt)] + messages
            
        result = llm.invoke(messages)
        
        # Manual parsing for local LLMs
        manual_calls = _parse_manual_tool_calls(str(result.content))
        if manual_calls and not (hasattr(result, 'tool_calls') and result.tool_calls):
            result.tool_calls = manual_calls
            
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
        "5. 如果解题失败，根据子代理的反馈决定是否重试或分配给其他代理。\n\n"
        "注意：如果需要调用工具，请在回答的最后按照以下格式输出（不要使用原生 Tool Calling）：\n"
        "CALL: tool_name(arg1=\"value1\", arg2=\"value2\")\n\n"
        "可用工具：\n"
        "- dispatch_to_agent(agent_type, task, platform_url, challenge_id)\n"
        "- platform_get_challenge(url)\n"
        "- platform_submit_flag(challenge_id, flag, base_url)\n\n"
        "注意：请优先利用 [事实仓库] 中的信息进行决策，避免重复劳动。"
    )
    
    def orchestrator_node(state: AgentState):
        messages = state["messages"]
        fact_store = state.get("fact_store", {
            "recon": {}, "web": {}, "crypto": {}, "reverse": {}, "common": {}
        })
        
        # 1. 尝试从最近的工具调用中提取事实
        if messages and isinstance(messages[-1], ToolMessage) and messages[-1].name == "dispatch_to_agent":
            try:
                result_data = json.loads(str(messages[-1].content))
                new_facts = result_data.get("extracted_facts", {})
                if new_facts:
                    for k, v in new_facts.items():
                        fact_store["common"][k] = v
            except Exception as e:
                print(f"FAILED to merge facts: {e}")
            
        # 2. 注入事实仓库内容到系统提示词
        knowledge_context = ""
        has_facts = any(len(v) > 0 for v in fact_store.values())
        if has_facts:
            knowledge_context = "\n\n--- [当前全局事实仓库] ---\n"
            for category, facts in fact_store.items():
                if facts:
                    knowledge_context += f"{category.upper()}: {json.dumps(facts, ensure_ascii=False)}\n"
        
        current_system_content = system_prompt + knowledge_context
        
        # 构造消息列表
        new_messages = []
        system_msg_added = False
        for m in messages:
            if isinstance(m, SystemMessage):
                new_messages.append(SystemMessage(content=current_system_content))
                system_msg_added = True
            else:
                new_messages.append(m)
        
        if not system_msg_added:
            new_messages = [SystemMessage(content=current_system_content)] + new_messages
            
        # 直接调用模型，不绑定工具定义
        ai_msg = llm.invoke(new_messages)
        content = str(ai_msg.content)
        
        # 解析正则指令 CALL: tool_name(...) 或模型原生的 <|channel|> 格式
        import re
        import ast
        
        tool_name = None
        args = {}
        
        # 模式 1: CALL: format
        call_match = re.search(r"CALL:\s*(\w+)\((.*)\)", content)
        if call_match:
            tool_name = call_match.group(1)
            args_str = call_match.group(2)
            try:
                if args_str.strip():
                    parts = re.findall(r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|\d+)', args_str)
                    for k, v in parts:
                        args[k] = ast.literal_eval(v)
            except: pass
            
        # 模式 2: 模型原生标记 <|channel|> (适配 Qwen/GPT-OSS)
        elif "<|channel|>" in content:
            msg_match = re.search(r"<\|message\|>(.*)", content)
            if msg_match:
                try:
                    args = json.loads(msg_match.group(1))
                    # 尝试从上下文推断 tool_name
                    if "to=" in content:
                        tool_name = re.search(r"to=(\w+)", content).group(1)
                except: pass
                
        # 模式 3: 简单的 JSON 块
        elif not tool_name:
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                try:
                    args = json.loads(json_match.group(0))
                    if "tool" in args: tool_name = args.pop("tool")
                    elif "action" in args: tool_name = args.pop("action")
                except: pass

        if tool_name:
            # 手动注入 tool_calls 结构，让后续 ToolNode 能识别
            ai_msg.tool_calls = [{
                "name": tool_name.strip(),
                "args": args,
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "type": "tool_call"
            }]
            
        return {"messages": [ai_msg], "fact_store": fact_store}

    workflow = StateGraph(AgentState)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tools", ToolNode(tools))
    
    # Reflection Node Logic
    def reflection_node(state: AgentState):
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = state["messages"]
        last_tool_msg = messages[-1]
        
        # Increment retry count
        current_retries = state.get("retry_count", 0) + 1
        
        reflection_prompt = (
            f"反思时刻 (第 {current_retries}/3 次尝试)：\n"
            f"上一步工具调用返回了错误或未找到 Flag。\n"
            f"错误信息: {last_tool_msg.content[:500]}...\n"
            "请分析失败原因，并生成一个新的策略。你可以尝试：\n"
            "1. 检查参数是否正确。\n"
            "2. 换一个工具或方法。\n"
            "3. 使用 `retrieve_knowledge` 查找类似问题的解决办法。"
        )
        
        # Inject reflection as a user message to guide the LLM
        return {
            "messages": [HumanMessage(content=reflection_prompt)],
            "retry_count": current_retries
        }

    workflow.add_node("reflection", reflection_node)
    
    workflow.add_edge(START, "orchestrator")
    
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        
        # If it's a tool output (ToolMessage)
        if hasattr(last_message, 'tool_call_id'):
            # Check for failure keywords in tool output
            content = str(last_message.content).lower()
            if "error" in content or "failed" in content or "indeterminate" in content:
                # Check retry limit
                retries = state.get("retry_count", 0)
                if retries < 3:
                    return "reflection"
            return "orchestrator"
            
        # If it's an AI message with tool calls
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
            
        return END
        
    workflow.add_conditional_edges("orchestrator", should_continue, ["tools", END])
    workflow.add_conditional_edges("tools", should_continue, ["orchestrator", "reflection"])
    workflow.add_edge("reflection", "orchestrator")
    
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

