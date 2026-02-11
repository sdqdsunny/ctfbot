
import asyncio
import os
import sys

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "src"))

from asas_agent.agents.web import create_web_agent
from asas_agent.llm.factory import create_llm
from asas_agent.graph.tools_factory import get_tools_for_agent
from langchain_core.messages import HumanMessage

async def main():
    config = {
        "provider": "lmstudio",
        "model": "openai/gpt-oss-20b",
        "base_url": "http://127.0.0.1:1234/v1"
    }
    
    llm = create_llm(config)
    tools = get_tools_for_agent("web")
    print(f"Loaded {len(tools)} tools for Web Agent.")
    
    graph = create_web_agent(llm, tools)
    
    task = "Test http://10.255.1.2:81/Less-1/ for SQL injection using kali_sqlmap_tool. Just get the banner."
    # We use a simple prompt that expects a tool call
    inputs = {"messages": [HumanMessage(content=task)]}
    
    print("🚀 Running Web Agent...")
    async for event in graph.astream(inputs):
        for key, value in event.items():
            if key == "agent":
                msg = value["messages"][-1]
                print(f"🤖 Web Agent: {msg.content}")
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"🔧 Tool Calls: {msg.tool_calls}")
            elif key == "tools":
                res = value["messages"][-1]
                print(f"📥 Tool Return: {str(res.content)[:200]}...")

if __name__ == "__main__":
    asyncio.run(main())
