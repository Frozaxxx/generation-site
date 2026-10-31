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
        last_names=("Petrow", "Iwanow", "Smirnow", "Wolkow", "Sokolow", "Morosow"),
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
            "straight blonde hair tied back in a ponytail",
            "short auburn bob",
            "long wavy light-brown hair",
            "dark hair in a loose low bun",
            "chin-length ash-blonde hair",
            "curly black hair",
            "short pixie cut, greying at the temples",
            "red hair, shoulder length",
        ),
        Gender.MALE: (
            "short dark-blond hair",
            "close-cropped brown hair",
            "receding hairline, short grey-brown hair",
            "wavy dark hair, slightly messy",
            "short black hair with a side part",
            "shaved head",
            "medium-length light-brown hair combed back",
            "thick grey hair",
            "curly brown hair",
        ),
    },
    facial_hair=(
        "clean-shaven",
        "clean-shaven",
        "short stubble",
        "neatly trimmed beard",
        "full beard",
    ),
    clothing={
        Gender.FEMALE: (
            "a navy blazer over a plain white T-shirt",
            "a mustard-yellow knit sweater",
            "a light-blue denim shirt",
            "a black turtleneck",
            "a camel coat-style blazer and a thin silver necklace",
            "a dark-green silk blouse",
            "a striped Breton top under an open grey cardigan",
            "a burgundy wrap dress",
            "a white linen shirt with rolled sleeves",
        ),
        Gender.MALE: (
            "a navy blazer over an open-collar white shirt, no tie",
            "a dark-green quarter-zip pullover",
            "a light-blue oxford shirt with sleeves rolled up",
            "a charcoal suit, white shirt and a dark knitted tie",
            "a black crew-neck T-shirt under a casual grey jacket",
            "a checked flannel shirt",
            "a burgundy V-neck sweater over a white T-shirt",
            "a denim shirt",
            "a beige chore jacket over a black T-shirt",
        ),
    },
    expression=(
        "a slight natural smile",
        "a relaxed, friendly expression",
        "a calm, attentive look",
        "a warm wide smile",
        "a neutral, confident expression",
        "caught mid-laugh",
        "a thoughtful half-smile",
    ),
    accessories=(
        "",
        "",
        "",
        "",
        "thin metal-frame glasses",
        "dark acetate glasses",
        "a wristwatch",
    ),
)

# Поза и кадр - у каждого свои, иначе портреты выглядят как один шаблон.
POSES: tuple[str, ...] = (
    "head-and-shoulders, body turned slightly to the left, looking into the camera",
    "waist-up, arms loosely crossed, standing",
    "seated at a desk with a laptop, three-quarter view, looking up at the camera",
    "standing by a window, looking slightly past the camera",
    "leaning against a wall, hands in pockets, half-body shot",
    "head-and-shoulders, head tilted a little, close crop",
    "seated in a meeting room chair, leaning forward slightly, elbows on the table",
    "standing in a corridor, walking pose captured mid-step, glancing at the camera",
    "waist-up, holding a coffee mug, turned to the right",
)

# Свет и мелкие особенности кадра, чтобы фото не выглядели как одна серия рендеров.
LIGHTING: tuple[str, ...] = (
    "soft overcast daylight from a window on the left",
    "warm late-afternoon light with gentle shadows",
    "mixed office lighting, slightly cool colour cast",
    "bright daylight, a little overexposed highlights on the window side",
    "diffuse light, low contrast",
)

# Офис компании: общий для всей команды, но каждый снят в своём месте.
OFFICES: tuple[str, ...] = (
    "a converted brick warehouse office with tall windows and wooden floors",
    "a bright open-plan office with white walls, plants and glass meeting rooms",
    "an old-building (Altbau) office with high ceilings, stucco and herringbone parquet",
    "a modern office in a high-rise with a view over the city",
    "a small co-working space with concrete walls, shelves and warm lamps",
    "a quiet office with light oak furniture, bookshelves and large monitors",
)

OFFICE_SPOTS: tuple[str, ...] = (
    "next to the window",
    "in front of a bookshelf",
    "in the kitchen area",
    "at their desk",
    "in a glass meeting room",
    "by a whiteboard with blurred notes",
    "in the hallway",
    "near a large plant",
)
