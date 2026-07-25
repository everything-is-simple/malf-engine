"""第一刀 golden fixture 端到端测试：uninitialized → up_alive。

逐 bar 喂入，每根发布一个 CoreStateSnapshot，与 fixture 的 expected_snapshots 逐条全等比对。
这是第一次真正跑完整引擎逻辑的测试——串起 pivot_detection + initialization，
覆盖 spec §2 的 S1→S9 事件顺序、pivot k=2 延迟确认、first guard=L1、initial wave 创建。
"""

from __future__ import annotations

import json
from pathlib import Path

from malf.fingerprint import runtime_fingerprint
from malf.initialization import find_initial_wave
from malf.pivot_detection import detect_pivots
from malf.types import (
    CoreStateSnapshot,
    Direction,
    PriceBar,
    SystemState,
    WaveCoreState,
)

FIXTURE = Path(__file__).parent / "fixtures" / "uninitialized_to_up_alive.json"


def _load():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def _bars_from(input_bars):
    return [
        PriceBar(
            symbol="TEST",
            timeframe="day",
            bar_dt=b["bar_dt"],
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"],
        )
        for b in input_bars
    ]


def test_uninitialized_to_up_alive_end_to_end():
    """H0 → L1 → H2>H0，system_state 从 uninitialized 转 up_alive（golden fixture 端到端）。

    逐 bar 推进，每根产出一个 snapshot，与 fixture 的 expected_snapshots 全等比对。
    """
    d = _load()
    bars = _bars_from(d["input_bars"])
    k = d["params"]["k"]
    expected_snapshots = d["expected_snapshots"]

    # 一次性检测全部 pivot（实际引擎是逐 bar 累积，但第一刀简化：全喂完再检测）
    all_pivots = detect_pivots(bars, k=k)
    pivots_by_confirm_dt = {p.confirm_bar_dt: p for p in all_pivots}

    # 逐 bar 推进
    confirmed_pivots = []
    init_result = None

    for i, bar in enumerate(bars):
        # S2: confirm pivots（若当前 bar_dt 是某个 pivot 的 confirm_bar_dt，加入已确认列表）
        if bar.bar_dt in pivots_by_confirm_dt:
            confirmed_pivots.append(pivots_by_confirm_dt[bar.bar_dt])

        # S3-S9: 初始化判定（只要还没确认就每根都试，确认后就不再调用）
        if init_result is None or not init_result.confirmed:
            init_result = find_initial_wave(confirmed_pivots)

        # 产出当前 bar 的 snapshot
        if init_result and init_result.confirmed:
            snapshot = CoreStateSnapshot(
                symbol=bar.symbol,
                timeframe=bar.timeframe,
                bar_dt=bar.bar_dt,
                system_state=SystemState.UP_ALIVE,
                direction=Direction.UP,
                wave_core_state=WaveCoreState.ALIVE,
                current_effective_guard_price=init_result.guard_price,
                current_effective_guard_extreme_bar_dt=init_result.guard_extreme_bar_dt,
                current_effective_guard_confirm_bar_dt=init_result.guard_confirm_bar_dt,
                progress_extreme_price=init_result.progress_extreme_price,
                progress_extreme_bar_dt=init_result.progress_extreme_bar_dt,
                runtime_fingerprint=runtime_fingerprint(),
            )
        else:
            snapshot = CoreStateSnapshot(
                symbol=bar.symbol,
                timeframe=bar.timeframe,
                bar_dt=bar.bar_dt,
                system_state=SystemState.UNINITIALIZED,
                runtime_fingerprint=runtime_fingerprint(),
            )

        # 断言：与 fixture 的 expected_snapshots[i] 比对（忽略 note 字段）
        expected = expected_snapshots[i]
        assert snapshot.bar_dt == expected["bar_dt"]
        assert snapshot.system_state.value == expected["system_state"]

        if expected["direction"] is not None:
            assert snapshot.direction is not None
            assert snapshot.direction.value == expected["direction"]
        else:
            assert snapshot.direction is None

        if "wave_core_state" in expected and expected["wave_core_state"] is not None:
            assert snapshot.wave_core_state is not None
            assert snapshot.wave_core_state.value == expected["wave_core_state"]

        if "current_effective_guard_price" in expected:
            assert snapshot.current_effective_guard_price == expected.get(
                "current_effective_guard_price"
            )
            assert snapshot.current_effective_guard_extreme_bar_dt == expected.get(
                "current_effective_guard_extreme_bar_dt"
            )
            assert snapshot.current_effective_guard_confirm_bar_dt == expected.get(
                "current_effective_guard_confirm_bar_dt"
            )

        if "progress_extreme_price" in expected:
            assert snapshot.progress_extreme_price == expected.get("progress_extreme_price")
            assert snapshot.progress_extreme_bar_dt == expected.get("progress_extreme_bar_dt")


def test_skeleton_smoke():
    """空壳冒烟：证明 pytest 能发现并运行本目录的测试。此测试应 PASS。"""
    assert True
