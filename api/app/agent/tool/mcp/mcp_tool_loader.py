"""将 McpServerInfo 转为 langchain-mcp-adapters 连接配置并加载工具。"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import BaseTool

from app.entity.mcp.mcp_server import McpServerInfo

logger = logging.getLogger(__name__)

_TRANSPORT_NAME = {
    0: "stdio",
    1: "sse",
    2: "streamable_http",
}


def build_mcp_connection(entity: McpServerInfo) -> dict[str, Any]:
    """根据实体生成 MultiServerMCPClient 所需的 connection dict。"""
    transport = _TRANSPORT_NAME.get(entity.transport)
    if not transport:
        raise ValueError(f"不支持的 MCP transport: {entity.transport}")

    config = dict(entity.config or {})
    connection: dict[str, Any] = {"transport": transport}

    if transport == "stdio":
        command = config.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ValueError(f"MCP Server `{entity.name}` 缺少 command")
        connection["command"] = command.strip()
        args = config.get("args", [])
        connection["args"] = list(args) if isinstance(args, list) else []
        if isinstance(config.get("env"), dict):
            connection["env"] = {str(k): str(v) for k, v in config["env"].items()}
        if config.get("cwd"):
            connection["cwd"] = str(config["cwd"])
        return connection

    url = config.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError(f"MCP Server `{entity.name}` 缺少 url")
    connection["url"] = url.strip()
    if isinstance(config.get("headers"), dict):
        connection["headers"] = config["headers"]
    if config.get("timeout") is not None:
        connection["timeout"] = config["timeout"]
    if config.get("sse_read_timeout") is not None:
        connection["sse_read_timeout"] = config["sse_read_timeout"]
    if transport == "streamable_http" and config.get("terminate_on_close") is not None:
        connection["terminate_on_close"] = bool(config["terminate_on_close"])
    return connection


def _strip_tool_prefix(tool_name: str, server_name: str) -> str:
    prefix = f"{server_name}_"
    if tool_name.startswith(prefix):
        return tool_name[len(prefix) :]
    return tool_name


def _tool_matches_selection(tool_name: str, server_name: str, selected: list[str]) -> bool:
    if not selected:
        return False
    bare = _strip_tool_prefix(tool_name, server_name)
    allowed = set(selected)
    return tool_name in allowed or bare in allowed


def _filter_tools_for_server(
    tools: list[BaseTool],
    server: McpServerInfo,
    selected_names: list[str] | None,
) -> list[BaseTool]:
    """按 mcp_tool_cache 过滤单个 server 的工具。"""
    if selected_names is None:
        return tools
    if not selected_names:
        return []
    return [
        tool
        for tool in tools
        if _tool_matches_selection(tool.name, server.name, selected_names)
    ]


async def _load_tools_with_client(
    connections: dict[str, dict[str, Any]],
    *,
    server_name: str | None = None,
) -> list[BaseTool]:
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError as exc:
        logger.error("无法导入 langchain_mcp_adapters: %s", exc)
        return []

    try:
        client = MultiServerMCPClient(connections, tool_name_prefix=True)
        if server_name:
            return list(await client.get_tools(server_name=server_name))
        return list(await client.get_tools())
    except Exception as exc:  # noqa: BLE001
        logger.exception("加载 MCP tools 失败: %s", exc)
        return []


async def list_mcp_server_tools(server: McpServerInfo) -> list[dict[str, str | None]]:
    """列出单个 MCP Server 的可用 tools（供配置页勾选）。"""
    try:
        connection = build_mcp_connection(server)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(str(exc)) from exc

    tools = await _load_tools_with_client(
        {server.name: connection},
        server_name=server.name,
    )
    result: list[dict[str, str | None]] = []
    for tool in tools:
        bare_name = _strip_tool_prefix(tool.name, server.name)
        result.append(
            {
                "name": bare_name,
                "fullName": tool.name,
                "description": getattr(tool, "description", None) or "",
            }
        )
    return result


async def test_mcp_connection(
    name: str,
    transport: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    """测试 MCP Server 连接（仅验证能否拉取 tools）。"""
    from types import SimpleNamespace

    probe = SimpleNamespace(name=name.strip(), transport=transport, config=config)
    await list_mcp_server_tools(probe)  # type: ignore[arg-type]
    return {"success": True}


async def list_mcp_tools_by_config(
    name: str,
    transport: int,
    config: dict[str, Any],
) -> list[dict[str, str | None]]:
    """按连接配置列出 MCP tools。"""
    from types import SimpleNamespace

    probe = SimpleNamespace(name=name.strip(), transport=transport, config=config)
    return await list_mcp_server_tools(probe)  # type: ignore[arg-type]


async def load_mcp_tools_from_servers(
    servers: list[McpServerInfo],
    tool_cache: dict[str, list[str]] | None = None,
) -> list[BaseTool]:
    """连接多个 MCP Server 并返回 LangChain tools。失败的 server 会被跳过。"""
    if not servers:
        return []

    cache = tool_cache or {}
    all_tools: list[BaseTool] = []

    for server in servers:
        try:
            connection = build_mcp_connection(server)
        except Exception as exc:  # noqa: BLE001
            logger.warning("跳过无效 MCP Server `%s`: %s", server.name, exc)
            continue

        tools = await _load_tools_with_client(
            {server.name: connection},
            server_name=server.name,
        )
        if not tools:
            continue

        selected = cache.get(server.id)
        if server.id not in cache:
            selected = None
        filtered = _filter_tools_for_server(tools, server, selected)
        all_tools.extend(filtered)

    return all_tools
