from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.entity.parent.base import Base, CommonMixin, UUID_PK_KWARGS


class SessionInfo(Base, CommonMixin):

    __tablename__ = "session_info"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="会话id(UUID)",
    )

    account_id: Mapped[int | None] = mapped_column(
        Integer,
        default=None,
        nullable=True,
        comment="关联的用户id（登录用户）",
    )

    visitor_id: Mapped[str | None] = mapped_column(
        String(36),
        default=None,
        nullable=True,
        comment="访客 id（未登录用户，由前端传递）",
    )

    agent_id: Mapped[str | None] = mapped_column(
        String(36),
        default=None,
        nullable=True,
        comment="关联的 agent",
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        default=None,
        nullable=True,
        comment="会话标题",
    )
