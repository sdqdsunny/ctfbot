import asyncio
import click
import os
from dotenv import load_dotenv

from .graph.workflow import create_agent_graph
from .llm.mock import MockLLM
from .llm.claude import ClaudeLLM

load_dotenv()

@click.command()
@click.argument('input_text')
@click.option('--llm', type=click.Choice(['mock', 'claude']), default='mock', help='LLM provider to use')
@click.option('--api-key', help='Anthropic API Key', envvar='ANTHROPIC_API_KEY')
def main(input_text, llm, api_key):
    """ASAS Agent CLI - Execute CTF tasks."""
    
    print(f"🤖 ASAS Agent ({llm.capitalize()} Mode)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Select LLM
    if llm == 'claude':
        # Check for local LLM configuration
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        
        if not api_key and not base_url:
            click.echo("Error: API Key required for Claude mode (unless ANTHROPIC_BASE_URL is set)", err=True)
            return

        if base_url:
            print(f"🌐 模式: 本地离线 (Local) -> {base_url}")
        else:
            print(f"☁️  模式: 在线云端 (Online) -> Anthropic API")

        llm_provider = ClaudeLLM(api_key=api_key)
    else:
        llm_provider = MockLLM()
    
    # Run Graph
    app = create_agent_graph(llm_provider)
    
    inputs = {"user_input": input_text}
    
    async def run():
        result = await app.ainvoke(inputs)
        
        print(f"📝 理解: {result.get('task_understanding')}")
        print(f"🔧 规划: {result.get('planned_tool')} {result.get('tool_args')}")
        print(f"⚙️  结果: {result.get('tool_result')}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🎯 最终答案: {result.get('final_answer')}")

    asyncio.run(run())

if __name__ == '__main__':
    main()
