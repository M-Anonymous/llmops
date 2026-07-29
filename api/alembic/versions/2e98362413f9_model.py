"""model

Revision ID: 2e98362413f9
Revises: 80e2fbd2472f
Create Date: 2026-07-25 19:15:50.244887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2e98362413f9"
down_revision: Union[str, Sequence[str], None] = "80e2fbd2472f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "model_info",
        sa.Column("base_url", sa.String(length=100), nullable=False, comment="调用地址"),
    )


def downgrade() -> None:
    op.drop_column("model_info", "base_url")
