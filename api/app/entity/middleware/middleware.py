from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.entity.parent.base import Base, CommonMixin, UUID_PK_KWARGS


class MiddlewareInfo(Base, CommonMixin):


    __tablename__ = 'middleware_info'

    # 1. 主键与基础标识
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        **UUID_PK_KWARGS,
        comment="中间件唯一标识符(UUID)"
    )

    account_id: Mapped[int] = mapped_column(
        Integer,
        default=None,
        nullable=False,
        comment="关联的用户id"
    )

    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default=None,
        comment="中间价显示名称",
    )

    type: Mapped[int] = mapped_column(
        Integer,
        default=None,
        nullable=False,
        comment="中间件类型 0:SummarizationMiddleware 1:HumanInTheLoopMiddleware"
    )

    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=None,
        comment="中间件配置"
    )

"""
0 SummarizationMiddleware config
{
    "model":"model_id",
    "trigger":["tokens",4000],
    "keep":["messages",20]
}
{
    "model":"model_id",
    "trigger":[["tokens",3000],["messages",20]],
    "keep":["messages",20]
}
{
    "model":"model_id",
    "trigger":[{"tokens":5000,"messages":3},{"tokens":3000,"messages":6}],
    "keep":["messages",20]
}
{
    "model":"model_id",
    "trigger":["fraction",0.8],
    "keep":["fraction",0.3]
}
"""

"""
1 HumanInTheLoopMiddleware
{
    "interrupt_on:{
        "write_file": True,
        "execute_sql": {
            "allowed_decisions":["approve","reject"],
            "when":"",
            "description":""
            
        },
        "read_file": False 
    }
    "description_prefix":"Tool execution pending approval"

}
"""