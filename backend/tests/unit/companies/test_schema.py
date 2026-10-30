import json

import pytest
from pydantic import ValidationError

from src.cli.__main__ import SCHEMA_FILE
from src.companies.domain.serialization import (
    profile_from_dict,
    profile_json_schema,
    profile_to_dict,
)
from tests.support.factories import profile_data


def test_profile_roundtrip():
    data = profile_data()

    assert profile_to_dict(profile_from_dict(data)) == {
        "schema_version": 1,
        "content_language": "ru",
        **data,
    }


def test_schema_rejects_bad_phone_format():
    data = profile_data()
    data["contacts"]["phone"] = "069 90009 417"

    with pytest.raises(ValidationError):
        profile_from_dict(data)


def test_committed_schema_is_up_to_date():
    """docs/company.schema.json обновляется командой `python -m src.cli export-schema`."""

    assert json.loads(SCHEMA_FILE.read_text(encoding="utf-8")) == profile_json_schema()
