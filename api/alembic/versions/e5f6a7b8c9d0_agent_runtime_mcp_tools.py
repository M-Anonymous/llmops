"""mcp_server

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-29 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agent_config",
        sa.Column(
            "runtime_config",
            sa.JSON(),
            nullable=True,
            comment="Agent 运行时 LLM 参数（preset / temperature 等）",
        ),
    )
    op.add_column(
        "agent_config",
        sa.Column(
            "mcp_tool_cache",
            sa.JSON(),
            nullable=True,
            comment="MCP 工具选择缓存，key 为 server_id，value 为 tool 名列表",
        ),
    )


def downgrade() -> None:
    op.drop_column("agent_config", "mcp_tool_cache")
    op.drop_column("agent_config", "runtime_config")
