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

@click.command()
@click.argument('input_text', required=False)
@click.option('--url', help='CTF challenge URL for automatic fetching')
@click.option('--token', help='CTF platform API token')
@click.option('--llm', type=click.Choice(['mock', 'claude']), default='mock', help='LLM provider to use')
@click.option('--api-key', help='Anthropic API Key', envvar='ANTHROPIC_API_KEY')
@click.option('--v2/--v1', default=False, help='Use v2 ReAct architecture')
@click.option('--v3', is_flag=True, help='Use v3 Multi-Agent architecture')
@click.option('--config', help='Path to v3 configuration YAML')
def main(input_text, url, token, llm, api_key, v2, v3, config):
    """ASAS Agent CLI - Execute CTF tasks."""

    if not input_text and not url:
        click.echo("Error: Either INPUT_TEXT or --url must be provided", err=True)
        return

    async def run_v3():
        from asas_agent.graph.workflow import create_orchestrator_graph
        from asas_agent.mcp_client.client import MCPToolClient
        from asas_agent.llm.tool_adapter import convert_mcp_to_langchain_tools
        from asas_agent.llm.factory import create_llm
        from asas_agent.graph.dispatcher import dispatch_to_agent
        from langchain_core.messages import HumanMessage
        
        cfg = load_v3_config(config)
        
        # 1. Setup Tools
        client = MCPToolClient()
        try:
            all_tools = await convert_mcp_to_langchain_tools(client)
            
            # 过滤：指挥官只需要核心工具，减轻本地模型压力
            core_tool_names = ["platform_get_challenge", "platform_submit_flag", "dispatch_to_agent"]
            tools = [t for t in all_tools if t.name in core_tool_names]
            
            # 如果 dispatch_to_agent 不在 MCP 里（它是装饰器定义的），手动添加
            if not any(t.name == "dispatch_to_agent" for t in tools):
                tools.append(dispatch_to_agent)
                
            print(f"✅ Loaded {len(tools)} core tools for Orchestrator (from total {len(all_tools)}).")
        except Exception as e:
            print(f"❌ Failed to load tools: {e}")
            return

        # 2. Setup Orchestrator LLM
        orch_cfg = cfg["orchestrator"]
        if llm == 'mock':
            from asas_agent.llm.mock_react import ReActMockLLM
            orch_llm = ReActMockLLM()
        else:
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
        
        async for event in app.astream(state):
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
        
        if llm == 'claude':
            from asas_agent.llm.langchain_claude import create_langchain_claude
            llm_provider = create_langchain_claude(api_key=api_key)
        else:
            from asas_agent.llm.mock_react import ReActMockLLM
            llm_provider = ReActMockLLM()
            
        print(f"🧠 Initializing v2 ReAct Agent ({'Claude' if llm == 'claude' else 'Mock'})...")
        app = create_react_agent_graph(llm_provider, tools)
        initial_msg = input_text or f"Fetching challenge from {url}"
        inputs = {"messages": [HumanMessage(content=initial_msg)]}
        if url: inputs["platform_url"] = url
        if token: inputs["platform_token"] = token

        print(f"🚀 Starting v2 Mission: {initial_msg}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        async for event in app.astream(inputs):
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
        else:
            from asas_agent.llm.mock import MockLLM
            llm_provider = MockLLM()

        app = create_agent_graph(llm_provider)
        
        initial_msg = input_text or f"Fetching challenge from {url}"
        inputs = {
            "user_input": initial_msg,
            "platform_url": url,
            "platform_token": token
        }

        print(f"🚀 Starting v1 Mission: {initial_msg}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # v1 doesn't support astream as well as v2, we'll use invoke
        result = await app.ainvoke(inputs)
        print(f"🏁 Final Answer: {result.get('final_answer')}")
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ v1 Mission Complete")

    if v3:
        asyncio.run(run_v3())
    elif v2:
        asyncio.run(run_v2())
    else:
        asyncio.run(run_v1())

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1:3] == ['-m', 'asas_mcp']:
        run_server()
    else:
        main()
