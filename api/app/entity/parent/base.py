from datetime import datetime
import uuid

from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped, mapped_column


def uuid_hex() -> str:
    return uuid.uuid4().hex


# MappedAsDataclass 需用 default_factory + insert_default，不能用 default=callable
UUID_PK_KWARGS = {
    "insert_default": uuid_hex,
    "default_factory": uuid_hex,
}


class Base(MappedAsDataclass,DeclarativeBase):
    """
    Base 负责“告诉 SQLAlchemy 这是数据库表”；
    """
    pass


class CommonMixin:
    """
    CommonMixin 负责“提供公共字段”。
    """
    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=None,  # ← 核心：允许 Python 层为 None
        comment="创建时间"
    )
    update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # ← 自动更新（无需服务层逻辑）
        default=None,
        comment="更新时间"
    )