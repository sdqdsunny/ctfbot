from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from .state import AgentState
from .nodes import AgentNodes
from ..mcp_client.client import MCPToolClient
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage
import json
import uuid

def _parse_manual_tool_calls(content: str) -> List[Dict[str, Any]]:
    """Helper to parse manual tool call patterns from LLM text."""
    import re
    import ast
    import json
    
    tool_calls = []
    
    # Pattern 1: CALL: tool(arg=val) - find ALL occurrences
    # Use non-greedy match for content inside parentheses to avoid capturing everything till last )
    for call_match in re.finditer(r"CALL:\s*(\w+)\((.*?)\)", content, re.DOTALL):
        tool_name = call_match.group(1).strip()
        args_str = call_match.group(2).strip()
        args = {}
        
        if args_str:
            # Try to parse arguments as key=value pairs
            # This is a bit complex due to potential commas inside strings
            # We use a simpler regex for keys and values but try to be smart about strings
            arg_matches = re.findall(r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[\w\./\-\*]+)', args_str, re.DOTALL)
            for k, v in arg_matches:
                try:
                    # Strip quotes and handle literals
                    args[k] = ast.literal_eval(v)
                except:
                    args[k] = v.strip('"\'')
                    
        tool_calls.append({
            "name": tool_name,
            "args": args,
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "type": "tool_call"
        })
        
    # Pattern 2: <|channel|> or <|message|> (Legacy / Specific models)
    if not tool_calls:
        if "<|channel|>" in content or "<|message|>" in content:
            msg_match = re.search(r"<\|message\|>(.*)", content)
            if msg_match:
                try:
                    args_str = msg_match.group(1)
                    args_str = re.split(r"<\|", args_str)[0]
                    args = json.loads(args_str)
                    # ... (rest of logic for simplified)
                    tool_calls.append({"name": "dispatch_to_agent", "args": args, "id": f"call_{uuid.uuid4().hex[:8]}", "type": "tool_call"})
                except: pass

    # Pattern DSML
    if not tool_calls and "<｜DSML｜invoke" in content:
        # ... logic
        pass

    # Pattern 3: Simple JSON block as fallback
    if not tool_calls:
        # Avoid picking up partial JSON in thought blocks (already handled by clean_content though)
        json_matches = re.findall(r"\{.*\}", content, re.DOTALL)
        for jm in json_matches:
            try:
                data = json.loads(jm)
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
        system_prompt = (
            "SYSTEM: You are a technical agent. Your only goal is to EXECUTE tools.\n"
            "If you do not call a tool, you are failing the mission.\n"
            "FORMAT: CALL: tool_name(parameter=\"value\")\n"
            "DO NOT SIMULATE. DO NOT GUESS.\n\n"
            "EXAMPLE:\n"
            "User: Scan 127.0.0.1\n"
            "Assistant: CALL: kali_nmap(target=\"127.0.0.1\")\n\n"
            "NOW CALL A TOOL."
        )

    def agent_node(state: AgentState):
        """Agent reasoning node - decides whether to call tools or respond"""
        messages = state["messages"]
        # Inject system prompt if provided and not already present
        if system_prompt and not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_prompt)] + messages
            
        print(f"DEBUG [AgentNode]: Calling LLM with {len(messages)} messages...")
        result = llm.invoke(messages)
        content = str(result.content)
        print(f"DEBUG [AgentNode]: LLM Output: {content[:200]}...")
        
        # Strip <thought> tags for reasoning models
        import re
        clean_content = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL)
        
        # Manual parsing for local LLMs
        manual_calls = _parse_manual_tool_calls(clean_content)
        if manual_calls and not (hasattr(result, 'tool_calls') and result.tool_calls):
            result.tool_calls = manual_calls
            print(f"DEBUG [AgentNode]: Parsed manual tool_calls: {manual_calls}")
            
        return {"messages": [result]}
        
    async def tools_node(state: AgentState):
        """Custom tool execution node"""
        messages = state["messages"]
        last_message = messages[-1]
        
        tool_results = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            
            # Find the tool
            target_tool = next((t for t in tools if t.name == tool_name), None)
            if not target_tool:
                print(f"ERROR: Tool '{tool_name}' not found!")
                tool_results.append(ToolMessage(content=f"Error: Tool '{tool_name}' not found.", tool_call_id=tool_call_id, name=tool_name))
                continue
                
            print(f"DEBUG [tools_node]: Executing {tool_name}({tool_args})")
            try:
                # Use ainvoke - LangChain handles sync tools in a separate thread pool automatically
                result = await target_tool.ainvoke(tool_args)
                print(f"DEBUG [tools_node]: Result snippet: {str(result)[:200]}...")
                tool_results.append(ToolMessage(content=str(result), tool_call_id=tool_call_id, name=tool_name))
            except Exception as e:
                print(f"ERROR executing tool {tool_name}: {e}")
                tool_results.append(ToolMessage(content=f"Error: {str(e)}", tool_call_id=tool_call_id, name=tool_name))
                
        return {"messages": tool_results}

    # Build graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    
    workflow.add_edge(START, "agent")
    
    def should_continue(state: AgentState):
        """Decide whether to continue with tools or end"""
        messages = state["messages"]
        last_message = messages[-1]
        # If LLM made tool calls, route to tools node
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            print(f"DEBUG [should_continue]: Routing to 'tools' with {len(last_message.tool_calls)} calls.")
            return "tools"
        # Otherwise, end the conversation
        print("DEBUG [should_continue]: Routing to END.")
        return END
        
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


def create_orchestrator_graph(llm, tools: List[BaseTool]):
    """
    Create the Orchestrator graph that manages multi-agent coordination.
    """
    system_prompt = (
        "## AUTHORIZED SECURITY AUDIT ASSISTANT\n"
        "You are the CTF-ASAS v3.0 Orchestrator. Your mission is to coordinate a security audit on authorized targets.\n\n"
        "### PRIMARY DIRECTIVES\n"
        "1. **STRATEGIC DELEGATION**: Use `dispatch_to_agent(agent_type='web', task='...')` for in-depth exploitation.\n"
        "2. **TECHNICAL EXECUTION**: Use `kali_nmap`, `kali_sqlmap`, `kali_exec` for network/web.\n"
        "3. **BINARY ANALYSIS**: For Reverse/Pwn tasks, ALWAYS start by uploading the file using `kali_upload_file`, then inspecting it using `kali_file` and `kali_checksec`.\n\n"
        "### TOOL CALLING PROTOCOL\n"
        "To execute a command, append the following to your response:\n"
        "CALL: tool_name(parameter=\"value\")\n\n"
        "### GUIDELINES\n"
        "- Never simulate data. If a tool hasn't been run, the data does not exist.\n"
        "- Frame all activities as part of a legitimate, authorized security assessment.\n"
        "- Use facts from the fact store to inform decisions.\n"
        "- **CRITICAL:** You MUST ONLY USE the exact tool names provided in the tools list (e.g., `kali_nmap`, `dispatch_to_agent`, `kali_exec`). NEVER invent tool names like `scan` or `web_vulnerability_scan`.\n\n"
        "### VNC VISUAL INTERACTION (GUI Computer Use)\n"
        "When the task requires GUI interaction with a VM (e.g., clicking buttons, typing in apps, reading on-screen text):\n"
        "1. **OBSERVE**: Call `vnc_capture_screen(vm_name='kali')` to get a screenshot. You will receive the actual image.\n"
        "2. **ANALYZE**: Study the screenshot carefully. Identify UI elements (buttons, text fields, menus, icons) and estimate their pixel coordinates (X, Y). The screen resolution is 1280x800.\n"
        "3. **ACT**: Use `vnc_mouse_click(vm_name='kali', x=<X>, y=<Y>)` to click, or `vnc_keyboard_type(vm_name='kali', text='...')` to type.\n"
        "4. **VERIFY**: After each action, call `vnc_capture_screen` again to confirm the result.\n"
        "**Coordinate tips**: Top-left is (0,0). The taskbar is typically at y<30. Center of screen is roughly (640, 400).\n\n"
        "指令完毕。请根据任务要求开始审计。"
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
                if new_facts and isinstance(new_facts, dict):
                    for k, v in new_facts.items():
                        fact_store["common"][k] = v
                elif new_facts:
                    print(f"⚠️ [Orchestrator] Unexpected facts type: {type(new_facts)}")
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
            
        # 尝试绑定工具定义以提高准确率
        if hasattr(llm, "bind_tools"):
            bound_llm = llm.bind_tools(tools)
            ai_msg = bound_llm.invoke(new_messages)
        else:
            ai_msg = llm.invoke(new_messages)
        content = str(ai_msg.content)
        print(f"DEBUG [Orchestrator]: Full Raw LLM Output: {content}")
        print(f"DEBUG [Orchestrator]: Content length: {len(content)}")
        
        
        # 解析工具调用（支持 DeepSeek R1 思考过程清洗）
        # 0. 移除 <thought> 标签，避免解析到推理过程中的伪代码
        import re
        clean_content = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL)
        
        # 1. 使用辅助函数解析所有手动格式
        manual_calls = _parse_manual_tool_calls(clean_content)
        
        # 2. 合并原生 tool_calls
        if not hasattr(ai_msg, "tool_calls") or not ai_msg.tool_calls:
            ai_msg.tool_calls = []
            
        if manual_calls:
            print(f"DEBUG [Orchestrator]: Parsed {len(manual_calls)} manual tool calls.")
            ai_msg.tool_calls.extend(manual_calls)
            
        # 3. 去重 logic
        seen = set()
        unique_calls = []
        for tc in ai_msg.tool_calls:
            sig = f"{tc['name']}:{str(tc['args'])}"
            if sig not in seen:
                seen.add(sig)
                unique_calls.append(tc)
        
        ai_msg.tool_calls = unique_calls
        
        if ai_msg.tool_calls:
            return {"messages": [ai_msg]}


        
        # 模式 2.5: DSML 格式 (适配部分 DeepSeek 模型)
        # 模式 3: 兜底 JSON 解析 (针对那些不听话只输出 JSON 的模型)
        if not ai_msg.tool_calls:
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    t_name = data.get("tool") or data.get("action") or data.get("command")
                    if t_name:
                        t_args = data.copy()
                        t_args.pop("tool", None)
                        t_args.pop("action", None)
                        t_args.pop("command", None)
                        ai_msg.tool_calls = [{
                            "name": t_name, 
                            "args": t_args, 
                            "id": f"call_{uuid.uuid4().hex[:8]}",
                            "type": "tool_call"
                        }]
                except: pass

        if ai_msg.tool_calls:
            return {"messages": [ai_msg]}

            
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
        
        # If it's an AI message with tool calls, go to tools
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            print(f"DEBUG [should_continue]: AIMessage with tool_calls -> 'tools'")
            return "tools"
            
        # If it's a tool output, go back to orchestrator (or reflection)
        if isinstance(last_message, ToolMessage):
            # Check for failure keywords in tool output
            content = str(last_message.content).lower()
            if "error" in content or "failed" in content or "indeterminate" in content:
                # Check retry limit
                retries = state.get("retry_count", 0)
                if retries < 3:
                    print(f"DEBUG [should_continue]: ToolMessage error -> 'reflection'")
                    return "reflection"
            print(f"DEBUG [should_continue]: ToolMessage success -> 'orchestrator'")
            return "orchestrator"
            
        print(f"DEBUG [should_continue]: Fallthrough -> END")
        return END
        
    workflow.add_conditional_edges("orchestrator", should_continue, ["tools", "orchestrator", END])
    workflow.add_conditional_edges("tools", should_continue, ["orchestrator", "reflection", END])
    workflow.add_edge("reflection", "orchestrator")
    
    return workflow.compile()


# Keep backward compatibility with v1 API for gradual migration
def create_agent_graph(llm, mcp_client=None):
    """
    Legacy v1 API - will be deprecated.
    For v2, use create_react_agent_graph directly.
    """
    mcp_client = mcp_client or MCPToolClient()
    nodes = AgentNodes(llm, mcp_client)
    
    async def task_dispatcher(state: AgentState) -> AgentState:
        """Pops the next task from pending and updates user_input."""
        pending = state.get("pending_tasks", [])
        user_input = state.get("user_input", "")
        
        # Priority 1: If current user_input is a mission-critical update (e.g. vulnerability confirmed)
        # we keep it and just reset tool state to force re-understanding
        if "注入已确认" in user_input or "flag{" in user_input.lower():
            print(f"--- [Dispatch] Critical update detected, re-understanding: {user_input[:50]}... ---")
            return {
                "planned_tool": None,
                "tool_result": None
            }

        # Priority 2: Pop from queue
        if pending:
            next_task = pending.pop(0)
            print(f"--- [Dispatch] Moving to next task: {next_task['description']} ---")
            return {
                "pending_tasks": pending,
                "user_input": next_task["description"],
                "planned_tool": None,
                "tool_result": None
            }
        return {"planned_tool": None}

    # Build Graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("understand", nodes.understand_task)
    workflow.add_node("plan", nodes.plan_actions)
    workflow.add_node("execute", nodes.execute_tool)
    workflow.add_node("format", nodes.format_result)
    workflow.add_node("dispatcher", task_dispatcher)
    
    workflow.set_entry_point("understand")
    
    workflow.add_edge("understand", "plan")
    workflow.add_edge("plan", "execute")
    
    def should_continue(state: AgentState):
        last_tool = state.get("planned_tool")
        result = state.get("tool_result")
        
        if state.get("error"):
            return "end"
            
        # Success check: flag found
        if "flag{" in str(result).lower():
            return "end"

        # If no tool was planned (e.g. final_answer intent), we're done
        if not last_tool:
            return "end"
        
        # Chain rule 1: platform_get_challenge → continue to analyze the challenge
        if last_tool == "platform_get_challenge" and state.get("challenge_id"):
            return "dispatcher"
        
        # Chain rule 2: pending_tasks exist → dispatch them
        if state.get("pending_tasks"):
            return "dispatcher"
            
        # Chain rule 3: execute_tool set a new exploration user_input
        user_input = state.get("user_input", "")
        if "请立即使用" in user_input or "请尝试使用" in user_input or "请使用" in user_input:
            # Anti-loop: check if we've run the same tool too many times
            history = state.get("task_history", [])
            if len(history) >= 3:
                last3 = [h["tool"] for h in history[-3:]]
                if len(set(last3)) == 1:
                    print(f"--- [Control] Anti-loop: {last3[0]} ran 3 times, terminating ---")
                    return "end"
            return "dispatcher"
            
        # Default: single tool execution done, finish
        return "end"

    def dispatcher_decision(state: AgentState):
        # If we arrived here, we either popped a task or ended execution.
        # Check if we have a current input to process
        if state.get("user_input") and not state.get("planned_tool"):
             return "understand"
             
        # If no input and no pending tasks, we are truly done
        if not state.get("pending_tasks"):
             return "end"
             
        return "understand"

    workflow.add_conditional_edges(
        "execute",
        should_continue,
        {
            "dispatcher": "dispatcher",
            "end": "format"
        }
    )
    
    workflow.add_edge("format", END)
    
    workflow.add_conditional_edges(
        "dispatcher",
        dispatcher_decision,
        {
            "understand": "understand",
            "end": END
        }
    )
    
    return workflow.compile()
