from abc import ABC, abstractmethod

from fastapi import HTTPException
from langchain_core.tools import BaseTool


class ToolAdapter(ABC):

    def __init__(self):
        self.tool_name_prefix = None
        self.tools_dict: dict[str, BaseTool] = {}

    async def initialize(self):
        self.tools_dict = await self._load_tools()

    @abstractmethod
    async def _load_tools(self) -> dict[str, BaseTool]:
        pass

    def _resolve_tool_name(self, tool_name: str) -> str:
        prefix = self.tool_name_prefix or ""
        if prefix and tool_name.startswith(prefix):
            return tool_name
        return f"{prefix}{tool_name}"

    def _get_tool(self, tool_name: str) -> BaseTool:
        resolved_name = self._resolve_tool_name(tool_name)
        tool_instance = self.tools_dict.get(resolved_name)
        if not tool_instance:
            raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")
        return tool_instance

    def get_tool_schema(self, tool_name: str) -> dict:
        tool_instance = self._get_tool(tool_name)

        schema_class = tool_instance.get_input_schema()
        parameters = {}
        if hasattr(schema_class, "model_json_schema"):
            parameters = schema_class.model_json_schema()
        parameters.pop("title", None)
        parameters.pop("description", None)

        return {
            "type": "function",
            "function": {
                "name": tool_instance.name,
                "description": tool_instance.description,
                "parameters": parameters,
            },
        }

    def invoke(self, tool_name: str, kwargs: dict):
        tool_instance = self._get_tool(tool_name)
        return tool_instance.invoke(kwargs)

    async def ainvoke(self, tool_name: str, kwargs: dict):
        tool_instance = self._get_tool(tool_name)
        return await tool_instance.ainvoke(kwargs)
