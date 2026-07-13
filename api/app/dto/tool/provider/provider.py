from typing import Any

from pydantic import BaseModel, Field

from app.entity.tool.tool_entity import ToolEntity


class Provider(BaseModel):

    name: str
    desc: str

    tool_entity_map: dict[str, ToolEntity] = Field(default_factory=dict)
    tool_func_map: dict[str, Any] = Field(default_factory=dict)