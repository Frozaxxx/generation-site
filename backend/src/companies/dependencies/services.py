from typing import Annotated

from fastapi import Depends

from src.shared.dependencies.database import TransactionDep

from ..application.services import CompanyService
from .base import CompanyRepoDep


def get_company_service(repo: CompanyRepoDep, transaction: TransactionDep) -> CompanyService:
    """Подключает сервис к репозиторию и общей транзакции запроса."""
    return CompanyService(company_repo=repo, transaction=transaction)


CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]
