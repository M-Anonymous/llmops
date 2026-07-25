from fastapi import Depends

from app.agent.tool.api_tool.api_tool_entity_2_tool import get_api_tool_from_entity
from app.agent.tool.tool_adapter.base import ToolAdapter
from app.service.tool.api_tool_service import ApiToolService, get_api_tool_service


class ApiToolAdapter(ToolAdapter):
    """数据库配置的 API 工具适配器"""

    def __init__(self, api_tool_service: ApiToolService):
        super().__init__()
        self.api_tool_service = api_tool_service
        self.tool_name_prefix = "api_"

    async def _load_tools(self):
        tools = await self.api_tool_service.get_tools()
        tools_dict = {}
        for tool in tools:
            if not tool.enabled:
                continue
            tools_dict[self.tool_name_prefix + tool.name] = get_api_tool_from_entity(tool)
        return tools_dict


async def get_api_tool_adapter(
    api_tool_service: ApiToolService = Depends(get_api_tool_service),
) -> ApiToolAdapter:
    adapter = ApiToolAdapter(api_tool_service)
    await adapter.initialize()
    return adapter
