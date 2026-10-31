from sqlalchemy import select

from src.shared.application.dtos import Page, Pagination
from src.shared.infra.database.repos.sqlalchemy import SqlAlchemyRepository, paginate

from ....application.dtos import CompanyFilters
from ....domain.entities import Company
from ..mappers import CompanyMapper
from ..models import CompanyOrm


class SqlCompanyRepository(SqlAlchemyRepository[Company, CompanyOrm]):
    model = CompanyOrm
    model_mapper = CompanyMapper

    async def recent_concepts(self, limit: int) -> list[dict[str, str]]:
        """Краткое описание последних компаний, чтобы новые на них не походили."""

        stmt = select(self.model).order_by(self.model.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()

        concepts = []
        for row in rows:
            profile, generation = row.profile, row.generation or {}
            concepts.append(
                {
                    "бренд": profile["brand"]["name"],
                    "слоган": profile["brand"]["tagline"],
                    "продукт": profile["product"]["name"],
                    "ниша": (generation.get("concept") or {}).get("ниша", ""),
                    "основание": profile["history"]["founding_story"][:240],
                }
            )
        return concepts

    async def find(
        self,
        pagination: Pagination,
        filters: CompanyFilters | None = None,
    ) -> Page[Company]:
        """Возвращает компании с применением фильтров."""

        stmt = select(self.model)

        if filters:
            if filters.status is not None:
                stmt = stmt.where(self.model.status == filters.status.value)

            if filters.scale is not None:
                stmt = stmt.where(self.model.scale == filters.scale.value)

            if filters.search:
                stmt = stmt.where(self.model.brand_name.ilike(f"%{filters.search.strip()}%"))

        return await paginate(
            session=self._session,
            model=self.model,
            stmt=stmt,
            pagination=pagination,
            mapper=self.model_mapper.from_model,
            sort=filters.sort if filters else "created_at:desc",
        )
