from typing import Any

import shutil
from uuid import UUID

from pydantic import ValidationError

from src.shared.application.dtos import Page, Pagination
from src.shared.application.transaction import Transaction
from src.shared.domain.exceptions import BadRequestError, InvalidStateError, NotFoundError

from ..domain.checks import Issue, check_profile
from ..domain.entities import Company
from ..domain.serialization import profile_from_dict
from .dtos import CompanyFilters
from .generation.photos import company_media_dir
from .repos import CompanyRepository


class CompanyService:
    """Библиотека компаний: просмотр, ручное редактирование и утверждение карточек."""

    def __init__(self, company_repo: CompanyRepository, transaction: Transaction) -> None:
        self._company_repo = company_repo
        self._transaction = transaction

    async def get(self, company_id: UUID) -> Company:
        company = await self._company_repo.read(company_id)
        if company is None:
            raise NotFoundError(f"Компания {company_id} не найдена")
        return company

    async def find(self, pagination: Pagination, filters: CompanyFilters) -> Page[Company]:
        return await self._company_repo.find(pagination, filters)

    async def save_generated(self, company: Company) -> Company:
        await self._company_repo.create(company)
        await self._transaction()
        return company

    async def edit_profile(
        self,
        company_id: UUID,
        *,
        data: dict[str, Any],
        revision: int,
    ) -> tuple[Company, list[Issue]]:
        """
        Сохраняет ручные правки. Ревизия защищает от перезаписи чужих изменений,
        если карточку правят в двух вкладках.
        """

        company = await self.get(company_id)
        if company.revision != revision:
            raise InvalidStateError(
                "Карточка уже изменилась, обновите страницу",
                details={"current_revision": company.revision},
            )

        try:
            profile = profile_from_dict(data)
        except ValidationError as error:
            raise BadRequestError(
                "Карточка не соответствует схеме",
                details=[
                    {
                        "path": ".".join(str(part) for part in item["loc"]),
                        "message": item["msg"],
                    }
                    for item in error.errors(include_url=False)
                ],
            ) from None

        if company.edit(profile):
            await self._company_repo.upsert(company)
            await self._transaction()

        return company, check_profile(company.profile, company.params.country)

    async def approve(self, company_id: UUID) -> Company:
        company = await self.get(company_id)
        company.approve(check_profile(company.profile, company.params.country))

        await self._company_repo.upsert(company)
        await self._transaction()
        return company

    async def delete(self, company_id: UUID) -> None:
        await self.get(company_id)
        await self._company_repo.delete(company_id)
        await self._transaction()
        shutil.rmtree(company_media_dir(company_id), ignore_errors=True)
