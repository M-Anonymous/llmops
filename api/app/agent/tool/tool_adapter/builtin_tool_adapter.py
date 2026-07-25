import inspect
from pathlib import Path

from importlib.util import module_from_spec, spec_from_file_location
from langchain_core.tools import BaseTool

from app.agent.tool.tool_adapter.base import ToolAdapter


class BuiltinToolAdapter(ToolAdapter):
    """内置工具适配器：从 builtin_tool 目录动态加载"""

    def __init__(self):
        super().__init__()
        self.tool_name_prefix = "builtin_"

    async def _load_tools(self) -> dict[str, BaseTool]:
        tools_dict = {}
        current_file_path = Path(__file__).resolve()
        target_dir = current_file_path.parent.parent / "builtin_tool"
        if not target_dir.exists():
            raise ValueError(f"Builtin tool directory not found: {target_dir}")

        for file_path in target_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            try:
                module_name = f"tool.builtin_tool.{file_path.stem}"
                spec = spec_from_file_location(module_name, file_path)
                if spec is None or spec.loader is None:
                    continue
                module = module_from_spec(spec)
                spec.loader.exec_module(module)

                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj is not BaseTool:
                        tool_instance = obj()
                        tool_name = self.tool_name_prefix + tool_instance.name
                        tools_dict[tool_name] = tool_instance
            except Exception as e:
                print(f"Error loading tool from {file_path}: {e}")

        return tools_dict


async def get_builtin_tool_adapter() -> BuiltinToolAdapter:
    adapter = BuiltinToolAdapter()
    await adapter.initialize()
    return adapter
