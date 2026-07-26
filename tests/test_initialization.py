"""S5 验证：初始化状态机（D18/O6）在 golden fixture 上判定 up_alive 和 down_alive 的时刻与守护完全一致。

范围（见 malf/initialization.py 模块 docstring 的范围声明）：
- ✅ up 方向、干净序列（H0→L1→H2>H0，无 C-07 替换）— 第一刀已实现
- ✅ down 方向、干净序列（L0→H1→L2<L0）— 第二刀已实现
- ❌ H0/L0 替换（【填洞 C-07】）暂未实现
- ❌ L1/H1 替换暂未实现

超出已实现范围的输入应显式 NotImplementedError，不能沉默地给出未经验证的结果。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from malf.initialization import find_initial_wave
from malf.pivot_detection import detect_pivots
from malf.types import Direction, Pivot, PivotType, PriceBar

FIXTURE = Path(__file__).parent / "fixtures" / "uninitialized_to_up_alive.json"


def _load():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def _bars_from(input_bars):
    return [
        PriceBar(
            symbol="TEST", timeframe="day", bar_dt=b["bar_dt"],
            open=b["open"], high=b["high"], low=b["low"], close=b["close"],
        )
        for b in input_bars
    ]


def test_find_initial_wave_matches_golden_fixture():
    """golden fixture 的干净序列：H0(d02/d04,110) → L1(d05/d07,96) → H2(d09/d11,114)>H0。"""
    d = _load()
    bars = _bars_from(d["input_bars"])
    raw_pivots = detect_pivots(bars, k=d["params"]["k"])
    # 状态机看到 pivot 的时刻是 confirm_bar_dt，不是 extreme_bar_dt（时序不对称）
    pivots_confirm_order = sorted(raw_pivots, key=lambda p: p.confirm_bar_dt)

    result = find_initial_wave(pivots_confirm_order)

    last_snapshot = d["expected_snapshots"][-1]
    assert result.confirmed is True
    assert result.direction is Direction.UP
    assert result.confirm_bar_dt == last_snapshot["bar_dt"]  # d11
    assert result.guard_price == last_snapshot["current_effective_guard_price"]  # 96 = L1
    assert result.guard_extreme_bar_dt == last_snapshot["current_effective_guard_extreme_bar_dt"]
    assert result.guard_confirm_bar_dt == last_snapshot["current_effective_guard_confirm_bar_dt"]
    assert result.progress_extreme_price == last_snapshot["progress_extreme_price"]  # 114 = H2
    assert result.progress_extreme_bar_dt == last_snapshot["progress_extreme_bar_dt"]


def test_find_initial_wave_not_yet_confirmed_on_prefix():
    """只喂前两个 pivot（H0, L1），H2 还没出现——必须仍是 uninitialized（O6 失败规则）。"""
    h0 = Pivot(pivot_type=PivotType.H, price=110, extreme_bar_dt="d02", confirm_bar_dt="d04")
    l1 = Pivot(pivot_type=PivotType.L, price=96, extreme_bar_dt="d05", confirm_bar_dt="d07")

    result = find_initial_wave([h0, l1])

    assert result.confirmed is False


def test_find_initial_wave_waits_when_h2_does_not_exceed_h0():
    """H2 不满足严格突破（<=H0）时应继续等待，不确认；后续真正的 H2'>H0 才确认。

    人肉推导：H0=110, L1=96, H_a=105(<=110，不确认，继续等)，H_b=114(>110，确认)。
    这不是 C-07 替换场景（H_a 没有比 H0 高，不触发替换），是纯粹的"结构不足继续等"（O6）。
    """
    h0 = Pivot(pivot_type=PivotType.H, price=110, extreme_bar_dt="d02", confirm_bar_dt="d04")
    l1 = Pivot(pivot_type=PivotType.L, price=96, extreme_bar_dt="d05", confirm_bar_dt="d07")
    h_a = Pivot(pivot_type=PivotType.H, price=105, extreme_bar_dt="d08", confirm_bar_dt="d10")
    h_b = Pivot(pivot_type=PivotType.H, price=114, extreme_bar_dt="d12", confirm_bar_dt="d14")

    result = find_initial_wave([h0, l1, h_a, h_b])

    assert result.confirmed is True
    assert result.progress_extreme_price == 114
    assert result.confirm_bar_dt == "d14"
    assert result.guard_price == 96  # L1 不受 h_a 影响


def test_find_initial_wave_down_direction_implemented():
    """down 方向（L0→H1→L2<L0）已实现（第二刀）——验证基本的 down 序列能正确返回。"""
    l0 = Pivot(pivot_type=PivotType.L, price=100, extreme_bar_dt="d00", confirm_bar_dt="d02")
    h1 = Pivot(pivot_type=PivotType.H, price=115, extreme_bar_dt="d03", confirm_bar_dt="d05")
    l2 = Pivot(pivot_type=PivotType.L, price=95, extreme_bar_dt="d05", confirm_bar_dt="d07")

    result = find_initial_wave([l0, h1, l2])

    assert result.confirmed is True
    assert result.direction is Direction.DOWN
    assert result.confirm_bar_dt == "d07"
    assert result.guard_price == 115  # H1
    assert result.progress_extreme_price == 95  # L2


def test_find_initial_wave_h0_replacement_implemented():
    """H0 被更高 H 替换（C-07 规则已实现）——更高的 H 替换 H0。"""
    h0 = Pivot(pivot_type=PivotType.H, price=110, extreme_bar_dt="d02", confirm_bar_dt="d04")
    h_higher = Pivot(pivot_type=PivotType.H, price=120, extreme_bar_dt="d05", confirm_bar_dt="d07")
    l1 = Pivot(pivot_type=PivotType.L, price=96, extreme_bar_dt="d08", confirm_bar_dt="d10")
    h2 = Pivot(pivot_type=PivotType.H, price=125, extreme_bar_dt="d11", confirm_bar_dt="d13")

    result = find_initial_wave([h0, h_higher, l1, h2])

    # H0 should be replaced by h_higher (120), and H2 (125) > h_higher (120) triggers initialization
    assert result.confirmed is True
    assert result.direction is Direction.UP
    assert result.guard_price == 96  # L1
    assert result.progress_extreme_price == 125  # H2


def test_find_initial_wave_l1_replacement_implemented():
    """L1 之后、H2 确认前又出现一个 L（C-07 规则已实现）——更低的 L 替换 L1。"""
    h0 = Pivot(pivot_type=PivotType.H, price=110, extreme_bar_dt="d02", confirm_bar_dt="d04")
    l1 = Pivot(pivot_type=PivotType.L, price=96, extreme_bar_dt="d05", confirm_bar_dt="d07")
    l_lower = Pivot(pivot_type=PivotType.L, price=90, extreme_bar_dt="d08", confirm_bar_dt="d10")
    h2 = Pivot(pivot_type=PivotType.H, price=115, extreme_bar_dt="d11", confirm_bar_dt="d13")

    result = find_initial_wave([h0, l1, l_lower, h2])

    # L1 should be replaced by l_lower (90), which becomes the guard
    assert result.confirmed is True
    assert result.direction is Direction.UP
    assert result.guard_price == 90  # l_lower replaces l1
    assert result.progress_extreme_price == 115  # H2
