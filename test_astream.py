
import asyncio
from langgraph.graph import StateGraph, MessagesState, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def node_a(state):
    return {"messages": ["hello"]}

workflow = StateGraph(AgentState)
workflow.add_node("node_a", node_a)
workflow.add_edge(START, "node_a")
workflow.add_edge("node_a", END)
app = workflow.compile()

async def main():
    inputs = {"messages": [("user", "hi")]}
    print("--- stream_mode='updates' ---")
    async for event in app.astream(inputs, stream_mode="updates"):
        print(f"Event: {event}")

    print("\n--- stream_mode='values' ---")
    async for event in app.astream(inputs, stream_mode="values"):
        print(f"Event: {event}")

if __name__ == "__main__":
    asyncio.run(main())
