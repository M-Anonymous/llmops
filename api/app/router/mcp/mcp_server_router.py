from fastapi import APIRouter, Depends, Query

from app.request.mcp.mcp_server import (
    McpServerCreateRequest,
    McpServerDeleteRequest,
    McpServerTestRequest,
    McpServerUpdateRequest,
)
from app.service.mcp.mcp_server_service import (
    McpServerService,
    get_mcp_server_service,
)

mcp_server_router = APIRouter(prefix="/mcp", tags=["mcp"])


@mcp_server_router.post("/create")
async def create_mcp_server(
    request: McpServerCreateRequest,
    mcp_server_service: McpServerService = Depends(get_mcp_server_service),
):
    server_id = await mcp_server_service.create_server(request)
    return {"id": server_id}


@mcp_server_router.post("/delete")
async def delete_mcp_server(
    request: McpServerDeleteRequest,
    mcp_server_service: McpServerService = Depends(get_mcp_server_service),
):
    await mcp_server_service.delete_server(request)
    return {"status": "success"}


@mcp_server_router.post("/update")
async def update_mcp_server(
    request: McpServerUpdateRequest,
    mcp_server_service: McpServerService = Depends(get_mcp_server_service),
):
    return await mcp_server_service.update_server(request)


@mcp_server_router.get("/list")
async def get_mcp_server_list(
    mcp_server_service: McpServerService = Depends(get_mcp_server_service),
):
    return await mcp_server_service.get_server_list()


@mcp_server_router.get("/tools")
async def list_mcp_server_tools(
    server_id: str = Query(..., description="MCP Server ID"),
    mcp_server_service: McpServerService = Depends(get_mcp_server_service),
):
    return await mcp_server_service.list_server_tools(server_id)


@mcp_server_router.post("/test")
async def test_mcp_server_connection(
    request: McpServerTestRequest,
    mcp_server_service: McpServerService = Depends(get_mcp_server_service),
):
    return await mcp_server_service.test_connection(request)


@mcp_server_router.post("/tools")
async def list_mcp_tools_by_config(
    request: McpServerTestRequest,
    mcp_server_service: McpServerService = Depends(get_mcp_server_service),
):
    return await mcp_server_service.list_tools_from_config(request)
