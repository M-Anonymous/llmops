import json
from typing import Any, Optional, Type

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, ValidationError, create_model

from app.entity.tool.tool_entity import ApiToolEntity
from app.request.tool.tool import ApiConfig, HttpMethod


def get_api_tool_from_entity(api_tool_entity: ApiToolEntity) -> BaseTool:
    tool_name = api_tool_entity.name
    tool_desc = api_tool_entity.desc
    try:
        api_config: ApiConfig = ApiConfig.model_validate(api_tool_entity.api_config)
    except ValidationError as e:
        raise ValueError(f"工具 [{tool_name}] 的 API 配置格式错误: {e}")

    properties, required_fields = {}, []
    all_params = api_config.params + api_config.body

    for param in all_params:
        properties[param.name] = {
            "type": param.type.value,
            "description": param.desc,
        }
        if param.enum:
            properties[param.name]["enum"] = param.enum
        if param.required:
            required_fields.append(param.name)

    def create_dynamic_schema() -> type[BaseModel]:
        field_definitions = {}
        for name, prop in properties.items():
            field_type = str
            description = prop.get("description", "")
            if name in required_fields:
                field_definitions[name] = (field_type, Field(description=description))
            else:
                field_definitions[name] = (
                    Optional[field_type],
                    Field(default=None, description=description),
                )
        return create_model("DynamicApiSchema", **field_definitions)

    dynamic_schema = create_dynamic_schema()

    class DynamicApiTool(BaseTool):
        name: str = tool_name
        description: str = tool_desc
        args_schema: Type[BaseModel] = dynamic_schema
        _api_config: ApiConfig = api_config

        def _build_request(
            self,
            config: Optional[RunnableConfig],
            kwargs: dict[str, Any],
        ) -> tuple[str, dict[str, str], dict[str, Any], dict[str, Any]] | str:
            context = config.get("configurable", {}) if config else {}
            url = self._api_config.base_url.rstrip("/") + self._api_config.path

            headers = {"Content-Type": "application/json"}
            for head_param in self._api_config.headers:
                if head_param.inject_from_context:
                    token = context.get("token")
                    if not token:
                        return "错误：该接口需要用户登录，但未获取到用户凭证。"
                    headers[head_param.name] = f"Bearer {token}"
                elif head_param.name in kwargs:
                    headers[head_param.name] = kwargs[head_param.name]
                elif head_param.default_value:
                    headers[head_param.name] = head_param.default_value

            query_params = {
                p.name: kwargs[p.name]
                for p in self._api_config.params
                if p.name in kwargs
            }
            body_data = (
                {
                    p.name: kwargs[p.name]
                    for p in self._api_config.body
                    if p.name in kwargs
                }
                if self._api_config.method == HttpMethod.POST
                else {}
            )
            return url, headers, query_params, body_data

        @staticmethod
        def _format_response(response: httpx.Response) -> str:
            try:
                return json.dumps(response.json(), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                return response.text

        def _run(self, config: Optional[RunnableConfig] = None, **kwargs) -> str:
            prepared = self._build_request(config, kwargs)
            if isinstance(prepared, str):
                return prepared
            url, headers, query_params, body_data = prepared

            try:
                if self._api_config.method == HttpMethod.GET:
                    response = httpx.get(
                        url, params=query_params, headers=headers, timeout=10.0
                    )
                else:
                    response = httpx.post(
                        url,
                        json=body_data,
                        params=query_params,
                        headers=headers,
                        timeout=10.0,
                    )
                return self._format_response(response)
            except httpx.RequestError as exception:
                return f"请求失败: {str(exception)}"

        async def _arun(self, config: Optional[RunnableConfig] = None, **kwargs) -> str:
            prepared = self._build_request(config, kwargs)
            if isinstance(prepared, str):
                return prepared
            url, headers, query_params, body_data = prepared

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    if self._api_config.method == HttpMethod.GET:
                        response = await client.get(
                            url, params=query_params, headers=headers
                        )
                    else:
                        response = await client.post(
                            url,
                            json=body_data,
                            params=query_params,
                            headers=headers,
                        )
                return self._format_response(response)
            except httpx.RequestError as exception:
                return f"请求失败: {str(exception)}"

    return DynamicApiTool()
