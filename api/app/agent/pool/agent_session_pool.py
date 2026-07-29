from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.agent.config.agent_config import AgentConfig
from app.component.database.postgres_client import PostgresClient


class AgentSessionPool:

    agent_session_pool: dict[str, Any] = {}

    @classmethod
    async def get_or_create_agent(
        cls,
        session_id: str,
        agent_id: str,
        agent_config: AgentConfig,
    ):
        cache_key = session_id + ":" + agent_id
        if cache_key in cls.agent_session_pool:
            return cls.agent_session_pool[cache_key]

        model = await agent_config.get_agent_model(agent_id)
        system_prompt = await agent_config.get_agent_system_prompt(agent_id)
        tools = await agent_config.get_agent_tools(agent_id)
        middlewares = await agent_config.get_agent_middlewares(
            agent_id,
            fallback_model=model,
        )
        agent = create_agent(
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            middleware=middlewares,
            checkpointer=PostgresClient.checkpointer,
            store=PostgresClient.store,
        )
        cls.agent_session_pool[cache_key] = agent
        return agent

    @classmethod
    def _create_custom_agent(
        cls,
        model: BaseChatModel,
        system_prompt: str,
        tools: list[BaseTool],
        middlewares: list[AgentMiddleware] | None = None,
    ):
        agent = create_agent(
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            middleware=middlewares or [],
            checkpointer=PostgresClient.checkpointer,
            store=PostgresClient.store,
        )
        return agent

    @classmethod
    def _create_system_agent(
        cls,
        model: BaseChatModel,
        system_prompt: str,
        tools: list[BaseTool],
        middlewares: list[AgentMiddleware] | None = None,
    ):
        # 系统 agent 可叠加额外中间件
        agent = create_agent(
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            middleware=middlewares or [],
            checkpointer=PostgresClient.checkpointer,
            store=PostgresClient.store,
        )
        return agent

    @classmethod
    def remove_session(cls, session_id: str) -> None:
        prefix = session_id + ":"
        for key in [k for k in cls.agent_session_pool if k.startswith(prefix)]:
            cls.agent_session_pool.pop(key, None)

    # 定时清理长时间未活跃会话
    @classmethod
    def cleanup(cls):
        pass
