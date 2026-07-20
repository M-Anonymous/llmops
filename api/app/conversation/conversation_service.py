from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.request.conversation.conversation import Question
from langchain.tools import tool

@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


def invoke(question: Question):
    chatLLM = ChatOpenAI(
        api_key="sk-ws-H.EDXDLII.rsk5.MEUCIQCC_fHHxV7YfUcIigvJlagvB5QYBF2NDGdiovzLvwQ6pQIgfHJkh0BNX8x40PR2e8e-AdvS7xDdVkU11-xbDdE3U5M",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        # 此处以qwen-plus为例，您可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        # other params...
    )
    agent = create_agent(chatLLM, tools=[multiply],system_prompt="你是一个智能助手，可以回答用户的各种问题，当不知道时，就说不知道")
    result = agent.invoke({"messages":[{"role":"user","content":"12 * 6 等于多少"}]})
    print(result["messages"][-1].content_blocks)

async def stream():
    pass


invoke()