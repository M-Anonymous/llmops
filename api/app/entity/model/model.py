from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.entity.parent.base import Base, CommonMixin, UUID_PK_KWARGS


class ModelInfo(Base, CommonMixin):

    __tablename__ = "model_info"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="模型全局唯一标识符(UUID)",
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
        comment="模型图标",
    )

    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="模型显示名称",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="模型名称",
    )

    api_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default=None,
        comment="API Key",
    )

    desc: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=None,
        comment="模型描述",
    )

    base_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=None,
        comment="调用地址",
    )
