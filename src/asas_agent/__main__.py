import asyncio
import logging
import click
import os
import sys
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

from asas_agent.utils.config import ConfigNotFoundError

# Import asas_mcp to ensure PyInstaller bundles it
import asas_mcp.server
import asas_mcp.__main__

load_dotenv()

import re as _re
from urllib.parse import urlparse as _urlparse

def _generate_smart_instruction(url: str) -> str:
    """Generate a context-aware initial instruction based on URL patterns."""
    parsed = _urlparse(url)
    path = parsed.path.lower()
    host = parsed.hostname or ""
    port = parsed.port or 80
    
    # sqli-labs detection
    if _re.search(r'less-?\d+', path, _re.IGNORECASE) or 'sqli' in path:
        return (
            f"这是一道 SQL 注入题目（sqli-labs），目标地址为 {url}。"
            f"端口 {port} 已知，无需 nmap 扫描。"
            f"请立即使用 kali_sqlmap 工具，对 {url}?id=1 进行 SQL 注入检测。"
            f"具体步骤：1) --dbs 列出数据库  2) -D 数据库名 --tables  3) --dump 导出数据，寻找 flag。"
            f"使用 --batch 参数自动确认。"
        )
    
    # XSS detection
    if 'xss' in path:
        return (
            f"这是一道 XSS 跨站脚本题目，目标地址为 {url}。"
            f"请使用 kali_exec 配合 curl 分析页面，寻找可注入的参数。"
        )
    
    # File upload detection
    if 'upload' in path:
        return (
            f"这是一道文件上传漏洞题目，目标地址为 {url}。"
            f"请先用 kali_dirsearch 探测目录结构，然后分析上传接口的过滤机制。"
        )
    
    # General web challenge
    return (
        f"请对目标 {url} 进行安全审计。"
        f"端口 {port} 上已有 Web 服务运行，无需 nmap 端口扫描。"
        f"请优先使用 kali_sqlmap 检测 SQL 注入，同时用 kali_dirsearch 扫描目录。"
    )

# ── 退出码约定 ───────────────────────────────────────────────────────────
# 脚本/CI 需要据此判断任务结果，因此这里把"跑完了但没拿到 flag"与"跑挂了"
# 区分开，而不是一律返回 0（改造前无论成功失败都是 0，调用方无从判断）。
EXIT_OK = 0             # 任务完成且拿到 flag
EXIT_RUN_ERROR = 1      # 运行期间出错（异常、工具加载失败等）
EXIT_STARTUP_ERROR = 2  # 无法启动（配置文件缺失、未提供目标）
EXIT_NO_FLAG = 3        # 任务跑完但未拿到 flag


class StartupError(RuntimeError):
    """前置条件不满足，任务根本没开始跑。

    与"任务跑完但没拿到 flag"是两回事：前者是环境问题（该退出码 2，让调用方
    去修环境），后者是任务结果问题（退出码 3）。混在一起会让 CI 无法分辨
    "机器没配好"和"这题没过"。
    """


def _ensure_dispatch_tool(tools: list) -> list:
    """把 dispatch_to_agent 补进工具列表。

    它不是 MCP 工具——不来自 convert_mcp_to_langchain_tools()，而是本仓库用
    @tool 定义的本地工具，所以必须手动补进去。这段逻辑原先只写在 v3 里，
    v2 因此漏掉了：模型一旦决定 dispatch_to_agent，只会拿到
    "Tool 'dispatch_to_agent' not found"，任务当场失败。
    提成公共函数就是为了避免两条路径再次各写一份而漂移。
    """
    from asas_agent.graph.dispatcher import dispatch_to_agent

    if not any(t.name == "dispatch_to_agent" for t in tools):
        tools.append(dispatch_to_agent)
    return tools


def _collect_flags(accumulator: list, text: str) -> None:
    """把 text 里发现的 flag 并入 accumulator（就地修改，自动去重）。

    复用图里那套 FlagExtractor，避免 CLI 和 agent 对"什么算 flag"有两套判断。
    """
    from asas_agent.graph.verifier import flag_extractor

    for f in flag_extractor.extract(str(text)):
        if f not in accumulator:
            accumulator.append(f)


def load_v3_config(path: str = None) -> Dict[str, Any]:
    """Load v3 multi-agent configuration."""
    if path and os.path.exists(path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    return {
        "orchestrator": {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620"},
        "agents": {}
    }

def run_server():
    """Run the MCP server logic."""
    import asas_mcp.__main__
    asyncio.run(asas_mcp.__main__.main())

@click.group()
def swarm():
    """Swarm management commands."""
    pass

@swarm.command(name="status")
@click.option('--address', help='Ray cluster address')
def swarm_status(address):
    """Check distributed cluster status."""
    from asas_agent.distributed.cluster_manager import ClusterManager
    mgr = ClusterManager(address=address)
    if mgr.initialize():
        status = mgr.get_cluster_status()
        click.echo("🌐 Swarm Cluster Status:")
        for k, v in status.items():
            click.echo(f"  {k}: {v}")
    else:
        click.echo("❌ Failed to connect to Swarm cluster.")

@swarm.command(name="ban")
@click.argument('node_id')
def swarm_ban(node_id):
    """Manually blacklist a node."""
    # In a real implementation, this would state-sync to the Cluster
    click.echo(f"🚫 Node {node_id} has been added to blacklist.")

@click.command()
@click.argument('input_text', required=False)
@click.option('--url', help='CTF challenge URL for automatic fetching')
@click.option('--token', help='CTF platform API token')
@click.option('--llm', type=click.Choice(['mock', 'claude', 'openai', 'deepseek', 'lmstudio', 'config', 'gemini', 'zhipu', 'glm']), default='config', help='LLM provider to use')
@click.option('--api-key', help='Anthropic API Key', envvar='ANTHROPIC_API_KEY')
@click.option('--v2/--v1', default=False, help='Use v2 ReAct architecture')
@click.option('--v3', is_flag=True, help='Use v3 Multi-Agent architecture')
@click.option('--config', help='Path to v3 configuration YAML')
@click.option('--debug', is_flag=True,
              help='输出 DEBUG 级日志（LLM 原始输出、工具调用明细、路由决策等）')
def main_cli(input_text, url, token, llm, api_key, v2, v3, config, debug):
    """ASAS Agent CLI - Execute CTF tasks.

    退出码：0=拿到 flag　1=运行出错　2=无法启动（配置缺失/未给目标）
    　　　　3=任务跑完但未捕获 flag
    """
    # 日志级别：默认 WARNING，与改造前一致（这些明细原先由裸 print 无条件输出，
    # 现已改为 logger.debug）。需要排查时用 --debug 或 ASAS_DEBUG=1 打开。
    log_level = logging.DEBUG if (debug or os.environ.get("ASAS_DEBUG")) else logging.WARNING

    # basicConfig 只在 root 还没有 handler 时才生效。而本模块顶部
    # `import asas_mcp.server` 会经由 mcp 的 fastmcp.utils.logging.configure_logging()
    # 抢先装上 RichHandler 并把 root 级别设成 INFO——那一步发生在本函数之前，
    # 于是下面这行 basicConfig 实际是空操作，级别根本不会被应用。
    # 曾经的后果有两个：--debug 打开后一条 DEBUG 都没有；默认档也压不住
    # chromadb / mcp 的 INFO 噪音。
    # 因此保留 basicConfig（覆盖 root 尚无 handler 的场景，如测试与 ui_server），
    # 再显式设一次 root 级别——这一句不依赖任何前提，才是真正生效的那一步。
    logging.basicConfig(level=log_level, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger().setLevel(log_level)

    # MCP 工具子进程（`python -m asas_mcp`）有自己的日志配置，主进程设级别管不到它：
    # mcp 的 fastmcp 默认按 INFO 装机，于是每次工具调用都会往 stderr 打一行
    # "Processing request of type ..."，出现在每次运行的输出最前面。
    # 子进程环境由 MCPToolClient 以 **os.environ 透传，故在此按同一开关下发级别，
    # 保证父子一致：默认安静，--debug 时两边都出声。
    # 用 setdefault：用户若显式设了 FASTMCP_LOG_LEVEL，以他的为准。
    os.environ.setdefault(
        "FASTMCP_LOG_LEVEL", "DEBUG" if log_level == logging.DEBUG else "WARNING"
    )

    # --llm mock 要对整个进程生效，而不只是顶层那个 LLM：
    # dispatch_to_agent 会另起子代理，子代理按 agent 自己的配置调 create_llm()，
    # dispatcher 只在看到这个开关时才改用 mock。原先只有 v3 设了它，v2 漏了，
    # 于是 v2 的 mock 模式一遇到派发就会打真实 API 请求——用户以为是
    # "无需 API Key 的测试模式"，实际在产生费用。统一放在这里，三条路径都覆盖。
    if llm == 'mock':
        os.environ["ASAS_MOCK_MODE"] = "1"

    if not input_text and not url:
        click.echo("Error: Either INPUT_TEXT or --url must be provided", err=True)
        raise SystemExit(EXIT_STARTUP_ERROR)

    async def run_v3():
        from asas_agent.graph.workflow import create_orchestrator_graph
        from asas_agent.mcp_client.client import MCPToolClient
        from asas_agent.llm.tool_adapter import convert_mcp_to_langchain_tools
        from asas_agent.llm.factory import create_llm
        from langchain_core.messages import HumanMessage

        from asas_agent.utils.config import config_loader
        cfg = config_loader.load_config(config)
        
        # 1. Setup Tools
        client = MCPToolClient()
        try:
            all_tools = await convert_mcp_to_langchain_tools(client)
            
            # 过滤：指挥官只需要核心工具，减轻本地模型和DeepSeek API压力
            # 简化为最核心的三大件：扫描、SQL注入、命令执行
            core_tool_names = [
                "kali_nmap", 
                "kali_sqlmap", 
                "kali_exec", 
                "web_extract_links",
                "dispatch_to_agent",
                "open_vm_vnc",
                "kali_upload_file",
                "kali_file",
                "kali_checksec",
                "reverse_ghidra_decompile",
                "ghidra_list_functions",
                "ghidra_decompile_function",
                "sandbox_execute",
                "vnc_capture_screen",
                "vnc_mouse_click",
                "vnc_keyboard_type",
                "vnc_send_key",
                "kali_pwn_cyclic",
                "kali_pwn_gdb"
            ]
            tools = [t for t in all_tools if t.name in core_tool_names]
            _ensure_dispatch_tool(tools)

            print(f"✅ Loaded {len(tools)} core tools for Orchestrator (from total {len(all_tools)}).")
        except Exception as e:
            # 原先这里是 print 一行错误然后 return —— 进程照样以 0 退出，
            # 调用方（含 ui_server）无法把它和成功区分开。
            # 工具加载不出来属于"环境没准备好"，抛 StartupError 走退出码 2。
            raise StartupError(f"加载 MCP 工具失败: {e}") from e

        # 2. Setup Orchestrator LLM
        orch_cfg = cfg["orchestrator"]
        if llm == 'openai':
            # Use DeepSeek as default for 'openai' choice if not in config
            if "api_key" not in orch_cfg:
                orch_cfg["api_key"] = api_key or os.environ.get("DEEPSEEK_API_KEY")
            if "base_url" not in orch_cfg:
                orch_cfg["base_url"] = "https://api.deepseek.com/v1"
            orch_cfg["model"] = "deepseek-chat"
            orch_cfg["provider"] = "openai"
            
        if llm == 'claude':
            orch_cfg["provider"] = "anthropic"
            if "api_key" not in orch_cfg:
                orch_cfg["api_key"] = api_key or os.environ.get("ANTHROPIC_API_KEY")
            orch_cfg["model"] = "claude-3-5-sonnet-20240620"
        
        if llm == 'gemini':
            orch_cfg["provider"] = "google"
            if "api_key" not in orch_cfg:
                orch_cfg["api_key"] = api_key or os.environ.get("GOOGLE_API_KEY")
            orch_cfg["model"] = "gemini-2.5-flash"

        if llm == 'deepseek':
            orch_cfg["provider"] = "deepseek"
            # 优先使用用户提供的 Key
            orch_cfg["api_key"] = api_key or os.environ.get("DEEPSEEK_API_KEY")
            if "model" not in orch_cfg:
                orch_cfg["model"] = "deepseek-chat"
            if "base_url" not in orch_cfg:
                orch_cfg["base_url"] = "https://api.deepseek.com/v1"
        
        if llm == 'zhipu' or llm == 'glm':
            orch_cfg["provider"] = "zhipu"
            if "api_key" not in orch_cfg:
                orch_cfg["api_key"] = api_key or os.environ.get("ZHIPU_API_KEY")
            orch_cfg["model"] = "glm-4-plus"
        
        if llm == 'mock':
            # ASAS_MOCK_MODE 已在 main_cli 里统一设置（覆盖 v1/v2/v3 与子代理）
            from asas_agent.llm.mock_react import ReActMockLLM
            orch_llm = ReActMockLLM()
        else:
            if llm != 'config' and llm not in ['openai', 'claude', 'gemini', 'zhipu', 'glm', 'deepseek']:
                orch_cfg["provider"] = llm
            orch_llm = create_llm(orch_cfg)
            
        # 3. Build Graph
        print(f"🧠 Initializing v3 Multi-Agent Orchestrator ({orch_cfg.get('model')})...")
        app = create_orchestrator_graph(orch_llm, tools)
        
        # 4. Prepare Workflow - Generate smart initial instructions
        if input_text:
            initial_msg = input_text
        elif url:
            initial_msg = _generate_smart_instruction(url)
        else:
            initial_msg = "Awaiting instructions."
        state = {"messages": [HumanMessage(content=initial_msg)]}
        if url: state["platform_url"] = url
        if token: state["platform_token"] = token

        # 5. Execute
        print(f"🚀 Starting v3 Multi-Agent Mission: {initial_msg}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        from asas_agent.utils.ui_emitter import ui_emitter

        found_flags: list[str] = []

        async for event in app.astream(state, config={"recursion_limit": 100}):
            if not isinstance(event, dict):
                continue
            for key, value in event.items():
                if key == "orchestrator":
                    msg = value["messages"][-1]
                    tools_used = []
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            tools_used.append({"name": tc["name"], "args": tc.get("args", {})})
                            print(f"👑 指挥官决策: 调用工具 {tc['name']}")
                            print(f"   目标/参数: {tc['args'].get('agent_type') or tc['args']}")
                    else:
                        print(f"💡 最终报告: {msg.content}")
                        _collect_flags(found_flags, msg.content)

                    ui_emitter.emit("orchestrator_message", {
                        "content": msg.content,
                        "tool_calls": tools_used
                    })
                elif key == "tools":
                    for msg in value["messages"]:
                        content_str = str(msg.content)[:500]
                        print(f"📥 代理返回 ({msg.name}): {content_str[:150]}...")
                        _collect_flags(found_flags, msg.content)

                        ui_emitter.emit("tool_result", {
                            "tool_name": msg.name,
                            "content": content_str,
                            "is_error": "Error:" in content_str or "Failed" in content_str
                        })
                # flag_capture 节点会把已捕获的 flag 写进 state，直接采信它
                for f in value.get("extracted_flags") or []:
                    if f not in found_flags:
                        found_flags.append(f)

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        if found_flags:
            print(f"🏁 v3 Mission Complete — 捕获 flag: {found_flags}")
        else:
            print("✅ v3 Mission Complete（未捕获 flag）")
        return bool(found_flags)

    async def run_v2():
        from asas_agent.graph.workflow import create_react_agent_graph
        from asas_agent.llm.tool_adapter import convert_mcp_to_langchain_tools
        from asas_agent.mcp_client.client import MCPToolClient
        from langchain_core.messages import HumanMessage
        
        client = MCPToolClient()
        tools = await convert_mcp_to_langchain_tools(client)
        # v2 原先漏了这一步（只有 v3 注册了 dispatch_to_agent），
        # 结果是模型一决定派发子代理就拿到 "Tool not found"，任务当场哑火。
        _ensure_dispatch_tool(tools)
        
        from asas_agent.utils.config import config_loader
        from asas_agent.llm.factory import create_llm
        cfg = config_loader.load_config(config)
        orch_cfg = cfg["orchestrator"]
        
        # Apply command line overrides
        if llm == 'openai':
            orch_cfg["api_key"] = api_key or os.environ.get("DEEPSEEK_API_KEY")
            orch_cfg["base_url"] = "https://api.deepseek.com/v1"
            orch_cfg["model"] = "deepseek-reasoner"
            orch_cfg["provider"] = "openai"

        if llm == 'claude':
            from asas_agent.llm.langchain_claude import create_langchain_claude
            llm_provider = create_langchain_claude(api_key=api_key)
        elif llm == 'mock':
            from asas_agent.llm.mock_react import ReActMockLLM
            llm_provider = ReActMockLLM()
        else:
            llm_provider = create_llm(orch_cfg)
            
        print(f"🧠 Initializing v2 ReAct Agent ({llm_provider._llm_type if hasattr(llm_provider, '_llm_type') else 'Generic'})...")
        app = create_react_agent_graph(llm_provider, tools)
        initial_msg = input_text or f"Fetching challenge from {url}"
        inputs = {"messages": [HumanMessage(content=initial_msg)]}
        if url: inputs["platform_url"] = url
        if token: inputs["platform_token"] = token

        print(f"🚀 Starting v2 Mission: {initial_msg}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        found_flags: list[str] = []

        async for event in app.astream(inputs):
            if not isinstance(event, dict):
                continue
            for key, value in event.items():
                if key == "agent":
                    msg = value["messages"][-1]
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"🤔 思考中... 调用工具: {tc['name']}")
                            print(f"   参数: {tc['args']}")
                    else:
                        print(f"💡 最终结果: {msg.content}")
                        _collect_flags(found_flags, msg.content)
                elif key == "tools":
                    for msg in value["messages"]:
                        print(f"📥 工具返回 ({msg.name}): {str(msg.content)[:200]}...")
                        _collect_flags(found_flags, msg.content)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        if found_flags:
            print(f"🏁 v2 Mission Complete — 捕获 flag: {found_flags}")
        else:
            print("✅ v2 Mission Complete（未捕获 flag）")
        return bool(found_flags)

    async def run_v1():
        from asas_agent.graph.workflow import create_agent_graph
        from asas_agent.llm.factory import create_llm
        from langchain_core.messages import HumanMessage
        
        # v1 uses a different brain architecture
        print("🧠 Initializing v1 Legacy Agent (Chain-of-Thought)...")
        
        # Setup legacy LLM adapter
        if llm == 'claude':
            # v1 legacy node expects a provider with .chat() method
            # For simplicity, we wrap the factory LLM or use a simple adapter
            from asas_agent.llm.langchain_claude import create_langchain_claude
            raw_llm = create_langchain_claude(api_key=api_key)
            from asas_agent.llm.base import LLMProvider
            class LegacyAdapter(LLMProvider):
                def chat(self, messages):
                    # Convert list of dicts to HumanMessage if needed
                    # Node usually passes simple messages
                    return raw_llm.invoke(messages[0]["content"]).content
            llm_provider = LegacyAdapter()
        
        from asas_agent.utils.config import config_loader
        current_config = config_loader.load_config(config)
        orch_cfg = current_config["orchestrator"]
        
        # Apply command line overrides for v1
        if llm == 'openai':
            orch_cfg["api_key"] = api_key or os.environ.get("DEEPSEEK_API_KEY")
            orch_cfg["base_url"] = "https://api.deepseek.com/v1"
            orch_cfg["model"] = "deepseek-chat"
            orch_cfg["provider"] = "openai"

        if llm == 'mock':
            from asas_agent.llm.mock import MockLLM
            llm_provider = MockLLM()
        else:
            llm_provider = create_llm(orch_cfg)
            # v1 legacy expects a .chat() method or similar
            # If it's a LangChain model, we might need a small wrapper
            if not hasattr(llm_provider, "chat"):
                class LegacyWrapper:
                    def __init__(self, model): self.model = model
                    def chat(self, messages): 
                        # v1 passes list of dicts: [{"role": "user", "content": "..."}]
                        content = messages[-1]["content"]
                        return self.model.invoke(content).content
                llm_provider = LegacyWrapper(llm_provider)

        app = create_agent_graph(llm_provider)
        
        initial_msg = input_text or f"Fetching challenge from {url}"
        inputs = {
            "user_input": initial_msg,
            "platform_url": url,
            "platform_token": token
        }

        print(f"🚀 Starting v1 Mission: {initial_msg}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Increase recursion limit for complex tasks
        config_run = {"recursion_limit": 500}
        result = await app.ainvoke(inputs, config=config_run)
        print(f"🏁 Final Answer: {result.get('final_answer')}")

        # v1 的结果里没有 extracted_flags 字段，就地扫一遍最终答案与历史
        found_flags: list[str] = []
        _collect_flags(found_flags, result.get("final_answer") or "")
        for item in result.get("task_history") or []:
            _collect_flags(found_flags, item)

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        if found_flags:
            print(f"🏁 v1 Mission Complete — 捕获 flag: {found_flags}")
        else:
            print("✅ v1 Mission Complete（未捕获 flag）")
        return bool(found_flags)

    try:
        if v3:
            got_flag = asyncio.run(run_v3())
        elif v2:
            got_flag = asyncio.run(run_v2())
        else:
            got_flag = asyncio.run(run_v1())
    except ConfigNotFoundError as e:
        # 配置缺失属于"环境没准备好"，不是程序缺陷：
        # 给出可执行的补救步骤，而不是甩一屏 Python 栈。
        click.echo(f"\n✗ 启动失败：配置文件缺失\n\n{e}\n", err=True)
        raise SystemExit(EXIT_STARTUP_ERROR)
    except StartupError as e:
        click.echo(f"\n✗ 启动失败：{e}\n", err=True)
        raise SystemExit(EXIT_STARTUP_ERROR)

    # 拿到 flag 才算达成目标。区分 0 / 3 是为了让脚本能分辨
    # "这题过了"和"跑完了但没结果"，两者都不该和"环境挂了"混为一谈。
    if got_flag:
        raise SystemExit(EXIT_OK)
    click.echo(
        "\n⚠ 任务已结束，但未捕获到 flag（退出码 3）。"
        "\n  可用 --debug 查看明细；退出码约定见 run --help。\n",
        err=True,
    )
    raise SystemExit(EXIT_NO_FLAG)

# Update the entry point to handle groups
@click.group()
def cli():
    """ASAS Agent - Distributed CTF Orchestration System."""
    pass

cli.add_command(main_cli, name="run")
cli.add_command(swarm)

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1:3] == ['-m', 'asas_mcp']:
        run_server()
    else:
        cli()
