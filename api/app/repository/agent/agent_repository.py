from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.component.database.postgres_client import get_pg_session
from app.entity.agent.agent import AgentConfig


class AgentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_agent(self, agent_id: str, account_id: int) -> AgentConfig | None:
        result = await self.db.execute(
            select(AgentConfig).where(
                AgentConfig.id == agent_id,
                AgentConfig.account_id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_agent_by_id(self, agent_id: str) -> AgentConfig | None:
        result = await self.db.execute(
            select(AgentConfig).where(AgentConfig.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def list_agents(self, account_id: int) -> list[AgentConfig]:
        result = await self.db.execute(
            select(AgentConfig)
            .where(AgentConfig.account_id == account_id)
            .order_by(AgentConfig.create_at.desc())
        )
        return list(result.scalars().all())

    async def add_agent(self, entity: AgentConfig) -> AgentConfig:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update_agent(self, entity: AgentConfig) -> AgentConfig:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete_agent(self, entity: AgentConfig) -> None:
        await self.db.delete(entity)
        await self.db.commit()


async def get_agent_repository(
    db: AsyncSession = Depends(get_pg_session),
) -> AgentRepository:
    return AgentRepository(db)
