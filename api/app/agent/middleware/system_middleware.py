from typing import Any, Sequence

from langchain.agents.middleware import HumanInTheLoopMiddleware, SummarizationMiddleware
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.entity.middleware.middleware import MiddlewareInfo
from app.entity.model.model import ModelInfo

# 0: SummarizationMiddleware  1: HumanInTheLoopMiddleware
TYPE_SUMMARIZATION = 0
TYPE_HUMAN_IN_THE_LOOP = 1


def _as_context_size(value: Any) -> Any:
    """JSON 中的 ["tokens", 4000] 转为 ("tokens", 4000)。"""
    if isinstance(value, (list, tuple)) and len(value) == 2 and isinstance(value[0], str):
        return (value[0], value[1])
    return value


def _normalize_trigger(trigger: Any) -> Any:
    if trigger is None:
        return None
    # 单一条件: ["tokens", 4000]
    if isinstance(trigger, (list, tuple)) and len(trigger) == 2 and isinstance(trigger[0], str):
        return _as_context_size(trigger)
    # 多条件 / 条件组
    if isinstance(trigger, list):
        return [
            item if isinstance(item, dict) else _as_context_size(item)
            for item in trigger
        ]
    return trigger


def _normalize_interrupt_on(interrupt_on: dict[str, Any]) -> dict[str, Any]:
    """仅保留 bool 或 allowed_decisions；when 需 callable，暂不支持。"""
    result: dict[str, Any] = {}
    for tool_name, value in interrupt_on.items():
        if not tool_name:
            continue
        if isinstance(value, bool):
            if value:
                result[tool_name] = {"allowed_decisions": ["approve", "reject"]}
            # False: 不加入中断配置（由 HITL 视为自动放行）
            continue
        if isinstance(value, dict):
            decisions = value.get("allowed_decisions")
            if isinstance(decisions, list) and decisions:
                result[tool_name] = {"allowed_decisions": decisions}
            else:
                result[tool_name] = True
    return result


def _build_chat_model(model_info: ModelInfo) -> BaseChatModel:
    return ChatOpenAI(
        model=model_info.name,
        api_key=model_info.api_key,  # noqa
        base_url=model_info.base_url,
        temperature=0.7,
    )


class SystemMiddleware:
    """将 middleware_info 配置转换为 langchain AgentMiddleware 实例。"""

    @classmethod
    def build_from_entity(
        cls,
        entity: MiddlewareInfo,
        *,
        model_info: ModelInfo | None = None,
        fallback_model: BaseChatModel | None = None,
    ) -> AgentMiddleware | None:
        config = entity.config or {}
        if entity.type == TYPE_SUMMARIZATION:
            return cls._build_summarization(config, model_info, fallback_model)
        if entity.type == TYPE_HUMAN_IN_THE_LOOP:
            return cls._build_human_in_the_loop(config)
        return None

    @classmethod
    def _build_summarization(
        cls,
        config: dict[str, Any],
        model_info: ModelInfo | None,
        fallback_model: BaseChatModel | None,
    ) -> SummarizationMiddleware | None:
        if model_info is not None:
            model: BaseChatModel = _build_chat_model(model_info)
        elif fallback_model is not None:
            model = fallback_model
        else:
            return None

        kwargs: dict[str, Any] = {"model": model}
        if "trigger" in config:
            kwargs["trigger"] = _normalize_trigger(config.get("trigger"))
        if "keep" in config:
            kwargs["keep"] = _as_context_size(config.get("keep"))
        return SummarizationMiddleware(**kwargs)

    @classmethod
    def _build_human_in_the_loop(
        cls,
        config: dict[str, Any],
    ) -> HumanInTheLoopMiddleware | None:
        raw_interrupt_on = config.get("interrupt_on")
        if not isinstance(raw_interrupt_on, dict) or not raw_interrupt_on:
            return None
        interrupt_on = _normalize_interrupt_on(raw_interrupt_on)
        if not interrupt_on:
            return None

        description_prefix = config.get("description_prefix")
        if not isinstance(description_prefix, str) or not description_prefix.strip():
            description_prefix = "Tool execution requires approval"

        return HumanInTheLoopMiddleware(
            interrupt_on=interrupt_on,
            description_prefix=description_prefix.strip(),
        )

    @classmethod
    def build_many(
        cls,
        entities: Sequence[MiddlewareInfo],
        *,
        model_map: dict[str, ModelInfo],
        fallback_model: BaseChatModel | None = None,
    ) -> list[AgentMiddleware]:
        middlewares: list[AgentMiddleware] = []
        for entity in entities:
            model_id = None
            if entity.type == TYPE_SUMMARIZATION and isinstance(
                (entity.config or {}).get("model"), str
            ):
                model_id = entity.config["model"]
            built = cls.build_from_entity(
                entity,
                model_info=model_map.get(model_id) if model_id else None,
                fallback_model=fallback_model,
            )
            if built is not None:
                middlewares.append(built)
        return middlewares
