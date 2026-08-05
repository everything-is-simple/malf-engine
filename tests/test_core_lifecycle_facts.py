from __future__ import annotations

import json
from pathlib import Path

from malf.core_engine import MALFCoreEngine
from malf.types import Direction, PriceBar, RangeState, SystemState, WaveCoreState


def _bars(name: str):
    data = json.loads((Path(__file__).parent / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))
    return [
        PriceBar("TEST", "1d", b["bar_dt"], b["open"], b["high"], b["low"], b["close"])
        for b in data["input_bars"]
    ]


def test_core_publishes_initial_wave_facts_without_private_state():
    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in _bars("t3_same_direction_break_up")]

    alive = next(s for s in snapshots if s.bar_dt == "d08")
    assert alive.active_wave is not None
    assert alive.active_wave_id == "TEST_1d_1"
    wave = alive.active_wave
    assert wave.direction is Direction.UP
    assert wave.birth_type == "initial"
    assert wave.wave_state is WaveCoreState.ALIVE
    assert [p.price for p in wave.pivots] == [102, 94, 104]
    assert wave.primitive_count == 2
    assert wave.pivot_count == 3
    assert wave.first_pivot_price == 102
    assert wave.new_count == 0


def test_core_publishes_terminated_wave_event_once():
    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in _bars("t3_same_direction_break_up")]

    transition = next(s for s in snapshots if s.bar_dt == "d09")
    assert transition.terminated_wave is not None
    assert transition.active_wave is None
    terminated = transition.terminated_wave
    assert terminated.wave_state is WaveCoreState.TERMINATED
    assert terminated.wave_id == "TEST_1d_1"
    assert terminated.break_bar_dt == "d09"
    assert terminated.break_price == 90
    assert terminated.wave_end_price == 104
    assert transition.active_wave_id is None

    later = engine.on_bar(PriceBar("TEST", "1d", "d10", 92, 97, 91, 95))
    assert later.terminated_wave is None


def test_core_publishes_range_objects_and_resolution_uses_boundary_now():
    data = json.loads((Path(__file__).parent / "fixtures" / "range" / "R1_continuation_down_break_down_resolve.json").read_text(encoding="utf-8"))
    bars = [PriceBar("TEST", "1d", b["bar_dt"], b["open"], b["high"], b["low"], b["close"]) for b in data["input_bars"]]
    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in bars]

    alive_range = next(s for s in snapshots if s.bar_dt == "d14")
    assert alive_range.active_range is not None
    assert alive_range.active_range.range_state is RangeState.ALIVE
    assert alive_range.active_range.range_id == "TEST_1d_R1"

    resolved = next(s for s in snapshots if s.bar_dt == "d20")
    assert resolved.resolved_range is not None
    assert resolved.resolved_range.range_state is RangeState.RESOLVED
    assert resolved.resolved_range.resolution_distance == -11
    # T9.13 E4 撤回（2026-08-06 用户授权）：R5 用演化后 now（确认 pivot 85 已刷新边界）→ pct=0；R5 口径留战役 2 裁决
    assert resolved.resolved_range.resolution_distance_pct == 0.0
    assert resolved.resolved_range.resolution_bar_dt == "d20"
    assert resolved.resolved_range.resolution_type.value == "continuation"

    later = engine.on_bar(PriceBar("TEST", "1d", "d21", 85, 90, 84, 88))
    assert later.resolved_range is None


def test_same_bar_confirmed_pivot_is_evolved_after_guard_break() -> None:
    """Core §9 O2：break 进入 Transition 后，同一确认 bar 仍须完成候选演化。

    d13 同时确认 d11 的 H pivot（120）且 low=90 严格穿透旧 UP wave 的
    guard=96。Pivot 的 extreme bar 是 d11，不是 break bar d13，因此 C-05
    不排除它；O2 第 5 步要求本 bar 立刻把它纳入 Transition。
    """
    source = json.loads(
        (Path(__file__).parent / "fixtures" / "range" / "R1_continuation_down_break_down_resolve.json").read_text(
            encoding="utf-8"
        )
    )
    bars = [
        PriceBar(
            "TEST",
            "1d",
            item["bar_dt"],
            item["open"],
            item["high"],
            90 if item["bar_dt"] == "d13" else item["low"],
            item["close"],
        )
        for item in source["input_bars"]
    ]

    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in bars[:14]]
    same_bar = snapshots[-1]

    assert same_bar.bar_dt == "d13"
    assert same_bar.system_state is SystemState.TRANSITION
    assert same_bar.break_bar_dt == "d13"
    assert same_bar.active_candidate_guard_price == 120
    assert same_bar.active_candidate_direction is Direction.UP
    assert same_bar.range_boundary_now_high == 120
    assert same_bar.range_evolution_count == 1
