from fastapi import APIRouter, Depends, Query

from app.request.tool.tool import ApiToolRequest
from app.service.tool.api_tool_service import ApiToolService, get_api_tool_service
from app.tool.tool_adapter.tool_adapter import ApiToolAdapter, get_api_tool_adapter

api_tool_router = APIRouter(prefix="/tool", tags=["tool"])



@api_tool_router.post("/create_tool")
async def create_tool(request: ApiToolRequest,api_tool_service: ApiToolService = Depends(get_api_tool_service)):
    await api_tool_service.add_tool(request)
    return "success"


@api_tool_router.get("/get_tools")
async def create_tool(api_tool_service: ApiToolService = Depends(get_api_tool_service)):
    return await api_tool_service.get_tools()

@api_tool_router.get("/get_tool_schema")
async def get_tool_schema(api_tool_adapter: ApiToolAdapter = Depends(get_api_tool_adapter)):
    return  api_tool_adapter.get_tool_schema("get_weather")

@api_tool_router.post("/invoke")
async def invoke(api_tool_adapter: ApiToolAdapter = Depends(get_api_tool_adapter)):
    return api_tool_adapter.invoke("get_weather",{"city":"广州"})