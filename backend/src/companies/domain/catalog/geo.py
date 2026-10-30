from dataclasses import dataclass

from ..enums import CompanyScale


@dataclass(frozen=True, slots=True)
class Street:
    name: str
    postal_code: str
    district: str


@dataclass(frozen=True, slots=True)
class PhoneBlock:
    """Блок номеров, зарезервированный регулятором для медиапроизводств.

    Номера настоящие по формату, но не выдаются абонентам, поэтому сгенерированный
    телефон совпадает с кодом города и при этом никому не принадлежит.
    """

    area_code: str
    prefix: str
    first: int = 0
    last: int = 999

    def number(self, suffix: int) -> str:
        if not self.first <= suffix <= self.last:
            raise ValueError(f"Suffix {suffix} is outside of reserved block")
        return f"{self.prefix}{suffix:03d}"


@dataclass(frozen=True, slots=True)
class City:
    key: str
    name: str
    name_ru: str
    state: str
    phone_block: PhoneBlock
    postal_prefixes: tuple[str, ...]
    streets: tuple[Street, ...]


@dataclass(frozen=True, slots=True)
class Country:
    code: str
    name_ru: str
    name_de: str
    phone_country_code: str
    domain_zone: str
    legal_forms: dict[CompanyScale, tuple[str, ...]]
    cities: tuple[City, ...]

    def city(self, key: str) -> City:
        for city in self.cities:
            if city.key == key:
                return city
        raise KeyError(key)


# Источник блоков: Bundesnetzagentur, «Rufnummern für Medienproduktionen (Drama Numbers)».
GERMANY = Country(
    code="DE",
    name_ru="Германия",
    name_de="Deutschland",
    phone_country_code="49",
    domain_zone="de",
    legal_forms={
        CompanyScale.SMALL: ("GmbH", "UG (haftungsbeschränkt)"),
        CompanyScale.MEDIUM: ("GmbH", "AG"),
    },
    cities=(
        City(
            key="berlin",
            name="Berlin",
            name_ru="Берлин",
            state="Berlin",
            phone_block=PhoneBlock(area_code="30", prefix="23125"),
            postal_prefixes=("10", "12", "13", "14"),
            streets=(
                Street("Friedrichstraße", "10117", "Mitte"),
                Street("Invalidenstraße", "10115", "Mitte"),
                Street("Torstraße", "10119", "Mitte"),
                Street("Schlesische Straße", "10997", "Kreuzberg"),
                Street("Kurfürstendamm", "10719", "Charlottenburg"),
            ),
        ),
        City(
            key="frankfurt",
            name="Frankfurt am Main",
            name_ru="Франкфурт-на-Майне",
            state="Hessen",
            phone_block=PhoneBlock(area_code="69", prefix="90009"),
            postal_prefixes=("60", "65"),
            streets=(
                Street("Mainzer Landstraße", "60329", "Gallus"),
                Street("Bockenheimer Landstraße", "60323", "Westend"),
                Street("Neue Mainzer Straße", "60311", "Innenstadt"),
                Street("Hanauer Landstraße", "60314", "Ostend"),
                Street("Taunusanlage", "60325", "Westend"),
            ),
        ),
        City(
            key="hamburg",
            name="Hamburg",
            name_ru="Гамбург",
            state="Hamburg",
            phone_block=PhoneBlock(area_code="40", prefix="66969"),
            postal_prefixes=("20", "21", "22"),
            streets=(
                Street("Am Sandtorkai", "20457", "HafenCity"),
                Street("Ballindamm", "20095", "Altstadt"),
                Street("Neuer Wall", "20354", "Neustadt"),
                Street("Große Elbstraße", "22767", "Altona"),
                Street("Stresemannstraße", "22769", "Altona"),
            ),
        ),
        City(
            key="koeln",
            name="Köln",
            name_ru="Кёльн",
            state="Nordrhein-Westfalen",
            phone_block=PhoneBlock(area_code="221", prefix="4710"),
            postal_prefixes=("50", "51"),
            streets=(
                Street("Im Mediapark", "50670", "Neustadt-Nord"),
                Street("Hohenzollernring", "50672", "Neustadt-Nord"),
                Street("Habsburgerring", "50674", "Neustadt-Süd"),
                Street("Agrippinawerft", "50678", "Rheinauhafen"),
                Street("Deutz-Mülheimer Straße", "50679", "Deutz"),
            ),
        ),
        City(
            key="muenchen",
            name="München",
            name_ru="Мюнхен",
            state="Bayern",
            phone_block=PhoneBlock(area_code="89", prefix="99998"),
            postal_prefixes=("80", "81"),
            streets=(
                Street("Leopoldstraße", "80802", "Schwabing"),
                Street("Arnulfstraße", "80335", "Maxvorstadt"),
                Street("Sonnenstraße", "80331", "Altstadt"),
                Street("Rosenheimer Straße", "81669", "Au-Haidhausen"),
                Street("Maximilianstraße", "80539", "Altstadt-Lehel"),
            ),
        ),
    ),
)

COUNTRIES: dict[str, Country] = {GERMANY.code: GERMANY}
