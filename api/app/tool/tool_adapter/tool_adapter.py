import inspect
from abc import ABC, abstractmethod
from pathlib import Path
from fastapi import Depends
from langchain_core.tools import BaseTool
from importlib.util import spec_from_file_location, module_from_spec
from app.service.tool.api_tool_service import ApiToolService, get_api_tool_service
from app.tool.api_tool.api_tool_entity_2_tool import get_api_tool_from_entity


class ToolAdapter(ABC):

    def __init__(self):
        self.tool_name_prefix = None
        self.tools_dict: dict[str,BaseTool] = {}

    async def initialize(self):
        self.tools_dict = await self._load_tools()

    @abstractmethod
    async def _load_tools(self) -> dict[str,BaseTool]:
        pass


    def get_tool_schema(self,tool_name: str):
        tool_name = self.tool_name_prefix + tool_name
        if tool_name not in self.tools_dict:
            raise ValueError(f"tool {tool_name} not found")
        tool_instance = self.tools_dict[tool_name]

        # 1. 获取 Pydantic 模型类
        schema_class = tool_instance.get_input_schema()
        parameters = {}
        if hasattr(schema_class, "model_json_schema"):
            parameters = schema_class.model_json_schema()  # Pydantic v2
        # 3. 【优化】移除 Pydantic 自动生成的冗余字段（title 和 description），
        #    避免干扰大模型对参数的理解
        parameters.pop("title", None)
        parameters.pop("description", None)

        # 4. 组装成 OpenAI / 主流大模型 API 的标准格式
        return {
            "type": "function",
            "function": {
                "name": tool_instance.name,
                "description": tool_instance.description,
                "parameters": parameters
            }
        }

    def invoke(self,tool_name: str,kwargs: dict):
        tool_name = self.tool_name_prefix + tool_name
        if tool_name not in self.tools_dict:
            raise ValueError(f"tool {tool_name} not found")
        return self.tools_dict[tool_name].invoke(kwargs)




"""
api 工具
arg_schema:
{
  "type": "function",
  "name": "get_weather",
  "description": "Retrieves current weather for the given location.",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City and country e.g. Bogotá, Colombia"
      },
      "units": {
        "type": "string",
        "enum": ["Notion", "FeiShu"],
        "description": "Units the temperature will be returned in."
      }
    },
    "required": ["location", "units"],
    "additionalProperties": false
  },
  "strict": true
}
"""

class ApiToolAdapter(ToolAdapter):

    def __init__(self,api_tool_service: ApiToolService):
        super().__init__()
        self.api_tool_service = api_tool_service
        self.tool_name_prefix = 'api_'


    async def _load_tools(self):
        tools = await self.api_tool_service.get_tools()
        tools_dict = { self.tool_name_prefix + tool.name : get_api_tool_from_entity(tool) for tool in tools }
        return tools_dict



async def get_api_tool_adapter(api_tool_service: ApiToolService = Depends(get_api_tool_service)):
    adapter = ApiToolAdapter(api_tool_service)
    await adapter.initialize()
    return adapter



"""
遵循 OpenApi Swagger 规范的接口工具
"""
class OpenApiToolAdapter(ToolAdapter):

    def _load_tools(self) -> dict[str, BaseTool]:
        pass

"""
内置工具
"""
class BuiltinToolAdapter(ToolAdapter):

    def __init__(self):
        super().__init__()
        self.tool_name_prefix = 'builtin_'


    async def _load_tools(self) -> dict[str,BaseTool] :
        tools_dict = {}
        current_file_path = Path(__file__).resolve()
        target_dir = current_file_path.parent.parent / "builtin_tool"
        if not target_dir.exists():
            raise ValueError(f"Builtin tool directory not found: {target_dir}")
        for file_path in target_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            try:
                # 3. 动态导入模块
                module_name = f"tool.builtin_tool.{file_path.stem}"
                spec = spec_from_file_location(module_name, file_path)
                if spec is None or spec.loader is None:
                    continue
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                # 4. 在模块中寻找继承自 BaseTool 的类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # 确保是 BaseTool 的子类，且不是 BaseTool 本身
                    if issubclass(obj, BaseTool) and obj is not BaseTool:
                        # 5. 实例化工具
                        tool_instance = obj()
                        # 6. 生成统一名称 (例如: builtin_weather)
                        tool_name = self.tool_name_prefix + tool_instance.name
                        tools_dict[tool_name] = tool_instance

            except Exception as e:
                print(f"Error loading tool from {file_path}: {e}")

        return tools_dict

async def get_builtin_tool_adapter():
    adapter = BuiltinToolAdapter()
    await adapter.initialize()
    return adapter
