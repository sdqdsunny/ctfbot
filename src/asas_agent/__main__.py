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
def main(input_text, url, token, llm, api_key):
    """ASAS Agent CLI - Execute CTF tasks."""
    
    # Add src to path for standard imports if running from source
    # (Optional but helpful for development)
    
    from asas_agent.graph.workflow import create_agent_graph
    from asas_agent.llm.mock import MockLLM
    from asas_agent.llm.claude import ClaudeLLM

    if not input_text and not url:
        click.echo("Error: Either INPUT_TEXT or --url must be provided", err=True)
        return
    
    print(f"🤖 ASAS Agent ({llm.capitalize()} Mode)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
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
    
    async def run():
        result = await app.ainvoke(inputs)
        
        print(f"📝 理解: {result.get('task_understanding')}")
        print(f"🔧 规划: {result.get('planned_tool')} {result.get('tool_args')}")
        print(f"⚙️  结果: {result.get('tool_result')}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🎯 最终答案: {result.get('final_answer')}")

    asyncio.run(run())

if __name__ == '__main__':
    # Bundle Role Switching logic:
    # If the second argument is '-m' and the third is 'asas_mcp', run the server.
    # This must be checked BEFORE calling the Click-decorated main function.
    if len(sys.argv) > 2 and sys.argv[1:3] == ['-m', 'asas_mcp']:
        run_server()
    else:
        main()
