from dataclasses import dataclass
from typing import TypedDict

from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime
from pydantic import BaseModel, Field

"""
title
checkpointer 和 store 使用区别

checkpointer（短期记忆）：是 自动 保存的。create_agent 在每一次对话交互（invoke）结束时，都会自动将整个对话状态（消息历史、当前步骤等）保存到 Postgres 中。你什么都不用做，它就在默默工作。

store（长期记忆）：是 手动 保存的。它不会自动保存任何东西，而是需要 Agent 主动调用一个工具来触发写入。如果你没有给 Agent 提供一个能操作 store 的工具，那即使传入了 store，它也不会存储任何信息。

这意味着，store 就像一个智能的“知识库”，需要 Agent 自己决定“这个信息很重要，我需要记住它”，然后调用工具去执行写入。它不关心对话的细节，只负责持久化重要的知识点。与 checkpointer 不同的时，store 侧重于记录用户的偏好，累计的知识，以及用户强调需要记录的内容，这些内容时可以跨会话保存的，和用户是强相关的。

"""

@dataclass
class Context:
    account_id: int

class UserInfo(BaseModel):
    name: str = Field(..., max_length=255, description="用户姓名")
    prefect: str = Field(..., max_length=255, description="用户爱好")

@tool
def save_user_info(user_info: UserInfo,runtime: ToolRuntime[Context]):
    """保存用户信息"""
    # Access the store - same as that provided to `create_agent`
    assert runtime.store is not None
    store = runtime.store
    account_id = runtime.context.account_id
    # Store data in the store (namespace, key, data)
    store.put(("users",), str(account_id), dict(user_info))
    return "Successfully saved user info."


@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """
    获取当前用户的个人信息和偏好设置。

    使用场景：
    - 当用户询问关于自己的任何事情时使用（如名字、年龄、兴趣爱好等）
    - 当需要个性化推荐时需要先查询用户偏好
    - 当用户提到"我"、"我的"等第一人称时主动查询

    返回数据格式示例：
    {
        "name": "张三",
        "prefect": "打篮球",
    }

    如果用户不存在，返回 "Unknown user"。
    """
    # Access the store - same as that provided to `create_agent`
    assert runtime.store is not None
    account_id = runtime.context.account_id
    # Retrieve data from store - returns StoreValue object with value and metadata
    user_info = runtime.store.get(("users",), str(account_id))
    return str(user_info.value) if user_info else "Unknown user"

