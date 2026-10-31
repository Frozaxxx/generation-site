from typing import Annotated

from fastapi import Depends

from src.companies.dependencies import CompanyRepoDep
from src.core.database import session_factory
from src.jobs.dependencies import JobRunnerDep
from src.llm.dependencies import get_llm_client
from src.shared.dependencies.database import DBSession

from ..application.pipeline import SiteBuilder
from ..application.service import SiteService
from ..infra.database.repos.sites import SqlSiteVersionRepository


def get_site_repo(session: DBSession) -> SqlSiteVersionRepository:
    return SqlSiteVersionRepository(session)


SiteRepoDep = Annotated[SqlSiteVersionRepository, Depends(get_site_repo)]


def get_site_service(
    companies: CompanyRepoDep,
    sites: SiteRepoDep,
    runner: JobRunnerDep,
) -> SiteService:
    return SiteService(companies, sites, runner, SiteBuilder(get_llm_client(), session_factory))


SiteServiceDep = Annotated[SiteService, Depends(get_site_service)]

__all__ = ["SiteRepoDep", "SiteServiceDep", "get_site_service"]
