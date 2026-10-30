from typing import Self

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.domain.entities import AggregateRoot
from src.shared.domain.exceptions import InvariantViolationError
from src.shared.utils.time import current_datetime

from .checks import Issue, errors_only
from .enums import CompanyStatus
from .profile import CompanyProfile
from .vo import GenerationInfo, GenerationParams


@dataclass(kw_only=True)
class Company(AggregateRoot):
    """
    Компания и её карточка. Каждое изменение карточки увеличивает ревизию: сайты
    собираются из снимка конкретной ревизии и не меняются незаметно.
    """

    params: GenerationParams
    profile: CompanyProfile
    status: CompanyStatus = CompanyStatus.DRAFT
    revision: int = 1
    generation: GenerationInfo | None = None
    approved_at: datetime | None = field(default=None)

    @classmethod
    def create(
        cls,
        *,
        params: GenerationParams,
        profile: CompanyProfile,
        generation: GenerationInfo | None = None,
    ) -> Self:
        """Создаёт черновик компании из результата генерации."""

        return cls(params=params, profile=profile, generation=generation)

    @property
    def is_approved(self) -> bool:
        return self.status is CompanyStatus.APPROVED

    def edit(self, profile: CompanyProfile) -> bool:
        """
        Применяет ручные правки. Изменённая карточка снова становится черновиком,
        чтобы в сайт не попали непроверенные факты. Возвращает `True`, если что-то
        действительно поменялось.
        """

        if profile == self.profile:
            return False

        self.profile = profile
        self.revision += 1
        self.status = CompanyStatus.DRAFT
        self.approved_at = None
        self.touch()
        return True

    def approve(self, issues: list[Issue]) -> None:
        """Утверждает карточку, если проверки не нашли ошибок."""

        if errors := errors_only(issues):
            raise InvariantViolationError(
                "Карточку нельзя утвердить: исправьте ошибки проверки",
                details=[issue.as_dict() for issue in errors],
            )

        self.status = CompanyStatus.APPROVED
        self.approved_at = current_datetime()
        self.touch()
