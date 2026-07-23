from sqlalchemy import String, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.entity.parent.base import Base, CommonMixin, UUID_PK_KWARGS

"""
内部知识库，只上传文件
设想：可以兼容外部知识库比如飞书，后续补充
"""
class LibraryInfo(Base,CommonMixin):

    __tablename__ = 'library_info'

    # 1. 主键与基础标识
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="知识库全局唯一标识符(UUID)"
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
        comment="知识库图标"
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=None,
        comment="知识库名称"
    )

    # 3. 字符串长度 + 注释
    desc: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=None,
        comment="知识库描述"
    )


class DocumentInfo(Base,CommonMixin):

    __tablename__ = 'document_info'

    # 1. 主键与基础标识
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="文档全局唯一标识符(UUID)"
    )

    account_id: Mapped[int] = mapped_column(
        Integer,
        default=None,
        nullable=False,
        comment="关联的用户id"
    )

    library_id: Mapped[str] = mapped_column(
        String(36),
        default=None,
        nullable=False,
        comment="关联的知识库id"
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        default=None,
        nullable=False,
        comment="关联的知识库id"
    )

    file_ext: Mapped[str] = mapped_column(
        String(36),
        default=None,
        nullable=False,
        comment="关联的知识库id"
    )

    desc: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=None,
        comment="文档描述"
    )

    file_key: Mapped[str] = mapped_column(
        String(255),
        default=None,
        nullable=False,
        comment="关联的文件key"
    )

class ChunkInfo(Base,CommonMixin):
    __tablename__ = 'chunk_info'

    # 1. 主键与基础标识
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="分片全局唯一标识符(UUID)"
    )

    document_id: Mapped[str] = mapped_column(
        String(36),
        default=None,
        nullable=False,
        comment="关联的文档id"
    )

    position: Mapped[int] = mapped_column(
        Integer,
        default=None,
        nullable=False,
        comment="片段在文档的位置"
    )

    content: Mapped[str] = mapped_column(
        Text,
        default=None,
        nullable=False,
        comment="片断内容"
    )

    hash: Mapped[str] = mapped_column(
        String(255),
        default=None,
        nullable=False,
        comment="内容哈希值"
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )


class LibraryRelation(Base,CommonMixin):

    __tablename__ = 'library_relation'

    # 1. 主键与基础标识
    agent_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="关联的知识库id"
    )

    # 1. 主键与基础标识
    workflow_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="关联的工作流id"
    )

    # 1. 主键与基础标识
    library_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="关联的知识库id"
    )
