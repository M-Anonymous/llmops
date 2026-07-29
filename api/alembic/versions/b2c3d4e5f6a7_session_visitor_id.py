"""add visitor_id and make account_id nullable

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-27 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "session_info",
        sa.Column("visitor_id", sa.String(length=36), nullable=True, comment="访客 id"),
    )
    op.alter_column(
        "session_info",
        "account_id",
        existing_type=sa.Integer(),
        nullable=True,
        comment="关联的用户id（登录用户）",
    )


def downgrade() -> None:
    op.alter_column(
        "session_info",
        "account_id",
        existing_type=sa.Integer(),
        nullable=False,
        comment="关联的用户id",
    )
    op.drop_column("session_info", "visitor_id")
