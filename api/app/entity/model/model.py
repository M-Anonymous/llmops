import uuid

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.entity.parent.base import Base,CommonMixin


class ModelInfo:
    __tablename__ = 'model_info'

    # 1. 主键与基础标识
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid.uuid4().hex,
        comment="模型全局唯一标识符(UUID)"
    )

    account_id: Mapped[int] = mapped_column(
        Integer,
        default=None,
        nullable=False,
        comment="关联的用户id"
    )

    icon: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,  # 头像可能为空，建议改为允许为空
        default=None,
        comment="模型图标"
    )

    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="模型显示名称"
    )


    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="模型名称"
    )

    api_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="模型名称"
    )

    # 3. 字符串长度 + 注释
    desc: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=None,
        comment="知识库描述"
    )

