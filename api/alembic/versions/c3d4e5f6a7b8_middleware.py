"""middleware

Revision ID: c3d4e5f6a7b8
Revises: 62db8bd87bea
Create Date: 2026-07-28 09:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "62db8bd87bea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "middleware_info",
        sa.Column("id", sa.String(length=36), nullable=False, comment="中间件唯一标识符(UUID)"),
        sa.Column("account_id", sa.Integer(), nullable=False, comment="关联的用户id"),
        sa.Column(
            "type",
            sa.Integer(),
            nullable=False,
            comment="中间件类型 0:SummarizationMiddleware 1:HumanInTheLoopMiddleware",
        ),
        sa.Column("config", sa.JSON(), nullable=False, comment="中间件配置"),
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
    op.drop_table("middleware_info")
