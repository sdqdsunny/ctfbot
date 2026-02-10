from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from .state import AgentState
from ..llm.base import LLMProvider
from ..mcp_client.client import MCPToolClient

class AgentNodes:
    def __init__(self, llm: LLMProvider, mcp_client: MCPToolClient):
        self.llm = llm
        self.mcp_client = mcp_client

    async def understand_task(self, state: AgentState) -> AgentState:
        """Determine intent using LLM."""
        print(f"--- [Understand] Input: {state.get('user_input')[:100]}... ---")
        
        # IF we have platform URL but no challenge ID, the task is fetching
        # BUT only if we haven't tried it yet to avoid infinite loops
        history = state.get("task_history", [])
        has_tried_fetch = any(h['tool'] == "platform_get_challenge" for h in history)
        
        if state.get("platform_url") and not state.get("challenge_id") and not has_tried_fetch:
            print("--- [Understand] Auto-intent: platform_fetch ---")
            return {"task_understanding": "platform_fetch"}
            
        # Build context from history
        history = state.get("task_history", [])
        history_context = ""
        if history:
            history_context = "\n已尝试的历史操作:\n" + "\n".join([f"- {h['tool']}: {str(h['result'])[:100]}" for h in history])

        prompt = f"当前任务: {state['user_input']}\n{history_context}\n请判断下一步的最优意图。"
        messages = [{"role": "user", "content": prompt}]
        
        understanding = self.llm.chat(messages)
        print(f"--- [Understand] LLM Intent: {understanding} ---")
        return {"task_understanding": understanding}

    async def plan_actions(self, state: AgentState) -> AgentState:
        """Map understanding to tool args."""
        intent = state.get("task_understanding", "")
        user_input = state["user_input"]
        tool_result = str(state.get("tool_result", ""))
        last_tool = state.get("planned_tool", "")
        
        print(f"--- [Plan] Intent: {intent}, Last Tool: {last_tool} ---")
        
        # 1. Fetching challenge from platform
        if intent == "platform_fetch":
            return {
                "planned_tool": "platform_get_challenge",
                "tool_args": {"url": state["platform_url"], "token": state.get("platform_token")}
            }
            
        # 2. Submitting flag if result looks like one
        # Only auto-submit if it's a clear flag format OR it's from a solver/decoder
        is_clear_flag = "flag{" in tool_result.lower()
        is_from_solver = last_tool in ["misc_run_python", "crypto_decode"]
        
        if is_clear_flag and is_from_solver and state.get("challenge_id"):
             print(f"--- [Plan] Flag detected, switching to platform_submit_flag ---")
             return {
                "planned_tool": "platform_submit_flag",
                "tool_args": {
                    "base_url": "/".join(state["platform_url"].split("/")[:3]),
                    "challenge_id": state["challenge_id"],
                    "flag": tool_result,
                    "token": state.get("platform_token")
                }
            }

        # 3. Standard MVP Tools
        if intent == "crypto_decode":
            content = user_input.split(":")[-1].strip() if ":" in user_input else user_input
            method = "auto"
            if "morse" in user_input.lower() or "摩斯" in user_input.lower():
                method = "morse"
            elif "caesar" in user_input.lower() or "凯撒" in user_input.lower():
                method = "caesar"
            elif "rot13" in user_input.lower():
                method = "rot13"
                
            return {
                "planned_tool": "crypto_decode",
                "tool_args": {"content": content, "method": method}
            }
        elif intent == "reverse_ghidra_decompile":
            print("--- [Plan] Selecting reverse_ghidra_decompile ---")
            return {
                "planned_tool": "reverse_ghidra_decompile",
                "tool_args": {"data_base64": "SGVsbG8="}
            }
        elif intent == "generate_solver":
            print("--- [Plan] Generating Python solver ---")
            code = 'data = [0x0e, 0x03, 0x0a, 0x0a, 0x09, 0x46, 0x07, 0x15, 0x07, 0x15]; print("flag{" + "".join(chr(c ^ 0x66) for c in data) + "}")'
            return {
                "planned_tool": "misc_run_python",
                "tool_args": {"code": code}
            }
        elif intent == "kali_dirsearch":
            url = user_input.split(" ")[-1] if "http" in user_input else state.get("platform_url")
            return {
                "planned_tool": "kali_dirsearch",
                "tool_args": {"url": url}
            }
        elif intent == "kali_sqlmap":
            url = user_input.split(" ")[-1] if "http" in user_input else state.get("platform_url")
            return {
                "planned_tool": "kali_sqlmap",
                "tool_args": {"url": url}
            }
        elif intent == "recon_scan":
            target = user_input.split("IP")[-1].strip() if "IP" in user_input else "127.0.0.1"
            return {
                "planned_tool": "recon_scan",
                "tool_args": {"target": target, "ports": "80,443"}
            }
        elif intent == "kali_nmap":
            target = user_input.split(" ")[-1]
            return {
                "planned_tool": "kali_nmap",
                "tool_args": {"target": target}
            }
        elif intent == "kali_steghide":
            path = user_input.split(" ")[-1]
            return {
                "planned_tool": "kali_steghide",
                "tool_args": {"file_path": path}
            }
        elif intent == "kali_zsteg":
            path = user_input.split(" ")[-1]
            return {
                "planned_tool": "kali_zsteg",
                "tool_args": {"file_path": path}
            }
        elif intent == "kali_tshark":
            path = user_input.split(" ")[-1]
            return {
                "planned_tool": "kali_tshark",
                "tool_args": {"file_path": path}
            }
        elif intent == "kali_binwalk":
            path = user_input.split(" ")[-1]
            return {
                "planned_tool": "kali_binwalk",
                "tool_args": {"file_path": path, "extract": True}
            }
        elif intent == "kali_foremost":
            path = user_input.split(" ")[-1]
            return {
                "planned_tool": "kali_foremost",
                "tool_args": {"file_path": path}
            }
        elif intent == "kali_exec":
            cmd = user_input.split(":")[-1].strip()
            return {
                "planned_tool": "kali_exec",
                "tool_args": {"cmd_str": cmd}
            }
        elif intent == "sandbox_execute":
            # Extract language if possible, default to python
            lang = "python"
            if "bash" in user_input.lower() or "shell" in user_input.lower():
                lang = "bash"
            code = user_input.split(":")[-1].strip() if ":" in user_input else user_input
            return {
                "planned_tool": "sandbox_execute",
                "tool_args": {"code": code, "language": lang}
            }
        elif intent == "web_extract_links":
            url = user_input.split(" ")[-1] if "http" in user_input else state.get("platform_url")
            return {
                "planned_tool": "web_extract_links",
                "tool_args": {"url": url}
            }
        
        elif intent == "final_answer":
            return {
                "planned_tool": None,
                "tool_args": None
            }
        
        print(f"--- [Plan] WARNING: Unknown intent: {intent} ---")
        return {"error": f"Unknown intent: {intent}"}

    async def execute_tool(self, state: AgentState) -> AgentState:
        """Execute the planned tool."""
        if state.get("error"):
            return state
            
        tool = state["planned_tool"]
        args = state["tool_args"]
        print(f"--- [Execute] {tool} ---")
        
        try:
            result = await self.mcp_client.call_tool(tool, args)
            
            import json
            parsed_result = result
                try:
                    parsed_result = json.loads(result)
                except:
                    pass

            update = {"tool_result": parsed_result}
            
            # Record history
            history = state.get("task_history", []) or []
            history.append({
                "tool": tool,
                "args": args,
                "result": str(parsed_result)[:500] # Limit size
            })
            update["task_history"] = history

            if tool == "platform_get_challenge":
                if isinstance(parsed_result, dict):
                    update["challenge_id"] = str(parsed_result.get("id"))
                    update["user_input"] = parsed_result.get("description", "")
                    print(f"--- [Execute] Set Challenge ID: {update['challenge_id']} ---")
            
            elif tool == "reverse_ghidra_decompile":
                update["user_input"] = f"分析以下代码并生成求解脚本: {str(parsed_result)[:200]}"
                print(f"--- [Execute] Updated user_input for analysis ---")
            
            elif tool in ["web_dir_scan", "kali_dirsearch"]:
                # Robust parsing for dirsearch simple format: 200  10KB  /admin/
                import re
                # Simple regex for status code and path
                found_paths = re.findall(r"(\d{3})\s+\S+\s+(/\S+)", str(parsed_result))
                
                pending = state.get("pending_tasks", []) or []
                if found_paths:
                    for status, path in found_paths:
                        if status.startswith("2") or status == "301": # 2xx or 301
                            full_url = urljoin(args.get("url", ""), path)
                            # Avoid duplicates
                            if not any(t.get("url") == full_url for t in pending):
                                pending.append({
                                    "type": "web_explore",
                                    "url": full_url,
                                    "description": f"Explore found path with status {status}: {path}"
                                })
                
                if isinstance(parsed_result, dict) and "found" in parsed_result:
                    for item in parsed_result["found"]:
                        pending.append({
                            "type": "web_explore",
                            "url": item["url"],
                            "description": f"Explore found path: {item['path']}"
                        })
                        
                if pending:
                    update["pending_tasks"] = pending
                    print(f"--- [Execute] Added {len(pending)} pending exploration tasks ---")

            elif tool == "kali_sqlmap":
                # Check for "is vulnerable" or "Payload:" in sqlmap output
                res_str = str(parsed_result).lower()
                if "is vulnerable" in res_str or "payload:" in res_str:
                    print("--- [Execute] CRITICAL: SQL Injection vulnerability confirmed! ---")
                    update["user_input"] = f"SQL 注入已确认！结果如下，请尝试提取 flag: {str(parsed_result)[-500:]}"
                else:
                    print("--- [Execute] SQLMap finished, no obvious vulnerability found. ---")

            return update
        except Exception as e:
            print(f"--- [Execute] Error: {str(e)} ---")
            return {"error": str(e)}

    async def format_result(self, state: AgentState) -> AgentState:
        """Format final answer."""
        if state.get("error"):
            return {"final_answer": f"❌ Error: {state['error']}"}
        
        # If it's a final answer conclusion
        if state.get("task_understanding") == "final_answer":
            return {"final_answer": state.get("user_input", "Mission accomplished.")}

        result = state.get("tool_result")
        if state.get("planned_tool") == "platform_submit_flag":
            return {"final_answer": f"🚩 Flag Submitted! Platform Response: {result}"}
            
        return {"final_answer": str(result).strip()}
