import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> object:
    """
    Достаёт JSON из ответа модели: снимает ```json-обёртку и лишний текст вокруг
    объекта. Бросает `ValueError`, если JSON не найден.
    """

    cleaned = text.strip()
    if match := _FENCE_RE.match(cleaned):
        cleaned = match.group(1)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("В ответе модели нет JSON-объекта")

    try:
        return json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as error:
        raise ValueError(f"Некорректный JSON: {error.msg} (позиция {error.pos})") from None
