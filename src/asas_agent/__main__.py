import asyncio
import click
import os
import sys
from dotenv import load_dotenv

# Import asas_mcp to ensure PyInstaller bundles it
import asas_mcp.server
import asas_mcp.__main__

load_dotenv()

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
@click.option('--v2/--v1', default=False, help='Use v2 ReAct architecture (default: False)')
def main(input_text, url, token, llm, api_key, v2):
    """ASAS Agent CLI - Execute CTF tasks."""
    
    # Add src to path for standard imports if running from source
    # (Optional but helpful for development)
    
    
    # Imports are now localized to run_v1/run_v2 to avoid circular dependencies or unused imports


    if not input_text and not url:
        click.echo("Error: Either INPUT_TEXT or --url must be provided", err=True)
        return
    
    # Logic moved to run_v1/run_v2

    
    inputs = {
        "user_input": input_text or f"Fetching challenge from {url}",
        "platform_url": url,
        "platform_token": token
    }
    
    # v2 ReAct Mode logic
    async def run_v2():
        from asas_agent.graph.workflow import create_react_agent_graph
        from asas_agent.mcp_client.client import MCPToolClient
        from asas_agent.llm.tool_adapter import convert_mcp_to_langchain_tools
        
        # 1. Setup Tools
        client = MCPToolClient()
        # Ensure client is connected if needed (client.__init__ usually starts the server process)
        
        try:
            print("🔧 Loading tools from MCP server...")
            tools = await convert_mcp_to_langchain_tools(client)
            print(f"✅ Loaded {len(tools)} tools.")
        except Exception as e:
            print(f"❌ Failed to load tools: {e}")
            return

        # 2. Setup LLM
        if llm == 'claude':
            if not api_key:
                click.echo("Error: API Key required for Claude mode", err=True)
                return
            from asas_agent.llm.langchain_claude import create_langchain_claude
            llm_provider = create_langchain_claude(api_key=api_key)
        else:
            from asas_agent.llm.mock_react import ReActMockLLM
            llm_provider = ReActMockLLM()
            
        # 3. Build Graph
        print("🧠 Initializing ReAct Agent...")
        app = create_react_agent_graph(llm_provider, tools)
        
        # 4. Prepare Inputs
        # v2 uses list of messages
        from langchain_core.messages import HumanMessage
        initial_msg = input_text or f"Fetching challenge from {url}"
        if url and not input_text:
             initial_msg = f"Please fetch the challenge from {url} and solve it."
             
        inputs = {"messages": [HumanMessage(content=initial_msg)]}
        if url:
            inputs["platform_url"] = url
        if token:
            inputs["platform_token"] = token

        # 5. Execute
        print(f"🚀 Starting Task: {initial_msg}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        async for event in app.astream(inputs):
            for key, value in event.items():
                if key == "agent":
                    msg = value["messages"][-1]
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"🤔 思考: 决定调用工具 {tc['name']}")
                            print(f"   参数: {tc['args']}")
                    else:
                        print(f"💡 回复: {msg.content}")
                elif key == "tools":
                    # value is {'messages': [ToolMessage, ...]}
                    for msg in value["messages"]:
                        print(f"⚙️  工具输出 ({msg.name}): {str(msg.content)[:200]}...")
                        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        # Final result extraction could be improved
        print("✅ 任务结束")

    # v1 Legacy Mode logic
    async def run_v1():
        # Select LLM
        if llm == 'claude':
            if not api_key:
                click.echo("Error: API Key required for Claude mode", err=True)
                return
            llm_provider = ClaudeLLM(api_key=api_key)
        else:
            llm_provider = MockLLM()
        
        # Run Graph
        app = create_agent_graph(llm_provider)
        
        inputs = {
            "user_input": input_text or f"Fetching challenge from {url}",
            "platform_url": url,
            "platform_token": token
        }
        
        result = await app.ainvoke(inputs)
        
        print(f"📝 理解: {result.get('task_understanding')}")
        print(f"🔧 规划: {result.get('planned_tool')} {result.get('tool_args')}")
        print(f"⚙️  结果: {result.get('tool_result')}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🎯 最终答案: {result.get('final_answer')}")

    if v2:
        asyncio.run(run_v2())
    else:
        asyncio.run(run_v1())

if __name__ == '__main__':
    # Bundle Role Switching logic:
    # If the second argument is '-m' and the third is 'asas_mcp', run the server.
    # This must be checked BEFORE calling the Click-decorated main function.
    if len(sys.argv) > 2 and sys.argv[1:3] == ['-m', 'asas_mcp']:
        run_server()
    else:
        main()
