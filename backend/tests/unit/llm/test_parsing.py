import pytest

from src.llm.infra.parsing import extract_json


@pytest.mark.parametrize(
    "text",
    [
        '{"a": 1}',
        '```json\n{"a": 1}\n```',
        'Вот ответ:\n{"a": 1}\nНадеюсь, помог.',
    ],
)
def test_extract_json(text: str):
    assert extract_json(text) == {"a": 1}


def test_extract_json_without_object():
    with pytest.raises(ValueError, match="нет JSON"):
        extract_json("просто текст")
