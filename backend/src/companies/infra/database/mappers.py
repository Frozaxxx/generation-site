from pydantic import TypeAdapter

from src.shared.infra.database.mappers import ModelMapper
from src.shared.infra.database.types import aware

from ...domain.entities import Company
from ...domain.enums import CompanyStatus
from ...domain.serialization import profile_from_dict, profile_to_dict
from ...domain.vo import GenerationInfo, GenerationParams
from .models import CompanyOrm

_params_adapter = TypeAdapter(GenerationParams)
_generation_adapter = TypeAdapter(GenerationInfo)


class CompanyMapper(ModelMapper[Company, CompanyOrm]):
    """Преобразует компанию между доменной сущностью и ORM-моделью."""

    @staticmethod
    def from_model(model: CompanyOrm) -> Company:
        return Company(
            id=model.id,
            created_at=aware(model.created_at),  # pyright: ignore[reportArgumentType]
            updated_at=aware(model.updated_at),  # pyright: ignore[reportArgumentType]
            params=_params_adapter.validate_python(model.params),
            profile=profile_from_dict(model.profile),
            status=CompanyStatus(model.status),
            revision=model.revision,
            generation=(
                _generation_adapter.validate_python(model.generation)
                if model.generation is not None
                else None
            ),
            approved_at=aware(model.approved_at),
        )

    @staticmethod
    def to_model(entity: Company) -> CompanyOrm:
        return CompanyOrm(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            brand_name=entity.profile.brand.name,
            country=entity.params.country,
            direction=entity.params.direction,
            service_type=entity.params.service_type,
            scale=entity.params.scale.value,
            status=entity.status.value,
            revision=entity.revision,
            params=_params_adapter.dump_python(entity.params, mode="json"),
            profile=profile_to_dict(entity.profile),
            generation=(
                _generation_adapter.dump_python(entity.generation, mode="json")
                if entity.generation is not None
                else None
            ),
            approved_at=entity.approved_at,
        )
