from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.entity.parent.base import Base, CommonMixin, UUID_PK_KWARGS


class VectorStore(Base, CommonMixin):
    __tablename__ = "vector_store"
    __table_args__ = (
        Index("idx_content_tsv", "content_tsv", postgresql_using="gin"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="向量记录全局唯一标识符(UUID)",
    )

    account_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=None,
        comment="关联的用户 id",
    )

    library_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        default=None,
        comment="关联的知识库 id",
    )

    document_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        default=None,
        comment="关联的文档 id",
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=None,
        comment="片段在文档中的序号",
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="片段文本内容",
    )

    content_tsv: Mapped[Any | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple'::regconfig, COALESCE(content, ''::text))",
            persisted=True,
        ),
        nullable=True,
        init=False,
        comment="全文检索向量（由 content 自动生成）",
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1024),
        nullable=True,
        default=None,
        comment="文本 embedding 向量",
    )

    meta: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        server_default="{}",
        default=None,
        comment="扩展元数据",
    )
