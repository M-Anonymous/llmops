"""session

Revision ID: cd06b554aa51
Revises: 2e98362413f9
Create Date: 2026-07-26 09:52:28.514709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "cd06b554aa51"
down_revision: Union[str, Sequence[str], None] = "2e98362413f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "session_info",
        sa.Column("id", sa.String(length=36), nullable=False, comment="会话id(UUID)"),
        sa.Column("account_id", sa.Integer(), nullable=False, comment="关联的用户id"),
        sa.Column("agent_id", sa.String(length=36), nullable=True, comment="关联的 agent"),
        sa.Column("title", sa.String(length=255), nullable=True, comment="会话标题"),
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


def downgrade() -> None:
    op.drop_table("session_info")
