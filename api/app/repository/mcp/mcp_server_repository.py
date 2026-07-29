from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.mcp.mcp_server import McpServerInfo


class McpServerRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_server(self, server_id: str, account_id: int) -> McpServerInfo | None:
        result = await self.db.execute(
            select(McpServerInfo).where(
                McpServerInfo.id == server_id,
                McpServerInfo.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_by_name(self, name: str, account_id: int) -> McpServerInfo | None:
        result = await self.db.execute(
            select(McpServerInfo).where(
                McpServerInfo.name == name,
                McpServerInfo.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_servers(self, account_id: int) -> list[McpServerInfo]:
        result = await self.db.execute(
            select(McpServerInfo)
            .where(McpServerInfo.account_id == account_id)
            .order_by(McpServerInfo.create_at.desc())
        )
        return list(result.scalars().all())

    async def list_enabled_by_ids(self, server_ids: list[str]) -> list[McpServerInfo]:
        if not server_ids:
            return []
        result = await self.db.execute(
            select(McpServerInfo).where(
                McpServerInfo.id.in_(server_ids),
                McpServerInfo.enabled.is_(True),
            )
        )
        return list(result.scalars().all())

    async def add_server(self, entity: McpServerInfo) -> McpServerInfo:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update_server(self, entity: McpServerInfo) -> McpServerInfo:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete_server(self, entity: McpServerInfo) -> None:
        await self.db.delete(entity)
        await self.db.commit()


async def get_mcp_server_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> McpServerRepository:
    return McpServerRepository(db)
