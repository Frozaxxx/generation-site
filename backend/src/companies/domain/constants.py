FAQ_SIZE = 5
MIN_TEAM_SIZE = 5
DEPARTMENT_HEADS_COUNT = 2

MIN_BIO_LENGTH = 80
MAX_BIO_LENGTH = 1000

# Следы шаблонов, которые не должны остаться в готовых текстах.
PLACEHOLDER_PATTERNS: tuple[str, ...] = (
    r"\{\{.*?\}\}",
    r"\{[a-z_]+\}",
    r"\[(?:NAME|COMPANY|CITY|TODO|ИМЯ|КОМПАНИЯ|ГОРОД)\]",
    r"<[A-Z_]{3,}>",
    r"\bTODO\b",
    r"\bLorem ipsum\b",
)
