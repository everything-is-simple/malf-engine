"""S3 验证：数据结构能承载 fixture 的输入与预期字段。

这不是引擎逻辑测试（引擎还没写）。它验证的是：PriceBar / Pivot / CoreStateSnapshot
的字段形状，能无损装下 golden fixture 里的 input_bars、expected_pivots、expected_snapshots。
若装不下（少字段、类型不符），说明 S3 结构定义有洞，早暴露。
"""

from __future__ import annotations

import json
from pathlib import Path

from malf.fingerprint import runtime_fingerprint
from malf.types import (
    CoreStateSnapshot,
    Direction,
    Pivot,
    PivotType,
    PriceBar,
    SystemState,
    WaveCoreState,
)

FIXTURE = Path(__file__).parent / "fixtures" / "uninitialized_to_up_alive.json"


def _load():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def test_pricebar_carries_all_input_bars():
    d = _load()
    bars = [
        PriceBar(
            symbol="TEST", timeframe="day", bar_dt=b["bar_dt"],
            open=b["open"], high=b["high"], low=b["low"], close=b["close"],
        )
        for b in d["input_bars"]
    ]
    assert len(bars) == 12
    assert all(isinstance(b.high, int) for b in bars)  # int_fixed
    assert bars[9].high == 114  # d09 H2 极值


def test_pivot_carries_double_timestamps():
    d = _load()
    pivots = [
        Pivot(
            pivot_type=PivotType(p["pivot_type"]),
            price=p["price"],
            extreme_bar_dt=p["extreme_bar_dt"],
            confirm_bar_dt=p["confirm_bar_dt"],
        )
        for p in d["expected_pivots"]
    ]
    h0, l1, h2 = pivots
    assert (h0.extreme_bar_dt, h0.confirm_bar_dt) == ("d02", "d04")
    assert (l1.extreme_bar_dt, l1.confirm_bar_dt) == ("d05", "d07")
    assert (h2.extreme_bar_dt, h2.confirm_bar_dt) == ("d09", "d11")


def test_snapshot_carries_core_assertion():
    """最后一根 d11 的 up_alive 快照能被结构无损承载。"""
    d = _load()
    last = d["expected_snapshots"][-1]
    snap = CoreStateSnapshot(
        symbol="TEST", timeframe="day", bar_dt=last["bar_dt"],
        system_state=SystemState(last["system_state"]),
        direction=Direction(last["direction"]),
        wave_core_state=WaveCoreState(last["wave_core_state"]),
        current_effective_guard_price=last["current_effective_guard_price"],
        current_effective_guard_extreme_bar_dt=last["current_effective_guard_extreme_bar_dt"],
        current_effective_guard_confirm_bar_dt=last["current_effective_guard_confirm_bar_dt"],
        progress_extreme_price=last["progress_extreme_price"],
        progress_extreme_bar_dt=last["progress_extreme_bar_dt"],
        runtime_fingerprint=runtime_fingerprint(),
    )
    assert snap.system_state is SystemState.UP_ALIVE
    assert snap.direction is Direction.UP
    assert snap.current_effective_guard_price == 96  # L1 = first guard
    assert snap.progress_extreme_price == 114  # H2


def test_uninitialized_snapshot_has_null_wave_fields():
    """uninitialized 期间 wave 字段应为 None。"""
    d = _load()
    first = d["expected_snapshots"][0]
    snap = CoreStateSnapshot(
        symbol="TEST", timeframe="day", bar_dt=first["bar_dt"],
        system_state=SystemState(first["system_state"]),
    )
    assert snap.system_state is SystemState.UNINITIALIZED
    assert snap.direction is None
    assert snap.current_effective_guard_price is None


def test_runtime_fingerprint_shape():
    fp = runtime_fingerprint()
    assert fp.startswith("py3.")
    assert fp.count("|") == 2  # py版本|平台|实现
