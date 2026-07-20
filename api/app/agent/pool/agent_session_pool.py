from uuid import UUID
from app.agent.config.agent_config import AgentConfig
from langchain.agents import create_agent


class AgentSessionPool:

    agent_session_pool: dict


    @classmethod
    def get_or_create_agent(cls,session_id: str,agent_id: str):
        cache_key = session_id + ":" + agent_id
        if cache_key in cls.agent_session_pool:
            return cls.agent_session_pool[cache_key]

        model = AgentConfig.get_agent_model(agent_id)
        system_prompt = AgentConfig.get_agent_system_prompt(agent_id)
        tools = AgentConfig.get_agent_tools(agent_id)
        skills = AgentConfig.get_agent_skills(agent_id)
        return create_agent(
            model,
            system_prompt,
            tools,
        )

    #定时清理长时间未活跃会话
    @classmethod
    def cleanup(cls):
        pass
