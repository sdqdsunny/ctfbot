from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import json
import re

from .state import AgentState
from ..llm.base import LLMProvider
from ..mcp_client.client import MCPToolClient

import logging
logger = logging.getLogger(__name__)

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

        # 启发式覆盖：如果输入中明确提到了某个工具，且当前处于重试/调度状态
        trigger_phrases = ["请立即使用", "请尝试使用", "请使用"]
        for t in ["kali_sqlmap", "kali_nmap", "kali_dirsearch", "kali_exec", "web_extract_links", "platform_fetch", "open_vm_vnc"]:
            if t in state['user_input'] and any(p in state['user_input'] for p in trigger_phrases):
                print(f"--- [Understand] Heuristic Match: {t} ---")
                
                if t == "open_vm_vnc":
                    t = "open_vm_vnc"
                # 清除强制指令，避免循环
                new_input = state['user_input']
                for p in trigger_phrases:
                    new_input = new_input.replace(f"{p} {t}", "").replace(p, "")
                return {"task_understanding": t, "user_input": new_input}

        prompt = (
            f"当前任务: {state['user_input']}\n{history_context}\n"
            "请从以下选项中选择下一步的最优意图（仅输出意图名称，如 kali_sqlmap, kali_nmap, recon_scan, open_vm_vnc, final_answer 等）:\n"
            "[kali_sqlmap, kali_nmap, kali_dirsearch, kali_exec, recon_scan, crypto_decode, platform_fetch, web_extract_links, open_vm_vnc, final_answer]\n"
            "注意：必须仅输出意图名字，严禁任何解释或推理。"
        )
        messages = [{"role": "user", "content": prompt}]
        
        raw_understanding = self.llm.chat(messages)
        
        # Strip <thought> or <think> tags if present
        import re
        clean_understanding = re.sub(r"<(thought|think)>.*?</\1>", "", str(raw_understanding), flags=re.DOTALL | re.IGNORECASE).strip()
        
        # Take only the first word or last word if it's a sentence
        # Some models might still be chatty
        intent_match = re.search(r"\b(kali_sqlmap|kali_nmap|kali_dirsearch|kali_exec|recon_scan|crypto_decode|platform_fetch|web_extract_links|open_vm_vnc|final_answer)\b", clean_understanding)
        understanding = intent_match.group(1) if intent_match else clean_understanding.split()[-1]

        print(f"--- [Understand] LLM Intent: {understanding} ---")
        return {"task_understanding": understanding}

    async def _extract_url(self, text: str, state_url: Optional[str] = None) -> str:
        url_match = re.search(r"(https?://[a-zA-Z0-9\.\-:/\?&=_%#]+)", text)
        return url_match.group(1) if url_match else (state_url or "")

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
                "tool_args": {"url": state.get("platform_url", ""), "token": state.get("platform_token")}
            }
            
        # 2. Standard MVP Tools with LLM parameter extraction
        if intent in ["kali_sqlmap", "kali_dirsearch", "kali_nmap", "kali_exec", "kali_steghide", "kali_zsteg", "kali_binwalk", "kali_foremost", "kali_tshark", "web_extract_links", "recon_scan"]:
            prompt = (
                f"任务: {user_input}\n"
                f"意图: {intent}\n"
                "请提取执行此意图所需的参数，并以 JSON 格式返回。\n"
                "注意：仅输出 JSON，不要有任何解释。"
            )
            # Add specific hints per tool
            if intent == "kali_sqlmap": 
                prompt += "\n格式要求: {\"url\": \"目标URL\", \"args\": \"--batch --banner\"}\n"
                prompt += "如果任务提到表单或 POST，请在 args 中包含 --data '字段1=值1&字段2=值2'，并建议添加 --level 3 --risk 3 以增强探测能力。"
            elif intent == "kali_exec":
                prompt += "\n格式要求: {\"cmd_str\": \"要执行的命令\"}"
            elif intent == "recon_scan":
                prompt += "\n格式要求: {\"target\": \"URL/IP\"}"
                prompt += "\n注意：必须使用 'target' 键名，不要使用 'target_url'。"
            elif intent == "kali_nmap":
                prompt += "\n格式要求: {\"target\": \"IP\", \"args\": \"-F\"}"
            elif intent in ["kali_dirsearch", "web_extract_links"]:
                prompt += "\n格式要求: {\"url\": \"目标URL\"}"
            elif intent in ["kali_steghide", "kali_zsteg", "kali_binwalk", "kali_foremost", "kali_tshark"]:
                prompt += "\n格式要求: {\"file_path\": \"文件路径\"}"
                
            messages = [{"role": "user", "content": prompt}]
            raw_params = self.llm.chat(messages)
            
            # Clean reasoning tags (thought or think) and parse JSON
            import re
            clean_params = re.sub(r"<(thought|think)>.*?</\1>", "", str(raw_params), flags=re.DOTALL | re.IGNORECASE).strip()
            logger.debug(f"DEBUG [Plan] Cleaned LLM params output: {clean_params[:200]}...")
            
            try:
                # Find the first { and last }
                json_match = re.search(r"(\{.*\})", clean_params, re.DOTALL)
                if json_match:
                    params = json.loads(json_match.group(1))
                    # Normalization
                    if "target_url" in params and "target" not in params:
                        params["target"] = params["target_url"]
                        
                    # Post-process for common issues
                    for key in ["args", "cmd_str"]:
                        if key in params and isinstance(params[key], list):
                            params[key] = " ".join(params[key])
                            
                    return {
                        "planned_tool": intent,
                        "tool_args": params
                    }
            except Exception as e:
                print(f"FAILED to parse params from LLM: {e}")

        # --- Fallbacks if LLM extraction fails ---
        if intent == "kali_sqlmap":
            url = await self._extract_url(user_input, state.get("platform_url"))
            return {
                "planned_tool": "kali_sqlmap",
                "tool_args": {"url": url, "args": "--batch --banner --current-db"}
            }
        elif intent == "kali_dirsearch":
            url = await self._extract_url(user_input, state.get("platform_url"))
            return {
                "planned_tool": "kali_dirsearch",
                "tool_args": {"url": url}
            }
        elif intent == "kali_nmap":
            raw_url = await self._extract_url(user_input, "127.0.0.1")
            target = raw_url.replace("http://", "").replace("https://", "").split("/")[0]
            return {
                "planned_tool": "kali_nmap",
                "tool_args": {"target": target}
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
        
        elif intent == "open_vm_vnc":
            vm = "pentest-windows" if "windows" in user_input.lower() else "kali"
            return {
                "planned_tool": "open_vm_vnc",
                "tool_args": {"vm_name": vm}
            }

        elif intent == "crypto_decode":
            # Extract content after colon or the last token
            if ":" in user_input:
                content = user_input.split(":", 1)[-1].strip()
            else:
                content = user_input.split(" ")[-1].strip()
            return {
                "planned_tool": "crypto_decode",
                "tool_args": {"content": content}
            }

        elif intent == "reverse_ghidra_decompile":
            path = user_input.split(" ")[-1] if " " in user_input else "binary"
            return {
                "planned_tool": "reverse_ghidra_decompile",
                "tool_args": {"file_path": path}
            }

        elif intent == "generate_solver":
            code = user_input.split(":", 1)[-1].strip() if ":" in user_input else user_input
            return {
                "planned_tool": "sandbox_execute",
                "tool_args": {"code": code, "language": "python"}
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
            
            elif tool == "recon_scan":
                pending = state.get("pending_tasks", []) or []
                res_str = str(parsed_result).lower()
                # If web port found, add dirsearch and sqlmap
                if "80" in res_str or "http" in res_str:
                    pending.append({
                        "type": "dir_scan",
                        "description": f"勘测发现 80 端口开放，请立即使用 kali_dirsearch 扫描敏感目录：{args.get('target')}"
                    })
                    pending.append({
                        "type": "sqli_test",
                        "description": f"勘测发现 Web 服务，请尝试使用 kali_sqlmap 进行初步注入探测：{args.get('target')}"
                    })
                
                if pending:
                    update["pending_tasks"] = pending
                    print(f"--- [Execute] Added {len(pending)} tasks from recon results ---")
            
            elif tool in ["web_dir_scan", "kali_dirsearch"]:
                # Robust parsing for dirsearch simple format: 200  10KB  /admin/
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
            elif tool == "web_extract_links":
                pending = state.get("pending_tasks", []) or []
                
                if isinstance(parsed_result, dict):
                    forms = parsed_result.get("forms", [])
                    if forms:
                        for f in forms:
                            action = f.get("action")
                            method = f.get("method", "get").upper()
                            inputs = f.get("inputs", [])
                            target_url = urljoin(args.get("url", ""), action) if action else args.get("url")
                            
                            # Build a more specific task
                            data_str = "&".join([f"{i}=admin" for i in inputs])
                            description = f"发现 {method} 表单 -> {target_url}，参数: {inputs}。请立即使用 kali_sqlmap 进行渗透测试。参数建议: --data '{data_str}' --level 3 --risk 3 --batch --banner"
                            
                            if not any(t.get("description") == description for t in pending):
                                pending.append({
                                    "type": "sqli_test",
                                    "description": description
                                })
                
                # Fallback if parsing fails but string contains "form"
                elif "form" in str(parsed_result).lower():
                    pending.append({
                        "type": "sqli_test",
                        "description": f"发现页面包含表单，尝试进行 POST 注入测试：{args.get('url')}. 请立即使用 kali_sqlmap --level 3 --risk 3"
                    })
                
                if pending:
                    update["pending_tasks"] = pending
                    print(f"--- [Execute] Added {len(pending)} pending tasks from link extraction ---")

            elif tool == "kali_sqlmap":
                # Check for "is vulnerable" or "Payload:" in sqlmap output
                res_str = str(parsed_result).lower()
                if "is vulnerable" in res_str or "payload:" in res_str or "fetching banner" in res_str or "retrieved:" in res_str:
                    print("--- [Execute] CRITICAL: SQL Injection vulnerability confirmed! ---")
                    update["user_input"] = f"SQL 注入已确认！结果如下，请尝试提取 flag: {str(parsed_result)[-500:]}"
                elif "all tested parameters do not appear to be injectable" in res_str or "skipping to the next target" in res_str or "none of the provided parameters seem to be injectable" in res_str:
                    print(f"--- [Execute] SQLMap failed. Full result preview: {res_str[:1000]} ---")
                    # Update input to guide the next Understand phase
                    update["user_input"] = f"SQL注入测试未发现漏洞。由于任务尚未完成，请立即使用 web_extract_links 提取页面表单，寻找可能存在的 POST 注入点：{args.get('url') or state.get('platform_url')}"
                else:
                    print(f"--- [Execute] SQLMap finished with ambiguous result. Output: {res_str[:500]} ---")
                    update["user_input"] = f"SQL注入扫描结束，但未明确确认漏洞。请尝试 web_extract_links 寻找其它入口或 check.php。"

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
        result_str = str(result).strip()
        
        if state.get("planned_tool") == "platform_submit_flag":
            return {"final_answer": f"🚩 Flag Submitted! Platform Response: {result}"}
        
        # Post-process sqlmap results
        if state.get("planned_tool") == "kali_sqlmap":
            if "vulnerable" in result_str.lower() or "vulnerability" in result_str.lower():
                return {"final_answer": f"SQL 注入已确认。{result_str}"}
        
        # Post-process results with flags
        if "flag{" in result_str.lower():
            return {"final_answer": f"🚩 Flag Found: {result_str}"}
            
        return {"final_answer": result_str}
