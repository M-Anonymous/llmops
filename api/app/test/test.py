from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings
from langgraph.store.base import IndexConfig # noqa
from langgraph.store.postgres import PostgresStore
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


# Augment the LLM with tools
tools = [add, multiply, divide]








chatLLM = ChatOpenAI(
    api_key="sk-ws-H.EDXDLII.rsk5.MEUCIQCC_fHHxV7YfUcIigvJlagvB5QYBF2NDGdiovzLvwQ6pQIgfHJkh0BNX8x40PR2e8e-AdvS7xDdVkU11-xbDdE3U5M",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",  # 此处以qwen-plus为例，您可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    # other params...
)
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "你是谁？"}]
response = chatLLM.invoke(messages)
print(response.model_dump_json())

embeddings = DashScopeEmbeddings(
    model="text-embedding-v4",
    dashscope_api_key="sk-ws-H.EDXDLII.rsk5.MEUCIQCC_fHHxV7YfUcIigvJlagvB5QYBF2NDGdiovzLvwQ6pQIgfHJkh0BNX8x40PR2e8e-AdvS7xDdVkU11-xbDdE3U5M"
)

DB_URI = "postgresql://postgres:postgres@localhost:5432/llmops?sslmode=disable"
store = PostgresStore.from_conn_string(
    DB_URI,
    index=IndexConfig(embed=embeddings, dims=1024))

agent = create_agent(chatLLM,store=store)
