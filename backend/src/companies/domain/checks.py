"""
Проверки согласованности карточки компании.

Проверки детерминированные и бесплатные: их можно запускать при каждом сохранении.
Смысловые проверки текста (противоречия в описании продукта) добавляются отдельно
и возвращают те же `Issue`.
"""

from typing import Any

import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict, dataclass, fields, is_dataclass

from src.shared.utils.time import current_datetime

from .catalog import COUNTRIES, City, Country
from .constants import DEPARTMENT_HEADS_COUNT, FAQ_SIZE, MIN_TEAM_SIZE, PLACEHOLDER_PATTERNS
from .enums import IssueSeverity, TeamRole
from .profile import CompanyProfile

_PLACEHOLDER_RE = re.compile("|".join(PLACEHOLDER_PATTERNS), re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    severity: IssueSeverity
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def errors_only(issues: list[Issue]) -> list[Issue]:
    return [issue for issue in issues if issue.severity is IssueSeverity.ERROR]


def _error(code: str, path: str, message: str) -> Issue:
    return Issue(code=code, severity=IssueSeverity.ERROR, path=path, message=message)


def _warning(code: str, path: str, message: str) -> Issue:
    return Issue(code=code, severity=IssueSeverity.WARNING, path=path, message=message)


def iter_strings(value: Any, path: str = "") -> Iterator[tuple[str, str]]:
    """Обходит все строки вложенной структуры вместе с путём до них."""

    if isinstance(value, str):
        yield path, value
    elif is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            yield from iter_strings(getattr(value, item.name), f"{path}.{item.name}".lstrip("."))
    elif isinstance(value, list | tuple):
        for index, item in enumerate(value):
            yield from iter_strings(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(item, f"{path}.{key}".lstrip("."))


def check_texts(profile: CompanyProfile) -> list[Issue]:
    """Пустые строки и незаменённые переменные шаблонов."""

    issues: list[Issue] = []
    for path, text in iter_strings(profile):
        if path.endswith("photo.file"):
            continue
        if not text.strip():
            issues.append(_error("empty_field", path, "Пустое обязательное поле"))
        elif match := _PLACEHOLDER_RE.search(text):
            issues.append(
                _error("placeholder", path, f"Незаменённая переменная: {match.group(0)!r}")
            )
    return issues


def check_team(profile: CompanyProfile) -> list[Issue]:
    issues: list[Issue] = []
    team = profile.team

    if len(team) < MIN_TEAM_SIZE:
        issues.append(
            _error("team_size", "team", f"В команде должно быть не меньше {MIN_TEAM_SIZE} человек")
        )

    ceo_count = sum(person.role is TeamRole.CEO for person in team)
    if ceo_count != 1:
        issues.append(_error("team_ceo", "team", "В команде должен быть ровно один руководитель"))

    if len(profile.department_heads) < DEPARTMENT_HEADS_COUNT:
        issues.append(
            _error(
                "team_heads",
                "team",
                f"Нужно минимум {DEPARTMENT_HEADS_COUNT} руководителя отделов",
            )
        )

    for person_id, count in Counter(person.id for person in team).items():
        if count > 1:
            issues.append(_error("team_duplicate_id", "team", f"Повторяется id {person_id!r}"))

    for name, count in Counter(person.full_name for person in team).items():
        if count > 1:
            issues.append(_error("team_duplicate_name", "team", f"Повторяется имя {name!r}"))

    for index, person in enumerate(team):
        if person.role is TeamRole.DEPARTMENT_HEAD and not person.department:
            issues.append(
                _error(
                    "team_department",
                    f"team[{index}].department",
                    f"У руководителя отдела {person.full_name} не указан отдел",
                )
            )

    return issues


def check_faq(profile: CompanyProfile) -> list[Issue]:
    issues: list[Issue] = []
    if len(profile.faq) != FAQ_SIZE:
        issues.append(_error("faq_size", "faq", f"Нужно ровно {FAQ_SIZE} вопросов и ответов"))

    questions = Counter(item.question.strip().lower() for item in profile.faq)
    if any(count > 1 for count in questions.values()):
        issues.append(_error("faq_duplicate", "faq", "Вопросы FAQ повторяются"))
    return issues


def _city(country: Country, key: str) -> City | None:
    try:
        return country.city(key)
    except KeyError:
        return None


def check_contacts(profile: CompanyProfile, country: Country) -> list[Issue]:
    """Телефон, индекс и почта должны соответствовать стране, городу и домену."""

    issues: list[Issue] = []
    contacts = profile.contacts
    address = contacts.address

    if address.country_code != country.code:
        issues.append(
            _error("country", "contacts.address.country_code", "Страна адреса не совпадает")
        )

    city = _city(country, contacts.city_key)
    if city is None:
        issues.append(
            _error("city_unknown", "contacts.city_key", "Города нет в каталоге выбранной страны")
        )
        return issues

    if address.city != city.name:
        issues.append(
            _error("city_name", "contacts.address.city", f"Ожидался город {city.name!r}")
        )

    if not address.postal_code.startswith(city.postal_prefixes):
        issues.append(
            _error(
                "postal_code",
                "contacts.address.postal_code",
                f"Индекс {address.postal_code} не относится к городу {city.name}",
            )
        )

    country_prefix = f"+{country.phone_country_code}"
    city_prefix = f"{country_prefix}{city.phone_block.area_code}"
    if not contacts.phone.startswith(country_prefix):
        issues.append(_error("phone_country", "contacts.phone", "Код страны не совпадает"))
    elif not contacts.phone.startswith(city_prefix):
        issues.append(
            _error(
                "phone_city",
                "contacts.phone",
                f"Код города не совпадает: для {city.name} ожидается {city_prefix}",
            )
        )
    elif not contacts.phone.startswith(f"{city_prefix}{city.phone_block.prefix}"):
        issues.append(
            _warning(
                "phone_unreserved",
                "contacts.phone",
                "Номер вне блока для медиапроизводств: он может принадлежать реальному абоненту",
            )
        )

    if re.sub(r"\D", "", contacts.phone_display.replace("(0)", "")) not in contacts.phone:
        issues.append(
            _error("phone_display", "contacts.phone_display", "Запись телефона не совпадает")
        )

    email_domain = contacts.email.rsplit("@", maxsplit=1)[-1]
    if email_domain != profile.brand.domain:
        issues.append(
            _error("email_domain", "contacts.email", "Домен почты не совпадает с доменом сайта")
        )

    return issues


def check_brand(profile: CompanyProfile, country: Country) -> list[Issue]:
    issues: list[Issue] = []
    brand = profile.brand

    if brand.name.lower() not in brand.legal_name.lower():
        issues.append(
            _error("legal_name", "brand.legal_name", "Наименование юрлица не содержит бренд")
        )

    if not brand.legal_name.endswith(brand.legal_form):
        issues.append(
            _error(
                "legal_form", "brand.legal_name", "Наименование не заканчивается правовой формой"
            )
        )

    known_forms = {form for forms in country.legal_forms.values() for form in forms}
    if brand.legal_form not in known_forms:
        issues.append(
            _warning("legal_form_unknown", "brand.legal_form", "Правовая форма не из каталога")
        )

    if not brand.domain.endswith(f".{country.domain_zone}"):
        issues.append(
            _warning("domain_zone", "brand.domain", "Домен не в национальной зоне страны")
        )

    return issues


def check_history(profile: CompanyProfile) -> list[Issue]:
    issues: list[Issue] = []
    history = profile.history
    this_year = current_datetime().year

    if history.founded_year > this_year:
        issues.append(_error("founded_future", "history.founded_year", "Год основания в будущем"))

    years = [milestone.year for milestone in history.milestones]
    if years != sorted(years):
        issues.append(_warning("milestones_order", "history.milestones", "Этапы не по порядку"))

    for index, year in enumerate(years):
        if not history.founded_year <= year <= this_year:
            issues.append(
                _error(
                    "milestone_year",
                    f"history.milestones[{index}].year",
                    "Год этапа раньше основания или в будущем",
                )
            )

    if (ceo := profile.ceo) is not None and ceo.age - (this_year - history.founded_year) < 21:  # noqa: PLR2004
        issues.append(
            _warning(
                "ceo_age",
                "team",
                f"{ceo.full_name} был младше 21 года при основании компании",
            )
        )

    return issues


def check_profile(profile: CompanyProfile, country_code: str) -> list[Issue]:
    """Полный набор детерминированных проверок карточки."""

    country = COUNTRIES.get(country_code)
    if country is None:
        return [_error("country_unknown", "params.country", "Страна не поддерживается")]

    return [
        *check_texts(profile),
        *check_brand(profile, country),
        *check_contacts(profile, country),
        *check_history(profile),
        *check_team(profile),
        *check_faq(profile),
    ]
