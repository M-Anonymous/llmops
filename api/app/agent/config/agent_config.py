import os
from typing import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from app.agent.tool.builtin_tool.memory_tool import save_user_info,get_user_info


class AgentConfig:

    @classmethod
    def get_agent_model(cls,agent_id: str) -> BaseChatModel:
        os.environ["OPENAI_API_KEY"] = os.getenv("QWEN_API_KEY","")
        llm = ChatOpenAI(
            model=os.getenv("QWEN_LLM_NAME",""),
            base_url=os.getenv("QWEN_LLM_BASE_URL",""),
            temperature=0.7,
        )
        return llm


    @classmethod
    def get_agent_system_prompt(cls,agent_id: str) -> str:
        return "你是一个乐于助人的助手，能帮助用户解决各种问题"

    @classmethod
    def get_agent_tools(cls,agent_id: str) -> Sequence[BaseTool]:
        @tool
        def get_weather(city: str):
            """
            获取指定城市的天气信息。

            Args:
                city: 城市名称，如 "北京"、"上海"
            Returns:
                该城市的天气描述
            """
            return f"{city}天气很好，阳光明媚。"
        return [get_weather,save_user_info,get_user_info] # type: ignore

    @classmethod
    def get_agent_middlewares(cls,agent_id: str):
        pass

    @classmethod
    def get_agent_skills(cls,agent_id: str):
        pass

    #是否开启记忆，对话轮次
    @classmethod
    def get_agent_external_config(cls,agent_id: str):
        pass
