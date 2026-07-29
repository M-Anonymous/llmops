from sqlalchemy import Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.entity.parent.base import Base, CommonMixin, UUID_PK_KWARGS


class McpServerInfo(Base, CommonMixin):
    """外部 MCP Server 配置。"""

    __tablename__ = "mcp_server_info"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="MCP Server 唯一标识符(UUID)",
    )

    account_id: Mapped[int] = mapped_column(
        Integer,
        default=None,
        nullable=False,
        comment="关联的用户 id",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="内部名称（连接键，需账号内唯一）",
    )

    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=None,
        comment="显示名称",
    )

    desc: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="描述",
    )

    transport: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
        comment="传输类型（当前仅支持 2:streamable_http；预留 0:stdio 1:sse）",
    )

    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=None,
        comment="连接配置 JSON",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )


"""
transport=0 stdio config:
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
  "env": {"FOO": "bar"},
  "cwd": null
}

transport=1 sse config:
{
  "url": "http://localhost:8000/sse",
  "headers": {"Authorization": "Bearer xxx"},
  "timeout": 5,
  "sse_read_timeout": 300
}

transport=2 streamable_http config:
{
  "url": "http://localhost:8000/mcp",
  "headers": {},
  "timeout": 30,
  "sse_read_timeout": 300,
  "terminate_on_close": true
}
"""
