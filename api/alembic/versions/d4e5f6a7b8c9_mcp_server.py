"""mcp_server

Revision ID: d4e5f6a7b8c9
Revises: bf817be67777
Create Date: 2026-07-29 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "bf817be67777"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mcp_server_info",
        sa.Column("id", sa.String(length=36), nullable=False, comment="MCP Server 唯一标识符(UUID)"),
        sa.Column("account_id", sa.Integer(), nullable=False, comment="关联的用户 id"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="内部名称（连接键，需账号内唯一）"),
        sa.Column("label", sa.String(length=255), nullable=False, comment="显示名称"),
        sa.Column("desc", sa.Text(), nullable=False, comment="描述"),
        sa.Column(
            "transport",
            sa.Integer(),
            nullable=False,
            comment="传输类型 0:stdio 1:sse 2:streamable_http",
        ),
        sa.Column("config", sa.JSON(), nullable=False, comment="连接配置 JSON"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="是否启用"),
        sa.Column(
            "create_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "update_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mcp_server_info_account_name",
        "mcp_server_info",
        ["account_id", "name"],
        unique=True,
    )
    op.add_column(
        "agent_config",
        sa.Column(
            "mcp_server_ids",
            postgresql.ARRAY(sa.String(length=36)),
            nullable=True,
            comment="关联的 MCP Server id 列表",
        ),
    )


def downgrade() -> None:
    op.drop_column("agent_config", "mcp_server_ids")
    op.drop_index("ix_mcp_server_info_account_name", table_name="mcp_server_info")
    op.drop_table("mcp_server_info")
