"""V3/V4/V5 validation contracts for the MALF v2.1 engine.

These tests are intentionally small and deterministic: they pin the
authoritative parameters, formula directions, and immutable bar indexing
without using real-market data as a semantic oracle.
"""

import pytest

from malf.core_engine import MALFCoreEngine
from malf.lifespan_engine import LifespanEngine
from malf.rank_engine import RankEngine
from malf.types import Direction, PriceBar, RangeResolutionType


def test_v3_authority_parameters_are_explicit():
    """V2.1 fixes pivot k=2 and rank minimum N=30."""
    assert MALFCoreEngine().k == 2
    assert RankEngine.MIN_SAMPLE_SIZE == 30


def test_v4_wave_progress_formula_is_directional():
    engine = LifespanEngine()

    up = engine.calculate_wave_lifespan(
        wave_id="W_UP",
        symbol="TEST",
        timeframe="D1",
        direction=Direction.UP,
        wave_start_bar_dt="2024-01-01",
        wave_start_price=100,
        wave_end_bar_dt="2024-01-10",
        wave_end_price=130,
        span_bars=9,
        primitive_count=3,
        pivot_count=4,
        new_count=2,
        no_new_span=1,
        first_pivot_price=100,
        guard_price=90,
    )
    down = engine.calculate_wave_lifespan(
        wave_id="W_DOWN",
        symbol="TEST",
        timeframe="D1",
        direction=Direction.DOWN,
        wave_start_bar_dt="2024-02-01",
        wave_start_price=120,
        wave_end_bar_dt="2024-02-10",
        wave_end_price=80,
        span_bars=9,
        primitive_count=3,
        pivot_count=4,
        new_count=2,
        no_new_span=1,
        first_pivot_price=120,
        guard_price=100,
    )

    assert up.progress_pct == pytest.approx((130 - 100) / (130 - 90))
    assert down.progress_pct == pytest.approx((120 - 80) / (100 - 80))


def test_v4_range_resolution_distance_uses_evolved_boundary():
    engine = LifespanEngine()

    up = engine.calculate_range_lifespan(
        range_id="R_UP",
        symbol="TEST",
        timeframe="D1",
        range_type=RangeResolutionType.CONTINUATION,
        range_start_bar_dt="2024-01-01",
        range_end_bar_dt="2024-01-10",
        span_bars=9,
        evolution_count=2,
        replacement_count=1,
        resolution_distance=6,
        boundary_high_init=110,
        boundary_low_init=90,
        boundary_high_now=120,
        boundary_low_now=85,
        breakout_direction="up",
        confirmation_pivot_extreme_price=126,
    )
    down = engine.calculate_range_lifespan(
        range_id="R_DOWN",
        symbol="TEST",
        timeframe="D1",
        range_type=RangeResolutionType.REVERSAL,
        range_start_bar_dt="2024-02-01",
        range_end_bar_dt="2024-02-10",
        span_bars=9,
        evolution_count=2,
        replacement_count=1,
        resolution_distance=-4,
        boundary_high_init=110,
        boundary_low_init=90,
        boundary_high_now=115,
        boundary_low_now=80,
        breakout_direction="down",
        confirmation_pivot_extreme_price=76,
    )

    assert up.resolution_distance_pct == pytest.approx((126 - 120) / 120)
    assert down.resolution_distance_pct == pytest.approx((80 - 76) / 80)


def test_v5_bar_index_is_zero_based_and_monotonic():
    engine = MALFCoreEngine(k=2)
    bars = [
        PriceBar("TEST", "D1", f"2024-03-{i:02d}", 100 + i, 101 + i, 99 + i, 100 + i)
        for i in range(1, 7)
    ]

    snapshots = [engine.on_bar(bar) for bar in bars]

    assert [snapshot.bar_index for snapshot in snapshots] == list(range(len(bars)))
