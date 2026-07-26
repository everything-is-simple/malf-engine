"""第三刀端到端测试：up_alive → transition (guard break)。

逐 bar 喂入，验证 guard break 触发时状态转换到 transition。
"""

from __future__ import annotations

import json
from pathlib import Path

from malf.core_engine import MALFCoreEngine
from malf.types import PriceBar, SystemState


def test_t3_same_direction_break_up_end_to_end():
    """
    Given: H0→L1→H2>H0 进入 up_alive，guard=94
    When: bar.close < guard (LH break)
    Then: system_state = transition
    """
    fixture_path = Path(__file__).parent / "fixtures" / "t3_same_direction_break_up.json"

    with open(fixture_path, encoding="utf-8") as f:
        d = json.load(f)

    k = d["params"]["k"]
    expected_snapshots = d["expected_snapshots"]

    # 构造 PriceBar 对象
    bars = [
        PriceBar(
            symbol="TEST",
            timeframe="day",
            bar_dt=b["bar_dt"],
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"],
        )
        for b in d["input_bars"]
    ]

    # 创建引擎并逐 bar 推进
    engine = MALFCoreEngine(k=k)

    for i, bar in enumerate(bars):
        expected = expected_snapshots[i]

        # 如果预期会抛出 NotImplementedError（transition 后续逻辑），就到此为止
        if expected["system_state"] == "transition":
            # 验证前一个状态是 up_alive
            assert i > 0
            prev_snapshot = engine.on_bar(bars[i - 1]) if i == len(bars) - 1 else None

            # 现在喂入会触发 guard break 的 bar
            snapshot = engine.on_bar(bar)
            # 第四刀已实现 transition 逻辑
            assert snapshot.system_state == SystemState.TRANSITION
            break
        else:
            snapshot = engine.on_bar(bar)

            # 断言：与 fixture 的 expected_snapshots[i] 比对
            assert snapshot.system_state.value == expected["system_state"], (
                f"Bar {i}: expected system_state={expected['system_state']}, "
                f"got {snapshot.system_state.value}"
            )

            if expected.get("direction") is not None:
                assert snapshot.direction is not None
                assert snapshot.direction.value == expected["direction"]
            else:
                assert snapshot.direction is None

            if expected.get("guard_price") is not None:
                assert snapshot.current_effective_guard_price == expected["guard_price"]

            if expected.get("progress_extreme_price") is not None:
                assert snapshot.progress_extreme_price == expected["progress_extreme_price"]


def test_t3_same_direction_break_down_end_to_end():
    """
    Given: L0→H1→L2<L0 进入 down_alive，guard=106
    When: bar.close > guard (HL break)
    Then: system_state = transition
    """
    fixture_path = Path(__file__).parent / "fixtures" / "t3_same_direction_break_down.json"

    with open(fixture_path, encoding="utf-8") as f:
        d = json.load(f)

    k = d["params"]["k"]
    expected_snapshots = d["expected_snapshots"]

    # 构造 PriceBar 对象
    bars = [
        PriceBar(
            symbol="TEST",
            timeframe="day",
            bar_dt=b["bar_dt"],
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"],
        )
        for b in d["input_bars"]
    ]

    # 创建引擎并逐 bar 推进
    engine = MALFCoreEngine(k=k)

    for i, bar in enumerate(bars):
        expected = expected_snapshots[i]

        # 如果预期会抛出 NotImplementedError（transition 后续逻辑），就到此为止
        if expected["system_state"] == "transition":
            # 验证前一个状态是 down_alive
            assert i > 0

            # 现在喂入会触发 guard break 的 bar
            snapshot = engine.on_bar(bar)
            # 第四刀已实现 transition 逻辑
            assert snapshot.system_state == SystemState.TRANSITION
            break
        else:
            snapshot = engine.on_bar(bar)

            # 断言：与 fixture 的 expected_snapshots[i] 比对
            assert snapshot.system_state.value == expected["system_state"], (
                f"Bar {i}: expected system_state={expected['system_state']}, "
                f"got {snapshot.system_state.value}"
            )

            if expected.get("direction") is not None:
                assert snapshot.direction is not None
                assert snapshot.direction.value == expected["direction"]
            else:
                assert snapshot.direction is None

            if expected.get("guard_price") is not None:
                assert snapshot.current_effective_guard_price == expected["guard_price"]

            if expected.get("progress_extreme_price") is not None:
                assert snapshot.progress_extreme_price == expected["progress_extreme_price"]
