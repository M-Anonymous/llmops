from fastapi import Depends, HTTPException

from app.entity.mcp.mcp_server import McpServerInfo
from app.repository.mcp.mcp_server_repository import (
    McpServerRepository,
    get_mcp_server_repository,
)
from app.request.mcp.mcp_server import (
    McpServerCreateRequest,
    McpServerDeleteRequest,
    McpServerTestRequest,
    McpServerUpdateRequest,
)
from app.service.oauth.current_user import CurrentUser

# 当前仅支持 streamable_http
_SUPPORTED_TRANSPORT = 2
_TRANSPORT_KEYS = {
    2: ("url",),
}


class McpServerService:

    def __init__(self, account_id: int, mcp_server_repository: McpServerRepository):
        self.account_id = account_id
        self.mcp_server_repository = mcp_server_repository

    @staticmethod
    def _to_dict(entity: McpServerInfo) -> dict:
        return {
            "id": entity.id,
            "accountId": entity.account_id,
            "name": entity.name,
            "label": entity.label,
            "desc": entity.desc,
            "transport": entity.transport,
            "config": entity.config,
            "enabled": entity.enabled,
            "createAt": entity.create_at,
            "updateAt": entity.update_at,
        }

    @staticmethod
    def _validate_config(transport: int, config: dict) -> None:
        if transport != _SUPPORTED_TRANSPORT:
            raise HTTPException(
                status_code=400,
                detail="当前仅支持 streamable_http（transport=2）",
            )
        required = _TRANSPORT_KEYS[_SUPPORTED_TRANSPORT]
        for key in required:
            value = config.get(key)
            if not isinstance(value, str) or not value.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"streamable_http 时 config.{key} 必填",
                )

    async def get_server(self, server_id: str) -> McpServerInfo:
        entity = await self.mcp_server_repository.find_server(server_id, self.account_id)
        if not entity:
            raise HTTPException(status_code=404, detail="MCP Server 不存在")
        return entity

    async def create_server(self, request: McpServerCreateRequest) -> str:
        self._validate_config(request.transport, request.config)
        exists = await self.mcp_server_repository.find_by_name(
            request.name.strip(), self.account_id
        )
        if exists:
            raise HTTPException(status_code=400, detail="该名称已存在")

        entity = McpServerInfo(
            account_id=self.account_id,
            name=request.name.strip(),
            label=request.label.strip(),
            desc=request.desc or "",
            transport=request.transport,
            config=request.config,
            enabled=request.enabled,
        )
        created = await self.mcp_server_repository.add_server(entity)
        return created.id

    async def update_server(self, request: McpServerUpdateRequest) -> dict:
        entity = await self.get_server(request.id)
        data = request.model_dump(exclude_unset=True, exclude={"id"})
        if not data:
            raise HTTPException(status_code=400, detail="未提供需要更新的字段")

        if "name" in data and data["name"] is not None:
            data["name"] = data["name"].strip()
            if data["name"] != entity.name:
                exists = await self.mcp_server_repository.find_by_name(
                    data["name"], self.account_id
                )
                if exists:
                    raise HTTPException(status_code=400, detail="该名称已存在")

        if "label" in data and data["label"] is not None:
            data["label"] = data["label"].strip()

        transport = data.get("transport", entity.transport)
        config = data.get("config", entity.config)
        if not isinstance(config, dict):
            raise HTTPException(status_code=400, detail="config 必须为对象")
        self._validate_config(transport, config)

        for key, value in data.items():
            setattr(entity, key, value)
        updated = await self.mcp_server_repository.update_server(entity)
        return self._to_dict(updated)

    async def delete_server(self, request: McpServerDeleteRequest) -> None:
        entity = await self.get_server(request.id)
        await self.mcp_server_repository.delete_server(entity)

    async def get_server_list(self) -> list[dict]:
        servers = await self.mcp_server_repository.list_servers(self.account_id)
        return [self._to_dict(item) for item in servers]

    async def list_server_tools(self, server_id: str) -> list[dict]:
        entity = await self.get_server(server_id)
        if not entity.enabled:
            raise HTTPException(status_code=400, detail="MCP Server 未启用")
        try:
            from app.agent.tool.mcp.mcp_tool_loader import list_mcp_server_tools

            return await list_mcp_server_tools(entity)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502,
                detail=f"连接 MCP Server 失败: {exc}",
            ) from exc

    async def test_connection(self, request: McpServerTestRequest) -> dict:
        name = request.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="内部名称不能为空")
        if not isinstance(request.config, dict):
            raise HTTPException(status_code=400, detail="config 必须为对象")
        self._validate_config(request.transport, request.config)
        try:
            from app.agent.tool.mcp.mcp_tool_loader import test_mcp_connection

            return await test_mcp_connection(name, request.transport, request.config)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502,
                detail=f"连接 MCP Server 失败: {exc}",
            ) from exc

    async def list_tools_from_config(self, request: McpServerTestRequest) -> list[dict]:
        name = request.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="内部名称不能为空")
        if not isinstance(request.config, dict):
            raise HTTPException(status_code=400, detail="config 必须为对象")
        self._validate_config(request.transport, request.config)
        try:
            from app.agent.tool.mcp.mcp_tool_loader import list_mcp_tools_by_config

            return await list_mcp_tools_by_config(name, request.transport, request.config)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502,
                detail=f"连接 MCP Server 失败: {exc}",
            ) from exc


async def get_mcp_server_service(
    account_id: int = Depends(CurrentUser()),
    mcp_server_repository: McpServerRepository = Depends(get_mcp_server_repository),
) -> McpServerService:
    return McpServerService(account_id, mcp_server_repository)
