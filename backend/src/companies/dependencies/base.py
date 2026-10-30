from typing import Annotated

from fastapi import Depends

from src.shared.dependencies.database import DBSession

from ..application.repos import CompanyRepository
from ..infra.database.repos.companies import SqlCompanyRepository


def get_company_repo(session: DBSession) -> SqlCompanyRepository:
    """Создаёт репозиторий на сессии текущего запроса."""
    return SqlCompanyRepository(session)


CompanyRepoDep = Annotated[CompanyRepository, Depends(get_company_repo)]
