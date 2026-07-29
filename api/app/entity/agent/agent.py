from sqlalchemy import Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.entity.parent.base import Base, CommonMixin, UUID_PK_KWARGS


class AgentConfig(Base, CommonMixin):

    __tablename__ = "agent_config"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="唯一标识符(UUID)",
    )

    account_id: Mapped[int] = mapped_column(
        Integer,
        default=None,
        nullable=False,
        comment="关联的用户id",
    )

    icon: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        comment="agent 图标",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="agent 名称",
    )

    desc: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=None,
        comment="agent 描述",
    )

    system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="系统提示词",
    )

    model_id: Mapped[str | None] = mapped_column(
        String(36),
        default=None,
        nullable=True,
        comment="关联的模型",
    )

    library_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String(36)),
        nullable=True,
        default_factory=list,
        insert_default=list,
        comment="关联的知识库 id 列表",
    )

    tool_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String(36)),
        nullable=True,
        default_factory=list,
        insert_default=list,
        comment="关联的工具 id 列表",
    )

    middleware_ids: Mapped[list[str]] = mapped_column(
            ARRAY(String(36)),
            nullable=True,
            default_factory=list,
            insert_default=list,
            comment="关联的工具 中间件 列表",
        )

    mcp_server_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String(36)),
        nullable=True,
        default_factory=list,
        insert_default=list,
        comment="关联的 MCP Server id 列表",
    )

    runtime_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="Agent 运行时 LLM 参数（preset: creative|balanced|precise|custom）",
    )

    mcp_tool_cache: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="MCP 工具选择，{server_id: [tool_name, ...]}；缺省或 null 表示加载全部",
    )

