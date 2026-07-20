from typing import Any

from app.agent.config.agent_config import AgentConfig
from langchain.agents import create_agent

from app.component.database.postgres_client import PostgresClient



class AgentSessionPool:

    agent_session_pool: dict[str,Any] = {}

    @classmethod
    def get_or_create_agent(cls,session_id: str,agent_id: str):
        cache_key = session_id + ":" + agent_id
        if cache_key in cls.agent_session_pool:
            return cls.agent_session_pool[cache_key]

        model = AgentConfig.get_agent_model(agent_id)
        system_prompt = AgentConfig.get_agent_system_prompt(agent_id)
        tools = AgentConfig.get_agent_tools(agent_id)
        #skills = AgentConfig.get_agent_skills(agent_id)
        agent = create_agent(
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            checkpointer=PostgresClient.checkpointer,
            store=PostgresClient.store
        )
        cls.agent_session_pool[cache_key] = agent
        return agent

    #定时清理长时间未活跃会话
    @classmethod
    def cleanup(cls):
        #对会话池进行清理
        pass
