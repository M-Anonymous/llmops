"""expand model api_key and base_url length

Revision ID: a1b2c3d4e5f6
Revises: cd06b554aa51
Create Date: 2026-07-26 11:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "cd06b554aa51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "model_info",
        "api_key",
        existing_type=sa.String(length=100),
        type_=sa.String(length=512),
        existing_nullable=False,
        comment="API Key",
    )
    op.alter_column(
        "model_info",
        "base_url",
        existing_type=sa.String(length=100),
        type_=sa.String(length=255),
        existing_nullable=False,
        comment="调用地址",
    )


def downgrade() -> None:
    op.alter_column(
        "model_info",
        "base_url",
        existing_type=sa.String(length=255),
        type_=sa.String(length=100),
        existing_nullable=False,
        comment="调用地址",
    )
    op.alter_column(
        "model_info",
        "api_key",
        existing_type=sa.String(length=512),
        type_=sa.String(length=100),
        existing_nullable=False,
        comment="API Key",
    )
