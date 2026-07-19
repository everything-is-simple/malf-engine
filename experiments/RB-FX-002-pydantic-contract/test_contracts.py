import pytest
from pydantic import ValidationError

from contracts import CoordinateField, PublishedSnapshot

VALID = {
    "schema_version": "riskbench-snapshot-v0.1",
    "evaluation_date": "2026-07-19",
    "usage_level": "research_only",
    "price_line": "raw_none",
    "lineage": {
        "run_id": "run-001",
        "snapshot_id": "snapshot-001",
        "source_sha256": "a" * 64,
        "parser_version": "tdx-day-v0.1",
        "malf_rule_version": "malf-v2.0",
        "adapter_version": "malf-v2.0-etf-tick-v0.1",
    },
    "core": {"value": "confirmed", "reason_codes": []},
    "range": {"value": None, "reason_codes": ["range_not_implemented"]},
}


def test_valid_snapshot_is_frozen_and_serializable():
    snapshot = PublishedSnapshot.model_validate(VALID)
    assert snapshot.usage_level == "research_only"
    assert '"range"' in snapshot.model_dump_json()
    with pytest.raises(ValidationError):
        snapshot.usage_level = "verification_only"


def test_missing_lineage_rejected():
    payload = dict(VALID)
    payload.pop("lineage")
    with pytest.raises(ValidationError):
        PublishedSnapshot.model_validate(payload)


def test_extra_field_rejected():
    payload = dict(VALID)
    payload["trade_signal"] = "buy"
    with pytest.raises(ValidationError):
        PublishedSnapshot.model_validate(payload)


def test_none_requires_machine_reason_code():
    with pytest.raises(ValidationError):
        CoordinateField(value=None)


def test_neutral_is_not_inserted_for_unknown():
    field = CoordinateField(value=None, reason_codes=("insufficient_history",))
    assert field.value is None
    assert "neutral" not in field.model_dump_json()
