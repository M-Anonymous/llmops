import os
from typing import Sequence

from fastapi import Depends
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.agent.middleware.system_middleware import SystemMiddleware
from app.agent.tool.api_tool.api_tool_entity_2_tool import get_api_tool_from_entity
from app.agent.tool.builtin_tool.library_search_tool import search_knowledge_base
from app.agent.tool.builtin_tool.memory_save_tool import get_user_info, save_user_info
from app.entity.agent.agent import AgentConfig as AgentEntity
from app.repository.agent.agent_repository import AgentRepository, get_agent_repository
from app.repository.middleware.middleware_repository import (
    MiddlewareRepository,
    get_middleware_repository,
)
from app.repository.model.model_repository import ModelRepository, get_model_repository
from app.repository.tool.api_tool_repository import APIToolRepository, get_api_tool_repository

_DEFAULT_SYSTEM_PROMPT = "你是一个乐于助人的助手，能帮助用户解决各种问题"


class AgentConfig:
    """运行时 Agent 配置加载器：通过构造注入 repository，由 FastAPI Depends 装配。"""

    def __init__(
        self,
        agent_repository: AgentRepository,
        model_repository: ModelRepository,
        api_tool_repository: APIToolRepository,
        middleware_repository: MiddlewareRepository,
    ):
        self.agent_repository = agent_repository
        self.model_repository = model_repository
        self.api_tool_repository = api_tool_repository
        self.middleware_repository = middleware_repository

    async def _get_agent(self, agent_id: str) -> AgentEntity:
        agent = await self.agent_repository.find_agent_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent 不存在: {agent_id}")
        return agent

    async def get_agent_model(self, agent_id: str) -> BaseChatModel:
        agent = await self._get_agent(agent_id)
        if agent.model_id:
            model_info = await self.model_repository.find_model(
                agent.model_id,
                agent.account_id,
            )
            if model_info:
                return ChatOpenAI(
                    model=model_info.name,
                    api_key=model_info.api_key,  # noqa
                    base_url=model_info.base_url,
                    temperature=0.7,
                )

        # 未配置模型时回退到环境变量
        return ChatOpenAI(
            model=os.getenv("QWEN_LLM_NAME", ""),
            api_key=os.getenv("QWEN_API_KEY", ""),
            base_url=os.getenv("QWEN_LLM_BASE_URL", ""),
            temperature=0.7,
        )

    async def get_agent_system_prompt(self, agent_id: str) -> str:
        agent = await self._get_agent(agent_id)
        prompt = (agent.system_prompt or "").strip()
        return prompt or _DEFAULT_SYSTEM_PROMPT

    async def get_agent_library_ids(self, agent_id: str) -> list[str]:
        agent = await self._get_agent(agent_id)
        return [item for item in (agent.library_ids or []) if item]

    async def get_agent_tools(self, agent_id: str) -> Sequence[BaseTool]:
        agent = await self._get_agent(agent_id)
        tools: list[BaseTool] = [save_user_info, get_user_info, search_knowledge_base]

        tool_ids = agent.tool_ids or []
        if not tool_ids:
            return tools

        entities = await self.api_tool_repository.list_enabled_tools_by_ids(tool_ids)
        entity_map = {entity.id: entity for entity in entities}
        for tool_id in tool_ids:
            entity = entity_map.get(tool_id)
            if entity is None:
                continue
            tools.append(get_api_tool_from_entity(entity))
        return tools

    async def get_agent_middlewares(
        self,
        agent_id: str,
        *,
        fallback_model: BaseChatModel | None = None,
    ) -> list[AgentMiddleware]:
        agent = await self._get_agent(agent_id)
        middleware_ids = [item for item in (agent.middleware_ids or []) if item]
        if not middleware_ids:
            return []

        entities = await self.middleware_repository.list_middlewares_by_ids(middleware_ids)
        entity_map = {entity.id: entity for entity in entities}
        # 保持 agent 配置中的顺序
        ordered = [entity_map[mid] for mid in middleware_ids if mid in entity_map]
        if not ordered:
            return []

        model_ids = {
            entity.config.get("model")
            for entity in ordered
            if entity.type == 0
            and isinstance(entity.config, dict)
            and isinstance(entity.config.get("model"), str)
            and entity.config.get("model")
        }
        model_map = {}
        for model_id in model_ids:
            model_info = await self.model_repository.find_model(model_id, agent.account_id)
            if model_info:
                model_map[model_id] = model_info

        return SystemMiddleware.build_many(
            ordered,
            model_map=model_map,
            fallback_model=fallback_model,
        )

    def get_agent_skills(self, agent_id: str):
        pass

    # 是否开启记忆，对话轮次
    def get_agent_external_config(self, agent_id: str):
        pass


async def get_agent_config(
    agent_repository: AgentRepository = Depends(get_agent_repository),
    model_repository: ModelRepository = Depends(get_model_repository),
    api_tool_repository: APIToolRepository = Depends(get_api_tool_repository),
    middleware_repository: MiddlewareRepository = Depends(get_middleware_repository),
) -> AgentConfig:
    return AgentConfig(
        agent_repository=agent_repository,
        model_repository=model_repository,
        api_tool_repository=api_tool_repository,
        middleware_repository=middleware_repository,
    )
