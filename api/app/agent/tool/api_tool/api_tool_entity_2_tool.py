import json
from typing import Type, Optional

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import ValidationError, BaseModel,create_model, Field
from app.entity.tool.tool_entity import ApiToolEntity
from app.request.tool.tool import ApiConfig, HttpMethod


def get_api_tool_from_entity(api_tool_entity: ApiToolEntity) -> BaseTool:
    tool_name = api_tool_entity.name
    tool_desc = api_tool_entity.desc
    try:
        api_config: ApiConfig = ApiConfig.model_validate(api_tool_entity.api_config)
    except ValidationError as e:
        # 如果数据库里的脏数据不符合 ApiConfig 规范，优雅地抛出错误
        raise ValueError(f"工具 [{tool_name}] 的 API 配置格式错误: {e}")
    # 2. 动态生成大模型需要的 arg_schema
    properties,required_fields  = {},[]

    # 合并 GET 的 params 和 POST 的 body
    all_params = api_config.params + api_config.body

    for param in all_params:
        properties[param.name] = {
            "type": param.type.value,
            "description": param.desc
        }
        if param.enum:
            properties[param.name]["enum"] = param.enum
        if param.required:
            required_fields.append(param.name)

    def create_dynamic_schema() -> type[BaseModel]:
        """
        动态生成真实的 Pydantic 模型
        """
        # 1. 构建真实的字段字典
        field_definitions = {}
        for name, prop in properties.items():
            # 默认当作 str 处理，如果有 required 标记则不加默认值
            field_type = str
            description = prop.get("description", "")

            if name in required_fields:
                # 必填字段：使用 Field(...)
                field_definitions[name] = (field_type, Field(description=description))
            else:
                # 可选字段：使用 Optional 或默认值 None
                from typing import Optional
                field_definitions[name] = (Optional[field_type], Field(default=None, description=description))

        # 2. 动态创建带有真实字段的 Pydantic 模型
        return create_model(
            "DynamicApiSchema",  # 模型名称
            **field_definitions  # 传入真实的字段定义
        )

    dynamic_schema = create_dynamic_schema()


    # 3. 定义具体的工具类
    class DynamicApiTool(BaseTool):
        name: str = tool_name
        description: str = tool_desc
        args_schema: Type[BaseModel] = dynamic_schema
        _api_config: ApiConfig = api_config

        def _run(self, config: Optional[RunnableConfig] = None, **kwargs) -> str:
            print(f"[DEBUG] Dynamic Schema Properties: {properties}")
            print(f"[DEBUG] Required Fields: {required_fields}")

            context = config.get("configurable", {}) if config else {}
            url = self._api_config.base_url.rstrip("/") + self._api_config.path

            # 处理 Headers (支持动态 Token)
            headers = {"Content-Type": "application/json"}
            for head_param in self._api_config.headers:
                if head_param.inject_from_context:
                    token = context.get("token")
                    if not token: return "错误：该接口需要用户登录，但未获取到用户凭证。"
                    headers[head_param.name] = f"Bearer {token}"
                elif head_param.name in kwargs:
                    headers[head_param.name] = kwargs[head_param.name]
                elif head_param.default_value:
                    headers[head_param.name] = head_param.default_value

            # 极简的参数分发 (无需正则替换，直接按 Method 归类)
            query_params = {p.name: kwargs[p.name] for p in self._api_config.params if p.name in kwargs}
            body_data = {p.name: kwargs[p.name] for p in self._api_config.body if
                         p.name in kwargs} if self._api_config.method == HttpMethod.POST else {}

            try:
                if self._api_config.method == HttpMethod.GET:
                    response = httpx.get(url, params=query_params, headers=headers, timeout=10.0)
                else:
                    response = httpx.post(url, json=body_data, params=query_params, headers=headers, timeout=10.0)
                try:
                    return json.dumps(response.json(), ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    return response.text
            except httpx.RequestError as exception:
                return f"请求失败: {str(exception)}"

    return DynamicApiTool()