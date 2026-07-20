from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool


class AgentConfig:

    @classmethod
    def get_agent_model(cls,agent_id: str) -> BaseChatModel:
        pass

    @classmethod
    def get_agent_system_prompt(cls,agent_id: str) -> str:
        pass

    @classmethod
    def get_agent_tools(cls,agent_id: str) -> BaseTool:
        pass

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
