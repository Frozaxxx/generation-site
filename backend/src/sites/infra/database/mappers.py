from src.shared.infra.database.mappers import ModelMapper
from src.shared.infra.database.types import aware

from ...domain.entities import SiteVersion
from ...domain.enums import SiteLanguage, SiteStatus
from .models import SiteVersionOrm


class SiteVersionMapper(ModelMapper[SiteVersion, SiteVersionOrm]):
    @staticmethod
    def from_model(model: SiteVersionOrm) -> SiteVersion:
        return SiteVersion(
            id=model.id,
            created_at=aware(model.created_at),  # pyright: ignore[reportArgumentType]
            updated_at=aware(model.updated_at),  # pyright: ignore[reportArgumentType]
            company_id=model.company_id,
            company_revision=model.company_revision,
            number=model.number,
            language=SiteLanguage(model.language),
            theme=model.theme,
            accent=model.accent,
            status=SiteStatus(model.status),
            snapshot=dict(model.snapshot),
            content=dict(model.content),
            issues=list(model.issues),
            pages=list(model.pages),
            cost_usd=model.cost_usd,
            requests=model.requests,
            reused_from=model.reused_from,
        )

    @staticmethod
    def to_model(entity: SiteVersion) -> SiteVersionOrm:
        return SiteVersionOrm(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            company_id=entity.company_id,
            company_revision=entity.company_revision,
            number=entity.number,
            language=entity.language.value,
            theme=entity.theme,
            accent=entity.accent,
            status=entity.status.value,
            snapshot=entity.snapshot,
            content=entity.content,
            issues=entity.issues,
            pages=entity.pages,
            cost_usd=entity.cost_usd,
            requests=entity.requests,
            reused_from=entity.reused_from,
        )
