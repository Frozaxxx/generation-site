"""
Факты, которые выбирает код, а не модель: параметры, адрес, телефон, домен, год
основания, состав команды, имена и зёрна разнообразия. Так телефон всегда
совпадает с городом, а люди в разных компаниях не повторяются.
"""

from typing import Any

import random
import re
import unicodedata
from dataclasses import dataclass, field

from src.core.settings import openrouter_config
from src.shared.domain.exceptions import BadRequestError
from src.shared.utils.time import current_datetime

from ...domain.catalog import COUNTRIES, DIRECTIONS, SCALES, City, Country, Direction, ServiceType
from ...domain.catalog.business import CUSTOM_KEY, custom_direction, custom_service_type
from ...domain.catalog.people import (
    APPEARANCE,
    LIGHTING,
    NAME_ORIGINS,
    OFFICE_SPOTS,
    OFFICES,
    POSES,
    NameOrigin,
)
from ...domain.catalog.seeds import (
    DELIVERY_FORMATS,
    DEPARTMENTS,
    DIFFERENTIATORS,
    EMAIL_PREFIXES,
    FOUNDING_ARCHETYPES,
    OFFICE_HOURS,
    PRICING_MODELS,
    SECTOR_FOCUS,
)
from ...domain.catalog.trademarks import find_known_brand
from ...domain.enums import CompanyScale, Gender, TeamRole
from ...domain.profile import Address, Brand, Contacts
from ...domain.vo import GenerationParams

_TRANSLIT = str.maketrans(
    {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "ı": "i", "ł": "l", "ş": "s", "ç": "c"}
)

AGE_RANGES: dict[TeamRole, tuple[int, int]] = {
    TeamRole.CEO: (36, 58),
    TeamRole.DEPARTMENT_HEAD: (32, 52),
    TeamRole.SPECIALIST: (26, 45),
}


def slugify(text: str) -> str:
    text = text.lower().translate(_TRANSLIT)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerationRequest:
    """То, что прислал пользователь. `None` - выбрать случайно."""

    brand_name: str | None = None
    country: str | None = None
    direction: str | None = None
    service_type: str | None = None
    scale: CompanyScale | None = None
    model: str | None = None
    with_photos: bool = True
    custom_direction: str | None = None
    custom_service: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PersonSkeleton:
    id: str
    first_name: str
    last_name: str
    gender: Gender
    age: int
    role: TeamRole
    department: str | None
    heritage: str
    appearance: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass(kw_only=True)
class CompanyFacts:
    params: GenerationParams
    country: Country
    direction: Direction
    service_type: ServiceType
    city: City
    legal_form: str
    address: Address
    phone: str
    phone_display: str
    email_prefix: str
    office_hours: str
    founded_year: int
    current_year: int
    employees: int
    team: list[PersonSkeleton]
    photo_setting: str
    seeds: dict[str, str] = field(default_factory=dict)

    def brand(self, name: str, tagline: str) -> Brand:
        domain = f"{slugify(name)}.{self.country.domain_zone}"
        return Brand(
            name=name,
            legal_form=self.legal_form,
            legal_name=f"{name} {self.legal_form}",
            tagline=tagline,
            domain=domain,
        )

    def contacts(self, domain: str) -> Contacts:
        return Contacts(
            address=self.address,
            city_key=self.city.key,
            phone=self.phone,
            phone_display=self.phone_display,
            email=f"{self.email_prefix}@{domain}",
            office_hours=self.office_hours,
        )

    def summary(self) -> dict[str, Any]:
        """Факты для промпта."""

        return {
            "страна": self.country.name_ru,
            "город": f"{self.city.name} ({self.city.name_ru})",
            "район": self.address.district,
            "масштаб": SCALES[self.params.scale].name_ru,
            "сотрудников": self.employees,
            "год основания": self.founded_year,
            "текущий год": self.current_year,
            "правовая форма": self.legal_form,
            "направление": self.direction.name_ru,
            "тип сервиса": f"{self.service_type.name_ru}: {self.service_type.description}",
            "типичные клиенты": ", ".join(self.service_type.typical_clients)
            or "определи сам по типу сервиса",
        }


def _choice[T](rng: random.Random, options: tuple[T, ...] | list[T]) -> T:
    return options[rng.randrange(len(options))]


def resolve_params(request: GenerationRequest, rng: random.Random) -> GenerationParams:
    randomized: list[str] = []

    def pick(name: str, value: Any, options: list[Any]) -> Any:
        if value is not None:
            if value not in options:
                raise BadRequestError(f"Неизвестное значение {name}: {value!r}")
            return value
        randomized.append(name)
        return _choice(rng, options)

    country = pick("country", request.country, list(COUNTRIES))

    custom_dir = (request.custom_direction or "").strip() or None
    custom_srv = (request.custom_service or "").strip() or None

    if custom_dir:
        # Своё направление: в каталоге для него нет типов, сервис тоже свой.
        direction = CUSTOM_KEY
        service_type = CUSTOM_KEY
        custom_srv = custom_srv or custom_dir
    else:
        direction = pick("direction", request.direction, list(DIRECTIONS))
        if custom_srv:
            service_type = CUSTOM_KEY
        else:
            service_type = pick(
                "service_type",
                request.service_type,
                [item.key for item in DIRECTIONS[direction].service_types],
            )
    scale = pick("scale", request.scale, list(SCALES))

    brand_name = (request.brand_name or "").strip() or None
    if brand_name is None:
        randomized.append("brand_name")
    elif known := find_known_brand(brand_name):
        raise BadRequestError(
            f"Название содержит известный бренд «{known}». Сайт выдавал бы себя за реальную "
            "компанию, выберите другое название."
        )

    model = request.model or openrouter_config.text_model
    if request.model is None:
        randomized.append("model")

    return GenerationParams(
        brand_name=brand_name,
        country=country,
        direction=direction,
        service_type=service_type,
        scale=CompanyScale(scale),
        model=model,
        randomized=tuple(randomized),
        custom_direction=custom_dir,
        custom_service=custom_srv,
    )


def _pick_origin(rng: random.Random) -> NameOrigin:
    return rng.choices(NAME_ORIGINS, weights=[origin.weight for origin in NAME_ORIGINS])[0]


@dataclass(slots=True)
class _Pools:
    """Варианты без повторов внутри одной команды."""

    rng: random.Random
    left: dict[str, list[str]] = field(default_factory=dict)

    def take(self, key: str, options: tuple[str, ...]) -> str:
        pool = self.left.get(key)
        if not pool:
            pool = list(options)
            self.rng.shuffle(pool)
            self.left[key] = pool
        return pool.pop()


def random_appearance(rng: random.Random, gender: Gender, pools: _Pools | None = None) -> str:
    pools = pools or _Pools(rng)
    parts = [
        pools.take(f"hair-{gender}", APPEARANCE.hair[gender]),
        f"wearing {pools.take(f'clothing-{gender}', APPEARANCE.clothing[gender])}",
        pools.take("expression", APPEARANCE.expression),
        _choice(rng, APPEARANCE.accessories),
    ]
    if gender is Gender.MALE:
        parts.insert(1, _choice(rng, APPEARANCE.facial_hair))
    pose = pools.take("pose", POSES)
    spot = pools.take("spot", OFFICE_SPOTS)
    light = _choice(rng, LIGHTING)
    return f"{', '.join(part for part in parts if part)}. Pose: {pose}, {spot}. Light: {light}"


def _genders(rng: random.Random, size: int) -> list[Gender]:
    """Минимум двое каждого пола, остальное случайно."""

    females = rng.randint(2, size - 2)
    genders = [Gender.FEMALE] * females + [Gender.MALE] * (size - females)
    rng.shuffle(genders)
    return genders


def build_team(rng: random.Random, scale: CompanyScale) -> list[PersonSkeleton]:
    low, high = SCALES[scale].team_on_site
    size = rng.randint(low, high)
    roles = [TeamRole.CEO, TeamRole.DEPARTMENT_HEAD, TeamRole.DEPARTMENT_HEAD]
    roles += [TeamRole.SPECIALIST] * (size - len(roles))

    head_departments = rng.sample(DEPARTMENTS, 2)
    used_names: set[str] = set()
    used_last: set[str] = set()
    pools = _Pools(rng)
    team: list[PersonSkeleton] = []

    for index, (role, gender) in enumerate(zip(roles, _genders(rng, size), strict=True)):
        origin = _pick_origin(rng)
        first_names = origin.female if gender is Gender.FEMALE else origin.male

        while True:
            first = _choice(rng, first_names)
            last = _choice(rng, origin.last_names)
            # Фамилии не должны совпадать и по корню (Becker / Becker-Smirnow).
            if first not in used_names and not any(
                last in other or other in last for other in used_last
            ):
                break
            origin = _pick_origin(rng)
            first_names = origin.female if gender is Gender.FEMALE else origin.male

        used_names.add(first)
        used_last.add(last)

        if role is TeamRole.DEPARTMENT_HEAD:
            department = head_departments[index - 1]
        elif role is TeamRole.SPECIALIST:
            department = _choice(rng, DEPARTMENTS)
        else:
            department = None

        team.append(
            PersonSkeleton(
                id=slugify(f"{first} {last}"),
                first_name=first,
                last_name=last,
                gender=gender,
                age=rng.randint(*AGE_RANGES[role]),
                role=role,
                department=department,
                heritage=origin.heritage,
                appearance=random_appearance(rng, gender, pools),
            )
        )

    return team


def build_facts(params: GenerationParams, rng: random.Random) -> CompanyFacts:
    country = COUNTRIES[params.country]
    direction = (
        custom_direction(params.custom_direction)
        if params.custom_direction
        else DIRECTIONS[params.direction]
    )
    service_type = (
        custom_service_type(params.custom_service)
        if params.custom_service
        else direction.service_type(params.service_type)
    )
    scale = SCALES[params.scale]

    city = _choice(rng, country.cities)
    street = _choice(rng, city.streets)
    house = str(rng.randint(1, 140))
    if rng.random() < 0.15:  # noqa: PLR2004
        house += _choice(rng, ("a", "b", "c"))

    suffix = rng.randint(city.phone_block.first, city.phone_block.last)
    subscriber = city.phone_block.number(suffix)
    phone = f"+{country.phone_country_code}{city.phone_block.area_code}{subscriber}"
    phone_display = (
        f"+{country.phone_country_code} {city.phone_block.area_code} "
        f"{city.phone_block.prefix} {suffix:03d}"
    )

    current_year = current_datetime().year
    founded_low, founded_high = scale.founded_years
    founded_year = rng.randint(founded_low, min(founded_high, current_year - 2))

    return CompanyFacts(
        params=params,
        country=country,
        direction=direction,
        service_type=service_type,
        city=city,
        legal_form=_choice(rng, country.legal_forms[params.scale]),
        address=Address(
            street=street.name,
            house_number=house,
            postal_code=street.postal_code,
            city=city.name,
            district=street.district,
            state=city.state,
            country_code=country.code,
        ),
        phone=phone,
        phone_display=phone_display,
        email_prefix=_choice(rng, EMAIL_PREFIXES),
        office_hours=_choice(rng, OFFICE_HOURS),
        founded_year=founded_year,
        current_year=current_year,
        employees=rng.randint(*scale.employees),
        team=build_team(rng, params.scale),
        photo_setting=_choice(rng, OFFICES),
        seeds={
            "основание": _choice(rng, FOUNDING_ARCHETYPES),
            "отраслевой фокус": _choice(rng, SECTOR_FOCUS),
            "отличие": _choice(rng, DIFFERENTIATORS),
            "формат поставки": _choice(rng, DELIVERY_FORMATS),
            "модель оплаты": _choice(rng, PRICING_MODELS),
        },
    )
