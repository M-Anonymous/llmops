import uuid
from sqlalchemy import String, Text, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.entity.parent.base import Base, CommonMixin


# 假设 Base 和 CommonMixin 已经导入

class ApiToolEntity(Base, CommonMixin):
    """
    工具定义表：存储所有 API 工具的元数据、Schema 和 HTTP 配置
    """
    __tablename__ = 'api_tool_entity'

    # 1. 主键与基础标识
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid.uuid4().hex,
        comment="工具全局唯一标识符(UUID)"
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        unique=True,
        index=True,
        comment="工具内部调用名(如 get_weather)"
    )

    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="工具显示名称(如 获取天气)"
    )

    desc: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=None,
        comment="工具描述(给大模型看的)"
    )

    api_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=None,
        comment="API 调用配置"
    )


    createBy: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=None,
        comment="创建人"
    )

    updateBy: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=None,
        comment="更新人"
    )


class ApiToolRelation(Base, CommonMixin):
    """
    账户-工具关联表：实现多租户/多用户隔离
    """
    __tablename__ = 'api_tool_relation'

    # 2. 外键与索引
    account_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
        default=None,
        index=True,
        comment="所属账户ID"
    )

    tool_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('api_tool_entity.id'),
        primary_key=True,
        default=None,
        nullable=False,
        index=True,
        comment="关联的工具id"
    )