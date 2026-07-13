from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

"""
request example:
{
    "name": "get_weather",
    "label": "天气查询工具",
    "desc": "获取某个城市的天气预报信息",
    "api_config":{
        "base_url":"localhost:8888",
        "path":"/get_weather",
        "method":"GET",
        "params":[
            {
                "name":"city",
                "type":"string",
                "desc":"城市名称",
                "required":true,
                "enum":null,
                "default_value":null,
                "inject_from_context":false
            }
        ]
    }
}
"""

class ApiToolRequest(BaseModel):
    """
    API 工具创建/更新请求模型
    """
    # 1. 基础标识信息
    name: str = Field(
        ...,
        max_length=100,
        description="工具内部调用名(如 get_weather)，需全局唯一"
    )
    label: str = Field(
        ...,
        max_length=100,
        description="工具显示名称(如 获取天气)"
    )
    desc: str = Field(
        ...,
        description="工具描述(给大模型看的，建议写清楚用途和参数说明)"
    )

    api_config: dict = Field(
        ...,
        description="API 调用配置(url, method, headers, body_template)"
    )

# 定义支持的 JSON Schema 基本数据类型枚举
class JsonSchemaType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


# 定义支持的 HTTP 请求方法枚举
class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"


# 参数属性模型
class Property(BaseModel):
    name: str = Field(
        ...,  # ... 表示必填项
        description="参数的名称 (如: location)"
    )
    type: JsonSchemaType = Field(
        ...,  # 必填项
        description="参数的数据类型"
    )
    desc: str = Field(
        ...,  # 必填项
        description="参数的详细描述 (给大模型看的，非常重要)"
    )
    required: bool = Field(
        ...,  # 必填项
        description="该参数是否为必填项"
    )
    enum: Optional[list] = Field(
        default=None,
        description="可选的枚举值列表 (如: ['Notion', 'FeiShu'])"
    )
    # 系统级固定值（如固定的内部 API Key）
    default_value: Optional[str] = Field(default=None, description="系统默认注入的固定值")

    # 标记该参数是否来自用户的运行时上下文（如 Token）
    inject_from_context: bool = Field(
        default=False,
        description="是否从运行时上下文中动态注入（如 user_token）"
    )


# 2. 完善 ApiConfig 模型
class ApiConfig(BaseModel):
    base_url: str = Field(
        ...,
        description="API 基础域名 (如: https://api.example.com)"
    )
    path: str = Field(
        ...,
        description="API 相对路径 (禁止包含 {xxx} 占位符)"
    )
    method: HttpMethod = Field(
        ...,
        description="HTTP 请求方法，仅支持 GET 或 POST"
    )

    # 使用 List[Property] 存储参数配置
    params: List[Property] = Field(
        default_factory=list,
        description="Query 查询参数配置 (通常用于 GET 请求)"
    )
    headers: List[Property] = Field(
        default_factory=list,
        description="HTTP 请求头配置 (如: Authorization, Content-Type)"
    )
    body: List[Property] = Field(
        default_factory=list,
        description="请求体参数配置 (通常用于 POST 请求)"
    )


