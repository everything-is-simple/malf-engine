"""Tests for C-07 rule: Early pivot replacement during initialization.

Tests cover 4 scenarios:
- C07-1: L0 replacement (DOWN direction)
- C07-2: H0 replacement (UP direction)
- C07-3: L1 replacement (UP direction)
- C07-4: H1 replacement (DOWN direction)
"""

import json
from pathlib import Path

import pytest

from src.malf.core_engine import MALFCoreEngine
from src.malf.types import PriceBar, SystemState


def _load_fixture(name: str) -> dict:
    """Load a C07 test fixture by name."""
    fixture_path = Path(__file__).parent / "fixtures" / "c07" / f"{name}.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def _run_fixture_test(fixture_name: str) -> None:
    """Run a C07 fixture test and validate the expected snapshot."""
    fixture = _load_fixture(fixture_name)

    # Create engine with fixture k
    k = fixture.get("pivot_detection_k", 2)
    engine = MALFCoreEngine(k=k)

    # Process all bars
    snapshots = {}
    for bar_data in fixture["bars"]:
        bar = PriceBar(
            symbol=fixture["symbol"],
            timeframe=fixture["timeframe"],
            bar_dt=bar_data["bar_dt"],
            open=bar_data["open"],
            high=bar_data["high"],
            low=bar_data["low"],
            close=bar_data["close"],
        )
        snapshot = engine.on_bar(bar)
        snapshots[bar_data["bar_dt"]] = snapshot

    # Validate expected snapshots
    for bar_dt, expected in fixture["expected_snapshots"].items():
        snapshot = snapshots[bar_dt]

        assert snapshot.system_state.value == expected["system_state"], (
            f"[{bar_dt}] system_state mismatch"
        )

        if "direction" in expected:
            assert snapshot.direction is not None
            assert snapshot.direction.value == expected["direction"], (
                f"[{bar_dt}] direction mismatch"
            )

        if "current_effective_guard_price" in expected:
            assert snapshot.current_effective_guard_price == expected["current_effective_guard_price"], (
                f"[{bar_dt}] guard_price mismatch"
            )

        if "current_effective_guard_extreme_bar_dt" in expected:
            assert snapshot.current_effective_guard_extreme_bar_dt == expected["current_effective_guard_extreme_bar_dt"], (
                f"[{bar_dt}] guard_extreme_bar_dt mismatch"
            )

        if "current_effective_guard_confirm_bar_dt" in expected:
            assert snapshot.current_effective_guard_confirm_bar_dt == expected["current_effective_guard_confirm_bar_dt"], (
                f"[{bar_dt}] guard_confirm_bar_dt mismatch"
            )

        if "progress_extreme_price" in expected:
            assert snapshot.progress_extreme_price == expected["progress_extreme_price"], (
                f"[{bar_dt}] progress_extreme_price mismatch"
            )

        if "progress_extreme_bar_dt" in expected:
            assert snapshot.progress_extreme_bar_dt == expected["progress_extreme_bar_dt"], (
                f"[{bar_dt}] progress_extreme_bar_dt mismatch"
            )

        if "bar_count" in expected:
            assert snapshot.bar_count == expected["bar_count"], (
                f"[{bar_dt}] bar_count mismatch"
            )


def test_c07_1_l0_replacement():
    """C07-1: L0 replacement in DOWN direction.

    L0_old @ 10000 is replaced by L0_new @ 9000 (lower).
    Final initialization uses L0_new as reference.
    """
    _run_fixture_test("C07_1_L0_replacement")


def test_c07_2_h0_replacement():
    """C07-2: H0 replacement in UP direction.

    H0_old @ 15000 is replaced by H0_new @ 18000 (higher).
    Final initialization uses H0_new as reference.
    """
    _run_fixture_test("C07_2_H0_replacement")


def test_c07_3_l1_replacement():
    """C07-3: L1 replacement in UP direction.

    L1_old @ 9000 is replaced by L1_new @ 7000 (lower).
    L1_new becomes the guard (lowest L).
    """
    _run_fixture_test("C07_3_L1_replacement")


def test_c07_4_h1_replacement():
    """C07-4: H1 replacement in DOWN direction.

    H1_old @ 17000 is replaced by H1_new @ 20000 (higher).
    H1_new becomes the guard (highest H).
    """
    _run_fixture_test("C07_4_H1_replacement")
