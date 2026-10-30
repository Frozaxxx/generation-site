from dataclasses import dataclass

from ..enums import CompanyScale


@dataclass(frozen=True, slots=True)
class ServiceType:
    key: str
    name_ru: str
    description: str
    typical_clients: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Direction:
    key: str
    name_ru: str
    description: str
    service_types: tuple[ServiceType, ...]

    def service_type(self, key: str) -> ServiceType:
        for service_type in self.service_types:
            if service_type.key == key:
                return service_type
        raise KeyError(key)


@dataclass(frozen=True, slots=True)
class ScaleProfile:
    """Параметры масштаба: сколько людей, с какого года, сколько человек на сайте."""

    scale: CompanyScale
    name_ru: str
    employees: tuple[int, int]
    founded_years: tuple[int, int]
    team_on_site: tuple[int, int]


AI_INVESTMENT_RESEARCH = Direction(
    key="ai_investment_research",
    name_ru="ИИ для инвестиционных исследований и анализа данных",
    description=(
        "B2B-сервисы, которые с помощью машинного обучения и языковых моделей ускоряют "
        "работу аналитиков: сбор и разметку данных, анализ отчётности, мониторинг рисков."
    ),
    service_types=(
        ServiceType(
            key="earnings_analysis",
            name_ru="Анализ отчётности и звонков с инвесторами",
            description=(
                "Разбор квартальных отчётов и стенограмм earnings calls, сравнение с консенсусом."
            ),
            typical_clients=("фонды акций", "sell-side аналитики", "семейные офисы"),
        ),
        ServiceType(
            key="alternative_data",
            name_ru="Альтернативные данные",
            description="Сбор и нормализация сигналов из вакансий, цен, веб-трафика и логистики.",
            typical_clients=("хедж-фонды", "квантовые команды", "управляющие активами"),
        ),
        ServiceType(
            key="esg_screening",
            name_ru="ESG-скрининг и анализ раскрытий",
            description="Проверка нефинансовой отчётности по SFDR и CSRD, поиск расхождений.",
            typical_clients=("управляющие компании", "пенсионные фонды", "банки"),
        ),
        ServiceType(
            key="due_diligence",
            name_ru="Ускоренный due diligence",
            description="Подготовка обзора целевой компании для сделок private equity и M&A.",
            typical_clients=("фонды private equity", "M&A-консультанты", "корпоративные венчуры"),
        ),
        ServiceType(
            key="portfolio_risk",
            name_ru="Мониторинг рисков портфеля",
            description="Отслеживание новостей, судебных дел и событий по эмитентам портфеля.",
            typical_clients=("управляющие активами", "страховые компании", "казначейства"),
        ),
        ServiceType(
            key="credit_research",
            name_ru="Кредитный анализ эмитентов",
            description="Модели кредитного качества и разбор проспектов облигаций.",
            typical_clients=(
                "фонды облигаций",
                "кредитные аналитики банков",
                "страховые компании",
            ),
        ),
        ServiceType(
            key="data_engineering",
            name_ru="Подготовка финансовых данных",
            description=(
                "Очистка, сопоставление идентификаторов и поставка рыночных данных в хранилища."
            ),
            typical_clients=("квантовые команды", "дата-отделы банков", "финтех-компании"),
        ),
    ),
)

DIRECTIONS: dict[str, Direction] = {AI_INVESTMENT_RESEARCH.key: AI_INVESTMENT_RESEARCH}

SCALES: dict[CompanyScale, ScaleProfile] = {
    CompanyScale.SMALL: ScaleProfile(
        scale=CompanyScale.SMALL,
        name_ru="Небольшая компания",
        employees=(8, 30),
        founded_years=(2015, 2022),
        team_on_site=(5, 5),
    ),
    CompanyScale.MEDIUM: ScaleProfile(
        scale=CompanyScale.MEDIUM,
        name_ru="Средняя компания",
        employees=(50, 180),
        founded_years=(2008, 2017),
        team_on_site=(6, 7),
    ),
}
