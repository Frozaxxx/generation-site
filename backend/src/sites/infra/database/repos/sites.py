from uuid import UUID

from sqlalchemy import func, select

from src.shared.infra.database.repos.sqlalchemy import SqlAlchemyRepository

from ....domain.entities import SiteVersion
from ....domain.enums import SiteLanguage, SiteStatus
from ..mappers import SiteVersionMapper
from ..models import SiteVersionOrm


class SqlSiteVersionRepository(SqlAlchemyRepository[SiteVersion, SiteVersionOrm]):
    model = SiteVersionOrm
    model_mapper = SiteVersionMapper

    async def by_company(self, company_id: UUID) -> list[SiteVersion]:
        stmt = (
            select(self.model)
            .where(self.model.company_id == company_id)
            .order_by(self.model.number.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self.model_mapper.from_model(row) for row in rows]

    async def next_number(self, company_id: UUID) -> int:
        stmt = select(func.max(self.model.number)).where(self.model.company_id == company_id)
        return (await self._session.scalar(stmt) or 0) + 1

    async def reusable(
        self, company_id: UUID, revision: int, language: SiteLanguage
    ) -> SiteVersion | None:
        """Последняя готовая версия с теми же фактами и языком: её тексты можно взять даром."""

        stmt = (
            select(self.model)
            .where(
                self.model.company_id == company_id,
                self.model.company_revision == revision,
                self.model.language == language.value,
                self.model.status == SiteStatus.READY.value,
            )
            .order_by(self.model.number.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return None if row is None else self.model_mapper.from_model(row)
