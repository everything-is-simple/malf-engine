"""Tests for the V2 validation-package generator."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from malf.types import PriceBar

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "verify" / "prepare_v2_validation.py"
SPEC = importlib.util.spec_from_file_location("prepare_v2_validation", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _fixture_bars() -> list[PriceBar]:
    fixture_path = Path(__file__).parent / "fixtures" / "uninitialized_to_up_alive.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [
        PriceBar(
            symbol="TEST",
            timeframe="D",
            bar_dt=item["bar_dt"],
            open=item["open"],
            high=item["high"],
            low=item["low"],
            close=item["close"],
        )
        for item in fixture["input_bars"]
    ]


def test_build_trace_exposes_initialization_and_pivot_context():
    bars = _fixture_bars()
    trace, pivots = MODULE.build_trace(bars, k=2)

    assert len(trace) == len(bars)
    assert [pivot.confirm_bar_dt for pivot in pivots] == ["d04", "d07", "d11"]

    initialization = next(row for row in trace if "initialization_up" in row["events"])
    initialization = dict(initialization, selection_category="initialization")
    case = MODULE.enrich_case(initialization, bars, pivots, k=2)

    assert case["event_bar"]["bar_dt"] == "d11"
    assert case["core_snapshot"]["current_effective_guard_price"] == 96
    assert case["core_snapshot"]["progress_extreme_price"] == 114
    roles = {audit["role"] for audit in case["pivot_audits"]}
    assert roles == {"confirmed_on_case_bar", "effective_guard", "progress_extreme"}
    assert all(audit["strict_fractal_check"] for audit in case["pivot_audits"])
    assert all(len(audit["ohlc_window"]) == 5 for audit in case["pivot_audits"])


def test_select_validation_cases_requires_acceptance_minimum():
    try:
        MODULE.select_validation_cases([], count=9)
    except ValueError as exc:
        assert "at least 10" in str(exc)
    else:
        raise AssertionError("count below the V2 acceptance threshold must fail")


def test_select_validation_cases_is_deterministic_and_unique():
    bars = _fixture_bars()
    trace, _ = MODULE.build_trace(bars, k=2)

    # Repeat a real trace with shifted indexes to exercise deterministic fill behavior.
    expanded = []
    for block in range(3):
        for row in trace:
            copied = dict(row)
            copied["bar_index"] = row["bar_index"] + block * len(trace)
            expanded.append(copied)

    first = MODULE.select_validation_cases(expanded, count=10)
    second = MODULE.select_validation_cases(expanded, count=10)
    first_indexes = [row["bar_index"] for row in first]
    second_indexes = [row["bar_index"] for row in second]

    assert first_indexes == second_indexes
    assert len(first_indexes) == 10
    assert len(set(first_indexes)) == 10
