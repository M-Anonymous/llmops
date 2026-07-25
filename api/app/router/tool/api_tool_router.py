from fastapi import APIRouter, Depends, Query

from app.agent.tool.tool_adapter import ApiToolAdapter, get_api_tool_adapter
from app.request.tool.tool import (
    ApiToolDeleteRequest,
    ApiToolInvokeRequest,
    ApiToolRequest,
    ApiToolUpdateRequest,
)
from app.service.tool.api_tool_service import ApiToolService, get_api_tool_service

api_tool_router = APIRouter(prefix="/tool", tags=["tool"])


@api_tool_router.post("/create")
async def create_tool(
    request: ApiToolRequest,
    api_tool_service: ApiToolService = Depends(get_api_tool_service),
):
    tool_id = await api_tool_service.add_tool(request)
    return {"id": tool_id}


@api_tool_router.post("/delete")
async def delete_tool(
    request: ApiToolDeleteRequest,
    api_tool_service: ApiToolService = Depends(get_api_tool_service),
):
    await api_tool_service.delete_tool(request)
    return {"status": "success"}


@api_tool_router.post("/update")
async def update_tool(
    request: ApiToolUpdateRequest,
    api_tool_service: ApiToolService = Depends(get_api_tool_service),
):
    return await api_tool_service.update_tool(request)


@api_tool_router.get("/list")
async def get_tool_list(
    api_tool_service: ApiToolService = Depends(get_api_tool_service),
):
    return await api_tool_service.get_tool_list()


@api_tool_router.get("/schema")
async def get_tool_schema(
    name: str = Query(..., description="工具内部调用名，如 get_weather"),
    api_tool_adapter: ApiToolAdapter = Depends(get_api_tool_adapter),
):
    return api_tool_adapter.get_tool_schema(name)


@api_tool_router.post("/invoke")
async def invoke_tool(
    request: ApiToolInvokeRequest,
    api_tool_adapter: ApiToolAdapter = Depends(get_api_tool_adapter),
):
    # 必须用异步调用，避免同步 httpx 阻塞事件循环导致回调本服务时死锁超时
    result = await api_tool_adapter.ainvoke(request.name, request.arguments)
    return {"name": request.name, "result": result}
