from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.entity.parent.base import Base,CommonMixin


class AccountInfo(Base,CommonMixin):

    __tablename__ = 'account_info'

    # 1. 主键
    id: Mapped[int] = mapped_column(
        primary_key=True,
        nullable=False,
        default=None,
        comment="用户唯一标识符")

    # 2. 字符串长度 + 索引 + 注释
    # String(100) 表示最大长度为 100
    # index=True 表示为该字段创建普通索引
    # unique=True 表示创建唯一索引
    # comment="..." 用于添加字段注释（会同步到数据库）

    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="用户登录邮箱"
    )

    # 3. 字符串长度 + 注释
    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=None,
        comment="用户昵称，长度限制50"
    )

    # 4. 允许为空 + 字符串长度 + 注释
    avatar: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,  # 头像可能为空，建议改为允许为空
        default=None,
        comment="用户头像URL地址"
    )

    """
        # 5. 复合索引示例（如果需要多字段组合查询）
        # 可以在类级别使用 __table_args__ 来定义复合索引
        __table_args__ = (
        Index('idx_nickname_email', 'nickname', 'email'),  # 复合索引
    )
    """