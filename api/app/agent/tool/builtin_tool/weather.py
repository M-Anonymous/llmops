from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, json


class WeatherArgSchema(BaseModel):
    city: str = Field(description = "城市名称")

class WeatherTool(BaseTool):

    name : str = "weather"
    description : str = "获取城市的天气预报信息"
    args_schema : type[BaseModel]  = WeatherArgSchema

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """
        获取城市的天气预报信息
        :param args:
        :param kwargs:
        :return:
        """
        try:
            # 2.从参数中获取city城市名字
            city = kwargs.get("city", "")
            return {
                "city": city,
                "temperature": 36
            }
            return f"获取{city}天气预报信息失败"
        except Exception as e:
            return f"获取{kwargs.get('city', '')}天气预报信息失败"