import asyncio
import click
import os
import sys
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

# Import asas_mcp to ensure PyInstaller bundles it
import asas_mcp.server
import asas_mcp.__main__

load_dotenv()

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
@click.option('--llm', type=click.Choice(['mock', 'claude', 'openai', 'lmstudio', 'config']), default='config', help='LLM provider to use')
@click.option('--api-key', help='Anthropic API Key', envvar='ANTHROPIC_API_KEY')
@click.option('--v2/--v1', default=False, help='Use v2 ReAct architecture')
@click.option('--v3', is_flag=True, help='Use v3 Multi-Agent architecture')
@click.option('--config', help='Path to v3 configuration YAML')
def main_cli(input_text, url, token, llm, api_key, v2, v3, config):
    """ASAS Agent CLI - Execute CTF tasks."""
    print(f"DEBUG: main_cli entered. args: input={input_text}, llm={llm}, v3={v3}, v2={v2}") # DEBUG

    if not input_text and not url:
        click.echo("Error: Either INPUT_TEXT or --url must be provided", err=True)
        return

    async def run_v3():
        print("DEBUG: run_v3 started") # DEBUG
        from asas_agent.graph.workflow import create_orchestrator_graph
        from asas_agent.mcp_client.client import MCPToolClient
        from asas_agent.llm.tool_adapter import convert_mcp_to_langchain_tools
        from asas_agent.llm.factory import create_llm
        from asas_agent.graph.dispatcher import dispatch_to_agent
        from asas_agent.llm.factory import create_llm
        from asas_agent.graph.dispatcher import dispatch_to_agent
        from langchain_core.messages import HumanMessage
        
        from asas_agent.utils.config import config_loader
        cfg = config_loader.load_config(config) if config else config_loader.load_config("v3_config.yaml")
        
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
                "sandbox_run_python",
                "vnc_capture_screen",
                "vnc_mouse_click",
                "vnc_keyboard_type",
                "vnc_send_key"
            ]
            tools = [t for t in all_tools if t.name in core_tool_names]
            
            # 手动确认 dispatch_to_agent 存在
            if not any(t.name == "dispatch_to_agent" for t in tools):
                tools.append(dispatch_to_agent)
                
            print(f"✅ Loaded {len(tools)} core tools for Orchestrator (from total {len(all_tools)}).")
        except Exception as e:
            print(f"❌ Failed to load tools: {e}")
            return

        # 2. Setup Orchestrator LLM
        orch_cfg = cfg["orchestrator"]
        if llm == 'openai':
            # Use DeepSeek as default for 'openai' choice if not in config
            if "api_key" not in orch_cfg:
                orch_cfg["api_key"] = api_key or os.environ.get("DEEPSEEK_API_KEY")
            if "base_url" not in orch_cfg:
                orch_cfg["base_url"] = "https://api.deepseek.com/v1"
            if "model" not in orch_cfg:
                orch_cfg["model"] = "deepseek-chat"
            orch_cfg["provider"] = "openai"
        
        if llm == 'mock':
            from asas_agent.llm.mock_react import ReActMockLLM
            orch_llm = ReActMockLLM()
        else:
            if llm != 'config':
                orch_cfg["provider"] = llm
            orch_llm = create_llm(orch_cfg)
            
        # 3. Build Graph
        print(f"🧠 Initializing v3 Multi-Agent Orchestrator ({orch_cfg.get('model')})...")
        app = create_orchestrator_graph(orch_llm, tools)
        
        # 4. Prepare Workflow
        initial_msg = input_text or f"Scan platform {url} and solve challenges."
        state = {"messages": [HumanMessage(content=initial_msg)]}
        if url: state["platform_url"] = url
        if token: state["platform_token"] = token

        # 5. Execute
        print(f"🚀 Starting v3 Multi-Agent Mission: {initial_msg}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        async for event in app.astream(state, config={"recursion_limit": 100}):
            if not isinstance(event, dict):
                continue
            for key, value in event.items():
                if key == "orchestrator":
                    msg = value["messages"][-1]
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"👑 指挥官决策: 调用工具 {tc['name']}")
                            print(f"   目标/参数: {tc['args'].get('agent_type') or tc['args']}")
                    else:
                        print(f"💡 最终报告: {msg.content}")
                elif key == "tools":
                    for msg in value["messages"]:
                        print(f"📥 代理返回 ({msg.name}): {str(msg.content)[:150]}...")
                        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ v3 Mission Complete")

    async def run_v2():
        from asas_agent.graph.workflow import create_react_agent_graph
        from asas_agent.llm.tool_adapter import convert_mcp_to_langchain_tools
        from asas_agent.mcp_client.client import MCPToolClient
        from langchain_core.messages import HumanMessage
        
        client = MCPToolClient()
        tools = await convert_mcp_to_langchain_tools(client)
        
        from asas_agent.utils.config import config_loader
        from asas_agent.llm.factory import create_llm
        cfg = config_loader.load_config(config) if config else config_loader.load_config("v3_config.yaml")
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
                elif key == "tools":
                    for msg in value["messages"]:
                        print(f"📥 工具返回 ({msg.name}): {str(msg.content)[:200]}...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ v2 Mission Complete")

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
        current_config = config_loader.load_config(config) if config else config_loader.load_config("v3_config.yaml")
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
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ v1 Mission Complete")

    if v3:
        asyncio.run(run_v3())
    elif v2:
        asyncio.run(run_v2())
    else:
        asyncio.run(run_v1())

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
