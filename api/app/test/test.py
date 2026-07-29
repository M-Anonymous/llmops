
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.base import IndexConfig # noqa
from langchain.tools import tool

@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

# Augment the LLM with tools
tools = [add, multiply, divide, get_weather]


chatLLM = ChatOpenAI(
    api_key="sk-ws-H.EDXDLII.rsk5.MEUCIQCC_fHHxV7YfUcIigvJlagvB5QYBF2NDGdiovzLvwQ6pQIgfHJkh0BNX8x40PR2e8e-AdvS7xDdVkU11-xbDdE3U5M",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="deepseek-v4-flash",  # 此处以qwen-plus为例，您可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    # other params...
)
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "你是谁？"}]
response = chatLLM.invoke(messages)
print(response.model_dump_json())

agent = create_agent(model=chatLLM,checkpointer=InMemorySaver(),tools=tools)
config = {"configurable": {"thread_id": "123456"}}
stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    config=config,
    version="v3",
)
for kind, item in stream.interleave("messages", "tool_calls"):
    if kind == "messages":
        for token in item.text:
            print(token, end="", flush=True)
    elif kind == "tool_calls":
        print(f"\nTool call: {item.tool_name}({item.input})")
        for delta in item.output_deltas:
            print(delta, end="", flush=True)
        print(f"\nTool result: {item.output}")


HumanInTheLoopMiddleware()
