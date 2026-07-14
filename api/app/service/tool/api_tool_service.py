from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity import ApiToolEntity
from app.entity.tool.tool_entity import ApiToolRelation
from app.request.tool.tool import ApiToolRequest
from app.service.oauth.current_user import CurrentUser


class ApiToolService:

    def __init__(self,account_id : int, db: AsyncSession):
        self.db = db
        self.account_id = account_id

    async def add_tool(self,request : ApiToolRequest) -> str:
        data = request.model_dump(exclude_unset=True)
        entity = ApiToolEntity(**data)
        entity.createBy =self.account_id
        entity.updateBy = self.account_id
        self.db.add(entity)

        # 执行 flush 会将数据发送给数据库分配 UUID，但不会真正提交事务
        await self.db.flush()

        # 此时 entity.id 已经有值了，可以安全地创建关联关系
        relation = ApiToolRelation(
            account_id=self.account_id,
            tool_id = entity.id,
        )
        self.db.add(relation)

        # 所有操作都准备好了，最后统一提交
        # 如果这一步失败，上面的 entity 也会被自动回滚，数据库干干净净
        await self.db.commit()

        # 6. 提交成功后，刷新实体获取最新状态
        await self.db.refresh(entity)

        return entity.id

    async def get_tools(self) -> list[ApiToolEntity]:
        statement = (
            select(ApiToolEntity)
            .join(ApiToolRelation, ApiToolEntity.id == ApiToolRelation.tool_id)
            .where(ApiToolRelation.account_id == self.account_id)
            .order_by(ApiToolEntity.createAt.desc())  # 按创建时间倒序
        )

        # 执行异步查询
        result = await self.db.execute(statement)
        tools = result.scalars().all()

        # 处理空结果（避免返回 None）
        return [tool for tool in tools]






async def get_api_tool_service(account_id: int = Depends(CurrentUser()),db: AsyncSession = Depends(get_pg_session)) -> ApiToolService:
    return ApiToolService(account_id,db)