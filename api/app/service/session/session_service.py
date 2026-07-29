import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langgraph.types import Command

from app.agent.config.agent_config import AgentConfig, get_agent_config
from app.agent.pool.agent_session_pool import AgentSessionPool
from app.agent.tool.builtin_tool.memory_save_tool import Context
from app.entity.session.session import SessionInfo
from app.repository.session.session_repository import SessionRepository, get_session_repository
from app.request.session.session_request import SessionRequest, SessionResumeRequest
from app.service.oauth.current_user import OptionalCurrentUser

_DEFAULT_SESSION_TITLE = "新会话"


class SessionService:

    def __init__(
        self,
        account_id: int | None,
        session_repository: SessionRepository,
        agent_config: AgentConfig,
    ):
        self.account_id = account_id
        self.session_repository = session_repository
        self.agent_config = agent_config

    @staticmethod
    def _to_dict(entity: SessionInfo) -> dict:
        return {
            "id": entity.id,
            "accountId": entity.account_id,
            "visitorId": entity.visitor_id,
            "agentId": entity.agent_id,
            "title": entity.title,
            "createAt": entity.create_at,
            "updateAt": entity.update_at,
        }

    def _require_identity(self, visitor_id: str | None) -> None:
        if self.account_id is None and not visitor_id:
            raise HTTPException(
                status_code=401,
                detail="未登录时必须提供 visitor_id",
            )

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    if item.get("type") == "text":
                        parts.append(str(item.get("text", "")))
                    elif "text" in item:
                        parts.append(str(item["text"]))
            return "".join(parts)
        return str(content)

    @classmethod
    def _serialize_messages(cls, messages: list[Any] | None) -> list[dict]:
        role_map = {
            "human": "user",
            "ai": "assistant",
            "system": "system",
            "tool": "tool",
        }
        serialized: list[dict] = []
        for message in messages or []:
            msg_type = getattr(message, "type", None) or message.__class__.__name__.lower()
            item: dict[str, Any] = {
                "role": role_map.get(msg_type, msg_type),
                "content": cls._content_to_text(getattr(message, "content", "")),
            }
            name = getattr(message, "name", None)
            if name:
                item["name"] = name
            tool_calls = getattr(message, "tool_calls", None)
            if tool_calls:
                item["toolCalls"] = tool_calls
            serialized.append(item)
        return serialized

    @classmethod
    def _extract_answer(cls, messages: list[Any] | None) -> str:
        for message in reversed(messages or []):
            if getattr(message, "type", None) != "ai":
                continue
            text = cls._content_to_text(getattr(message, "content", ""))
            if text.strip():
                return text
        return ""

    @staticmethod
    def _serialize_interrupt_payload(value: Any) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            return None

        action_requests = value.get("action_requests") or []
        review_configs = value.get("review_configs") or []
        actions: list[dict[str, Any]] = []
        for raw in action_requests:
            if not isinstance(raw, dict):
                continue
            actions.append(
                {
                    "name": raw.get("name"),
                    "args": raw.get("args") or raw.get("arguments") or {},
                    "description": raw.get("description") or "",
                }
            )
        configs: list[dict[str, Any]] = []
        for raw in review_configs:
            if not isinstance(raw, dict):
                continue
            allowed = raw.get("allowed_decisions") or ["approve", "reject"]
            allowed = [item for item in allowed if item in ("approve", "reject")]
            if not allowed:
                allowed = ["approve", "reject"]
            configs.append(
                {
                    "actionName": raw.get("action_name"),
                    "allowedDecisions": allowed,
                }
            )
        if not actions:
            return None
        return {
            "actionRequests": actions,
            "reviewConfigs": configs,
        }

    @classmethod
    def _serialize_interrupts(cls, interrupts: Any) -> dict[str, Any] | None:
        if not interrupts:
            return None
        for item in interrupts:
            value = getattr(item, "value", item)
            payload = cls._serialize_interrupt_payload(value)
            if payload:
                return payload
        return None

    async def _get_pending_interrupt(self, agent: Any, session_id: str) -> dict[str, Any] | None:
        state = await agent.aget_state(self._invoke_config(session_id))
        if not state:
            return None
        return self._serialize_interrupts(getattr(state, "interrupts", None))

    async def get_session(self, session_id: str) -> SessionInfo:
        entity = await self.session_repository.find_session(session_id)
        if not entity:
            raise HTTPException(status_code=404, detail="会话不存在")
        return entity

    @staticmethod
    def _resolve_title(request: SessionRequest) -> str:
        if request.title and request.title.strip():
            return request.title.strip()
        if request.question and request.question.strip():
            text = request.question.strip().replace("\n", " ")
            return text[:40] + ("…" if len(text) > 40 else "")
        return _DEFAULT_SESSION_TITLE

    async def create_session(self, request: SessionRequest) -> str:
        self._require_identity(request.visitor_id)
        entity = SessionInfo(
            account_id=self.account_id,
            visitor_id=request.visitor_id,
            agent_id=request.agent_id,
            title=self._resolve_title(request),
        )
        created = await self.session_repository.add_session(entity)
        return created.id

    def _assert_session_owner(self, entity: SessionInfo, visitor_id: str | None) -> None:
        if self.account_id is not None:
            if entity.account_id != self.account_id:
                raise HTTPException(status_code=403, detail="无权访问该会话")
            return
        if not visitor_id or entity.visitor_id != visitor_id:
            raise HTTPException(status_code=403, detail="无权访问该会话")

    async def get_session_messages(
        self,
        session_id: str,
        visitor_id: str | None = None,
    ) -> dict:
        self._require_identity(visitor_id)
        entity = await self.get_session(session_id)
        self._assert_session_owner(entity, visitor_id)

        agent = await self._get_agent(session_id, entity.agent_id)
        state = await agent.aget_state(self._invoke_config(session_id))
        values = state.values if state else None
        messages = values.get("messages") if isinstance(values, dict) else None
        interrupt = self._serialize_interrupts(
            getattr(state, "interrupts", None) if state else None
        )
        return {
            "session": self._to_dict(entity),
            "messages": self._serialize_messages(messages),
            "interrupt": interrupt,
        }

    async def update_session(self, request: SessionRequest) -> dict:
        if not request.session_id:
            raise HTTPException(status_code=400, detail="更新会话时 session_id 必填")
        entity = await self.get_session(request.session_id)
        data = request.model_dump(
            exclude_unset=True,
            exclude={"session_id", "visitor_id", "question"},
        )
        if not data:
            raise HTTPException(status_code=400, detail="未提供需要更新的字段")
        for key, value in data.items():
            setattr(entity, key, value)
        updated = await self.session_repository.update_session(entity)
        return self._to_dict(updated)

    async def delete_session(self, request: SessionRequest) -> None:
        if not request.session_id:
            raise HTTPException(status_code=400, detail="删除会话时 session_id 必填")
        self._require_identity(request.visitor_id)
        entity = await self.get_session(request.session_id)
        self._assert_session_owner(entity, request.visitor_id)
        await self.session_repository.delete_session(entity)
        AgentSessionPool.remove_session(entity.id)

    async def get_session_list(
        self,
        agent_id: str | None = None,
        visitor_id: str | None = None,
    ) -> list[dict]:
        self._require_identity(visitor_id)

        if self.account_id is not None:
            sessions = await self.session_repository.list_sessions_by_account(
                self.account_id,
                agent_id=agent_id,
            )
        else:
            assert visitor_id is not None
            sessions = await self.session_repository.list_sessions_by_visitor(
                visitor_id,
                agent_id=agent_id,
            )
        return [self._to_dict(session) for session in sessions]

    async def _resolve_chat_context(self, request: SessionRequest) -> tuple[str, str]:
        """解析 session_id / agent_id；未传 session_id 时自动创建会话。"""
        session_id = (request.session_id or "").strip() or None

        if session_id:
            session = await self.get_session(session_id)
            agent_id = request.agent_id or session.agent_id
            if not agent_id:
                raise HTTPException(status_code=400, detail="会话未关联 Agent，请传入 agent_id")
            return session.id, agent_id

        # 未传 session_id：创建新会话
        self._require_identity(request.visitor_id)
        if not request.agent_id:
            raise HTTPException(status_code=400, detail="新建会话时 agent_id 必填")

        created_id = await self.create_session(request)
        return created_id, request.agent_id

    async def _touch_session(self, session_id: str) -> None:
        session = await self.get_session(session_id)
        session.update_at = datetime.now(timezone.utc)
        await self.session_repository.update_session(session)

    async def _get_agent(self, session_id: str, agent_id: str):
        try:
            return await AgentSessionPool.get_or_create_agent(
                session_id,
                agent_id,
                self.agent_config,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @staticmethod
    def _invoke_config(session_id: str) -> dict:
        return {
            "configurable": {"thread_id": session_id},
        }

    async def _invoke_context(
        self,
        visitor_id: str | None = None,
        agent_id: str | None = None,
    ) -> Context:
        library_ids: list[str] = []
        if agent_id:
            try:
                library_ids = await self.agent_config.get_agent_library_ids(agent_id)
            except ValueError:
                library_ids = []
        return Context(
            account_id=self.account_id,
            visitor_id=visitor_id,
            library_ids=library_ids,
        )

    @staticmethod
    def _sse(payload: dict) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    async def _astream_messages(
        self,
        agent: Any,
        input_payload: Any,
        session_id: str,
        agent_id: str,
        context: Context,
    ) -> AsyncIterator[str]:
        async for item in agent.astream(
            input_payload,
            config=self._invoke_config(session_id),
            context=context,
            stream_mode="messages",
        ):
            message: BaseMessage | None = None
            if isinstance(item, tuple) and item:
                message = item[0]
            elif isinstance(item, BaseMessage):
                message = item

            if not isinstance(message, (AIMessage, AIMessageChunk)):
                continue

            text = self._content_to_text(getattr(message, "content", ""))
            if not text:
                continue

            yield self._sse({
                "type": "delta",
                "content": text,
            })

        interrupt = await self._get_pending_interrupt(agent, session_id)
        await self._touch_session(session_id)
        if interrupt:
            yield self._sse({
                "type": "interrupt",
                "sessionId": session_id,
                "agentId": agent_id,
                **interrupt,
            })
            return

        yield self._sse({"type": "done", "sessionId": session_id, "agentId": agent_id})

    async def chat(self, request: SessionRequest) -> dict:
        if not request.question:
            raise HTTPException(status_code=400, detail="聊天时 question 必填")

        session_id, agent_id = await self._resolve_chat_context(request)
        agent = await self._get_agent(session_id, agent_id)

        try:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": request.question}]},
                config=self._invoke_config(session_id),
                context=await self._invoke_context(request.visitor_id, agent_id),
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"对话失败: {exc}") from exc

        messages = result.get("messages") if isinstance(result, dict) else None
        interrupt = await self._get_pending_interrupt(agent, session_id)
        await self._touch_session(session_id)

        return {
            "sessionId": session_id,
            "agentId": agent_id,
            "answer": self._extract_answer(messages),
            "messages": self._serialize_messages(messages),
            "interrupt": interrupt,
        }

    async def prepare_stream(self, request: SessionRequest) -> tuple[str, str]:
        """流式开始前解析/创建会话（无 session_id 会自动创建）。"""
        if not request.question:
            raise HTTPException(status_code=400, detail="聊天时 question 必填")
        return await self._resolve_chat_context(request)

    async def stream(
        self,
        request: SessionRequest,
        session_id: str,
        agent_id: str,
    ) -> AsyncIterator[str]:
        agent = await self._get_agent(session_id, agent_id)
        context = await self._invoke_context(request.visitor_id, agent_id)

        yield self._sse({
            "type": "session",
            "sessionId": session_id,
            "agentId": agent_id,
        })

        try:
            async for chunk in self._astream_messages(
                agent,
                {"messages": [{"role": "user", "content": request.question}]},
                session_id,
                agent_id,
                context,
            ):
                yield chunk
        except Exception as exc:
            yield self._sse({"type": "error", "detail": str(exc)})

    async def prepare_resume(self, request: SessionResumeRequest) -> tuple[str, str]:
        self._require_identity(request.visitor_id)
        session = await self.get_session(request.session_id)
        self._assert_session_owner(session, request.visitor_id)
        agent_id = request.agent_id or session.agent_id
        if not agent_id:
            raise HTTPException(status_code=400, detail="会话未关联 Agent，请传入 agent_id")
        return session.id, agent_id

    async def resume_stream(
        self,
        request: SessionResumeRequest,
        session_id: str,
        agent_id: str,
    ) -> AsyncIterator[str]:
        agent = await self._get_agent(session_id, agent_id)
        pending = await self._get_pending_interrupt(agent, session_id)
        if not pending:
            yield self._sse({"type": "error", "detail": "当前会话没有待审批的工具调用"})
            return

        expected = len(pending.get("actionRequests") or [])
        if len(request.decisions) != expected:
            yield self._sse({
                "type": "error",
                "detail": (
                    f"决策数量 ({len(request.decisions)}) "
                    f"与待审批工具数 ({expected}) 不一致"
                ),
            })
            return

        decisions: list[dict[str, Any]] = []
        for item in request.decisions:
            decision: dict[str, Any] = {"type": item.type}
            if item.type == "reject" and item.message:
                decision["message"] = item.message.strip()
            decisions.append(decision)

        context = await self._invoke_context(request.visitor_id, agent_id)

        yield self._sse({
            "type": "session",
            "sessionId": session_id,
            "agentId": agent_id,
        })

        try:
            async for chunk in self._astream_messages(
                agent,
                Command(resume={"decisions": decisions}),
                session_id,
                agent_id,
                context,
            ):
                yield chunk
        except Exception as exc:
            yield self._sse({"type": "error", "detail": str(exc)})


async def get_session_service(
    account_id: int | None = Depends(OptionalCurrentUser()),
    session_repository: SessionRepository = Depends(get_session_repository),
    agent_config: AgentConfig = Depends(get_agent_config),
) -> SessionService:
    return SessionService(account_id, session_repository, agent_config)
