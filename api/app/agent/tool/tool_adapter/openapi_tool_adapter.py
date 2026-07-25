from langchain_core.tools import BaseTool

from app.agent.tool.tool_adapter.base import ToolAdapter


class OpenApiToolAdapter(ToolAdapter):
    """遵循 OpenAPI / Swagger 规范的接口工具适配器"""

    def __init__(self):
        super().__init__()
        self.tool_name_prefix = "openapi_"

    async def _load_tools(self) -> dict[str, BaseTool]:
        return {}
