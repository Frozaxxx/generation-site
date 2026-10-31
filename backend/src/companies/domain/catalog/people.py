"""
Имена и внешность для команды. Имена выбирает код, а не модель: модели склонны
повторять одни и те же «Лена Хартманн», а нам нужны разные и правдоподобные люди.
"""

from dataclasses import dataclass

from ..enums import Gender


@dataclass(frozen=True, slots=True)
class NameOrigin:
    key: str
    weight: int
    heritage: str  # подсказка для фото
    female: tuple[str, ...]
    male: tuple[str, ...]
    last_names: tuple[str, ...]


NAME_ORIGINS: tuple[NameOrigin, ...] = (
    NameOrigin(
        key="german",
        weight=70,
        heritage="Central European",
        female=(
            "Anna",
            "Lena",
            "Miriam",
            "Katharina",
            "Julia",
            "Sophie",
            "Laura",
            "Clara",
            "Johanna",
            "Franziska",
            "Sabine",
            "Petra",
            "Nina",
            "Theresa",
            "Hannah",
            "Marie",
            "Carolin",
            "Vanessa",
            "Annika",
            "Friederike",
            "Stefanie",
            "Ines",
            "Judith",
        ),
        male=(
            "Jonas",
            "Lukas",
            "Felix",
            "Maximilian",
            "Tobias",
            "Florian",
            "Daniel",
            "Markus",
            "Stefan",
            "Thomas",
            "Andreas",
            "Jan",
            "Niklas",
            "Philipp",
            "Christoph",
            "Sebastian",
            "Moritz",
            "Henrik",
            "Oliver",
            "Benedikt",
            "Matthias",
            "Jens",
            "Kai",
        ),
        last_names=(
            "Müller",
            "Schmidt",
            "Schneider",
            "Fischer",
            "Weber",
            "Meyer",
            "Wagner",
            "Becker",
            "Schulz",
            "Hoffmann",
            "Koch",
            "Richter",
            "Klein",
            "Wolf",
            "Schröder",
            "Neumann",
            "Schwarz",
            "Zimmermann",
            "Braun",
            "Krüger",
            "Hartmann",
            "Lange",
            "Werner",
            "Krause",
            "Lehmann",
            "Köhler",
            "Brandt",
            "Vogel",
            "Engel",
            "Kaiser",
            "Fuchs",
            "Berger",
            "Peters",
            "Seidel",
            "Ziegler",
            "Haas",
            "Graf",
            "Dietrich",
            "Roth",
            "Albrecht",
            "Sommer",
            "Winkler",
            "Lorenz",
            "Baumann",
            "Franke",
            "Simon",
        ),
    ),
    NameOrigin(
        key="turkish",
        weight=8,
        heritage="Turkish-German",
        female=("Elif", "Aylin", "Selin", "Deniz", "Melis", "Zeynep", "Derya"),
        male=("Mehmet", "Emre", "Can", "Murat", "Kerem", "Baris", "Okan"),
        last_names=("Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Arslan", "Aydın", "Öztürk"),
    ),
    NameOrigin(
        key="polish",
        weight=8,
        heritage="Polish-German",
        female=("Agnieszka", "Natalia", "Joanna", "Magdalena", "Karolina"),
        male=("Piotr", "Tomasz", "Marek", "Paweł", "Krzysztof"),
        last_names=("Nowak", "Kowalski", "Wiśniewski", "Lewandowski", "Zieliński", "Wójcik"),
    ),
    NameOrigin(
        key="italian",
        weight=5,
        heritage="Italian-German",
        female=("Giulia", "Chiara", "Francesca", "Elena"),
        male=("Matteo", "Luca", "Marco", "Alessandro"),
        last_names=("Rossi", "Esposito", "Romano", "Ferrari", "Conti", "Greco"),
    ),
    NameOrigin(
        key="eastern",
        weight=5,
        heritage="Eastern European",
        female=("Olga", "Irina", "Daria", "Ekaterina"),
        male=("Dmitri", "Alexander", "Sergej", "Viktor"),
        last_names=("Petrow", "Iwanow", "Becker-Smirnow", "Wolkow", "Sokolow"),
    ),
    NameOrigin(
        key="greek",
        weight=4,
        heritage="Greek-German",
        female=("Eleni", "Sofia", "Katerina"),
        male=("Nikos", "Giorgos", "Dimitrios"),
        last_names=("Papadopoulos", "Georgiou", "Nikolaidis", "Konstantinou"),
    ),
)


@dataclass(frozen=True, slots=True)
class Appearance:
    hair: dict[Gender, tuple[str, ...]]
    facial_hair: tuple[str, ...]
    clothing: dict[Gender, tuple[str, ...]]
    expression: tuple[str, ...]
    accessories: tuple[str, ...]


APPEARANCE = Appearance(
    hair={
        Gender.FEMALE: (
            "shoulder-length dark brown hair",
            "straight blonde hair tied back",
            "short auburn bob",
            "long wavy light-brown hair",
            "dark hair in a low bun",
            "chin-length ash-blonde hair",
            "curly black hair",
        ),
        Gender.MALE: (
            "short dark-blond hair",
            "close-cropped brown hair",
            "receding hairline, short grey-brown hair",
            "wavy dark hair, slightly messy",
            "short black hair with a side part",
            "buzz cut",
            "medium-length light-brown hair combed back",
        ),
    },
    facial_hair=("clean-shaven", "clean-shaven", "short stubble", "neatly trimmed beard"),
    clothing={
        Gender.FEMALE: (
            "navy blazer over a plain white top",
            "grey fine-knit sweater",
            "light-blue button-down shirt",
            "black turtleneck",
            "camel blazer, simple silver necklace",
            "dark-green blouse",
        ),
        Gender.MALE: (
            "navy blazer over an open-collar white shirt, no tie",
            "grey merino sweater over a collared shirt",
            "light-blue oxford shirt, sleeves slightly rolled",
            "dark charcoal suit jacket, no tie",
            "black crew-neck sweater",
            "checked flannel shirt under a casual blazer",
        ),
    },
    expression=(
        "slight natural smile",
        "relaxed, friendly expression",
        "calm and attentive look",
        "warm smile with crow's feet",
        "neutral, confident expression",
    ),
    accessories=("", "", "", "thin metal-frame glasses", "dark acetate glasses"),
)


# Общий стиль съёмки на компанию: все портреты как будто из одной фотосессии.
PHOTO_SETTINGS: tuple[str, ...] = (
    "bright modern office with softly blurred plants and glass partitions in the background",
    "plain light-grey studio backdrop with soft gradient",
    "loft office with exposed brick, background strongly blurred",
    "meeting room by a large window, out-of-focus city view behind",
    "warm wooden interior with bookshelves, shallow depth of field",
    "white wall with soft daylight shadows",
)
