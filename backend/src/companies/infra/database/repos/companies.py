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
