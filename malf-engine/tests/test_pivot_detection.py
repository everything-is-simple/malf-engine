"""S4 验证：pivot 检测（分形 k=2）在 golden fixture 上产出的 pivot 与人肉推导的预期完全一致。

TDD：先写这个测试（此刻应为 RED——detect_pivots 尚未实现），再实现 pivot_detection.py 让它变绿。
不断言中间过程，只断言最终产出的 pivot 列表——这是 S4 唯一的验收线。
"""

from __future__ import annotations

import json
from pathlib import Path

from malf.pivot_detection import detect_pivots
from malf.types import Pivot, PivotType, PriceBar

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


def test_detect_pivots_matches_golden_fixture():
    d = _load()
    bars = _bars_from(d["input_bars"])
    k = d["params"]["k"]

    got = detect_pivots(bars, k=k)

    expected = [
        Pivot(
            pivot_type=PivotType(p["pivot_type"]),
            price=p["price"],
            extreme_bar_dt=p["extreme_bar_dt"],
            confirm_bar_dt=p["confirm_bar_dt"],
        )
        for p in d["expected_pivots"]
    ]

    assert got == expected


def test_detect_pivots_window_boundary_no_crash():
    """窗口不足的边界（首尾各 k 根凑不齐）不应抛异常，也不应产生 pivot。"""
    d = _load()
    bars = _bars_from(d["input_bars"][:3])  # 只给 3 根，k=2 时任何 i 都凑不齐左右窗口
    got = detect_pivots(bars, k=2)
    assert got == []


def test_detect_pivots_rejects_invalid_k():
    d = _load()
    bars = _bars_from(d["input_bars"])
    try:
        detect_pivots(bars, k=0)
        assert False, "k=0 应拒绝"
    except ValueError:
        pass
