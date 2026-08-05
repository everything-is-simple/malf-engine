"""Range 层端到端测试 - 第六刀 Day 1。

使用 Day 0 推导的 4 个 P0 fixture 验证 Range 层实现：
- R1: Continuation Range（下 break → 下突破）
- R2: Reversal Range（下 break → 上突破）
- R3: Continuation Range（上 break → 上突破）
- R4: Reversal Range（上 break → 下突破）

测试策略：
1. 加载 fixture JSON（包含 input_bars 和 expected_range_snapshots）
2. 逐 bar 运行 Core 引擎
3. 验证关键时刻的 Range 状态快照与预期一致
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from malf.core_engine import MALFCoreEngine
from malf.types import PriceBar, SystemState


def load_fixture(fixture_name: str):
    """加载 Range fixture。

    Args:
        fixture_name: fixture 文件名（不含 .json 后缀）

    Returns:
        dict: fixture 数据
    """
    fixture_path = Path(__file__).parent / "fixtures" / "range" / f"{fixture_name}.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def bars_from_fixture(fixture_data: dict) -> List[PriceBar]:
    """从 fixture 数据构造 PriceBar 列表。

    Args:
        fixture_data: fixture 数据字典

    Returns:
        List[PriceBar]: bar 序列
    """
    return [
        PriceBar(
            symbol="TEST",
            timeframe="1d",
            bar_dt=b["bar_dt"],
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"]
        )
        for b in fixture_data["input_bars"]
    ]


def test_r1_continuation_down_break_down_resolve():
    """R1: UP wave → 下 break → Range alive → 下突破 (continuation)。

    验证点：
    - Range 在 guard break 时刻诞生（d14）
    - boundary_init 从 transition boundary 继承，永不改变
    - boundary_now 单调扩展（下边界演化）
    - Resolution 判定正确（continuation）
    - Resolution distance 符号正确（负数）
    """
    fixture = load_fixture("R1_continuation_down_break_down_resolve")
    bars = bars_from_fixture(fixture)

    # 运行引擎
    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in bars]

    # 构造 bar_dt → snapshot 映射
    snapshots_by_dt = {s.bar_dt: s for s in snapshots}

    # 验证关键断言点
    expected_snapshots = fixture["expected_range_snapshots"]

    # 断言 1: Range 诞生时刻（d14）
    birth_expected = next(e for e in expected_snapshots if e["bar_dt"] == "d14")
    birth_snapshot = snapshots_by_dt["d14"]

    assert hasattr(birth_snapshot, "range_birth_bar_dt"), "Range 字段缺失：range_birth_bar_dt"
    assert birth_snapshot.range_birth_bar_dt == "d14"
    assert birth_snapshot.range_boundary_init_high == 120
    assert birth_snapshot.range_boundary_init_low == 96
    assert birth_snapshot.range_boundary_now_high == 120
    assert birth_snapshot.range_boundary_now_low == 96
    assert birth_snapshot.range_evolution_count == 0

    # 断言 2: Range resolution 时刻（d20）
    resolution_expected = next(e for e in expected_snapshots if e["bar_dt"] == "d20")
    resolution_snapshot = snapshots_by_dt["d20"]

    assert resolution_snapshot.range_resolution_bar_dt == "d20"
    assert resolution_snapshot.range_resolution_type == "continuation"
    assert resolution_snapshot.range_resolution_distance == -11  # 85 - 96 = -11
    assert resolution_snapshot.range_boundary_now_low == 85  # T9.13 E4 撤回：确认 pivot 85 演化后 now_low=85
    assert resolution_snapshot.range_evolution_count == 2  # 两次演化：d16(90), d20(85)

    # 断言 3: boundary_init 永不改变
    assert resolution_snapshot.range_boundary_init_high == 120
    assert resolution_snapshot.range_boundary_init_low == 96


def test_r2_reversal_down_break_up_resolve():
    """R2: UP wave → 下 break → Range alive → 上突破 (reversal)。

    验证点：
    - Range 诞生（d14）
    - boundary_now 双边界演化（d17 下边界，d20 上边界）
    - Resolution 判定正确（reversal）
    - Resolution distance 符号正确（正数）
    - 命名陷阱验证（reversal = 反转 break 方向）
    """
    fixture = load_fixture("R2_reversal_down_break_up_resolve")
    bars = bars_from_fixture(fixture)

    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in bars]
    snapshots_by_dt = {s.bar_dt: s for s in snapshots}

    # 断言 1: Range 诞生（d14）
    birth_snapshot = snapshots_by_dt["d14"]
    assert birth_snapshot.range_birth_bar_dt == "d14"
    assert birth_snapshot.range_boundary_init_high == 120
    assert birth_snapshot.range_boundary_init_low == 96

    # 断言 2: boundary_now 演化（d17）
    evolution_snapshot = snapshots_by_dt["d17"]
    assert evolution_snapshot.range_boundary_now_low == 88  # 演化到 88
    assert evolution_snapshot.range_evolution_count == 1

    # 断言 3: Resolution（d20）
    resolution_snapshot = snapshots_by_dt["d20"]
    assert resolution_snapshot.range_resolution_bar_dt == "d20"
    assert resolution_snapshot.range_resolution_type == "reversal"  # 反转 break 方向
    assert resolution_snapshot.range_resolution_distance == 5  # 125 - 120 = 5（正数）
    assert resolution_snapshot.range_boundary_now_high == 125  # T9.13 E4 撤回：上边界演化
    assert resolution_snapshot.range_evolution_count == 2  # 两次演化


def test_r3_continuation_up_break_up_resolve():
    """R3: DOWN wave → 上 break → Range alive → 上突破 (continuation)。

    验证点：
    - 对称性验证（R1 的 DOWN wave 版本）
    - 上 break 场景
    - 上突破 continuation
    """
    fixture = load_fixture("R3_continuation_up_break_up_resolve")
    bars = bars_from_fixture(fixture)

    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in bars]
    snapshots_by_dt = {s.bar_dt: s for s in snapshots}

    # 断言 1: Range 诞生（d14）
    birth_snapshot = snapshots_by_dt["d14"]
    assert birth_snapshot.range_birth_bar_dt == "d14"
    assert birth_snapshot.range_boundary_init_high == 110
    assert birth_snapshot.range_boundary_init_low == 80

    # 断言 2: Resolution（d20）
    resolution_snapshot = snapshots_by_dt["d20"]
    assert resolution_snapshot.range_resolution_bar_dt == "d20"
    assert resolution_snapshot.range_resolution_type == "continuation"
    assert resolution_snapshot.range_resolution_distance == 10  # 120 - 110 = 10
    assert resolution_snapshot.range_boundary_now_high == 120  # T9.13 E4 撤回：对称 R1
    assert resolution_snapshot.range_evolution_count == 2  # 两次演化


def test_r4_reversal_up_break_down_resolve():
    """R4: DOWN wave → 上 break → Range alive → 下突破 (reversal)。

    验证点：
    - 对称性验证（R2 的 DOWN wave 版本）
    - 上 break 后下突破（reversal）
    - boundary_now 双边界演化
    """
    fixture = load_fixture("R4_reversal_up_break_down_resolve")
    bars = bars_from_fixture(fixture)

    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in bars]
    snapshots_by_dt = {s.bar_dt: s for s in snapshots}

    # 断言 1: Range 诞生（d14）
    birth_snapshot = snapshots_by_dt["d14"]
    assert birth_snapshot.range_birth_bar_dt == "d14"
    assert birth_snapshot.range_boundary_init_high == 110
    assert birth_snapshot.range_boundary_init_low == 80

    # 断言 2: boundary_now 演化（d17）
    evolution_snapshot = snapshots_by_dt["d17"]
    assert evolution_snapshot.range_boundary_now_high == 118
    assert evolution_snapshot.range_evolution_count == 1

    # 断言 3: Resolution（d20）
    resolution_snapshot = snapshots_by_dt["d20"]
    assert resolution_snapshot.range_resolution_bar_dt == "d20"
    assert resolution_snapshot.range_resolution_type == "reversal"
    assert resolution_snapshot.range_resolution_distance == -5  # 75 - 80 = -5
    assert resolution_snapshot.range_boundary_now_low == 75  # T9.13 E4 撤回
    assert resolution_snapshot.range_evolution_count == 2



def test_resolution_distance_pct_covers_zero_negative_and_non_positive_invariant() -> None:
    """T9.14 裁决落地（2026-08-05）：字面 R5 可达值域为 pct ≤ 0。

    裁决 R5-A（字面实现）+ R5-E（fixture 恢复）：
    - R1/R8：确认 pivot 参与 R3 演化后 now == 确认价 → pct = 0（零值特例）
    - R7：now 已被更早 pivot 演化、确认 pivot 高于 now 但低于 init → pct 为负
    - 正值不可达（R3 演化条件与 R5 分子同 pivot 自抵消）→ 以不可达性不变量断言：全部 resolved_range.pct ≤ 0
    """
    cases = (
        ("R1_continuation_down_break_down_resolve", 0.0),   # 零值：确认 pivot 刷新 now
        ("R7_resolution_distance_negative", -5 / 90),       # 负值：now 已演化高于确认 pivot
        ("R8_resolution_distance_zero", 0.0),               # 零值：确认 pivot == now
    )

    for fixture_name, expected_pct in cases:
        fixture = load_fixture(fixture_name)
        engine = MALFCoreEngine(k=2)
        snapshots = [engine.on_bar(bar) for bar in bars_from_fixture(fixture)]
        resolved_snapshot = next(snapshot for snapshot in snapshots if snapshot.resolved_range is not None)
        resolved_range = resolved_snapshot.resolved_range

        assert resolved_range is not None
        assert resolved_range.resolution_distance_pct == expected_pct


def test_resolution_distance_pct_positive_unreachable_invariant() -> None:
    """T9.14 不可达性不变量：字面 R5 永不产生正值（权威 R3/R5 时序自引用）。

    全部既有 range fixture 的 resolution_distance_pct 必须 ≤ 0；
    若未来引擎产生正值，说明实现偏离了裁决 R5-A 的字面顺序。
    """
    for fixture in sorted((Path(__file__).parent / "fixtures" / "range").glob("R*.json")):
        data = json.loads(fixture.read_text(encoding="utf-8"))
        engine = MALFCoreEngine(k=2)
        snapshots = [engine.on_bar(bar) for bar in bars_from_fixture(data)]
        resolved = [s for s in snapshots if s.resolved_range is not None]
        for s in resolved:
            assert s.resolved_range.resolution_distance_pct is None or s.resolved_range.resolution_distance_pct <= 0, \
                f"{fixture.name}: 字面 R5 产生正值 {s.resolved_range.resolution_distance_pct}"


def test_r5_multi_evolution():
    """R5: Boundary 演化场景（验证单次演化逻辑）。

    验证点：
    - L pivot 扩张下界触发演化
    - boundary_now.low 单调递减（R2 不变量）
    - boundary_init 保持冻结

    注：此测试验证基础演化逻辑，R1-R4 已覆盖多次演化场景。
    """
    fixture = load_fixture("R5_multi_evolution")
    bars = bars_from_fixture(fixture)

    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in bars]
    snapshots_by_dt = {s.bar_dt: s for s in snapshots}

    # 断言 1: Range 诞生（d14）
    birth_snapshot = snapshots_by_dt["d14"]
    assert birth_snapshot.system_state == SystemState.TRANSITION
    assert birth_snapshot.range_birth_bar_dt == "d14"
    assert birth_snapshot.range_boundary_init_high == 120
    assert birth_snapshot.range_boundary_init_low == 96
    assert birth_snapshot.range_boundary_now_high == 120
    assert birth_snapshot.range_boundary_now_low == 96
    assert birth_snapshot.range_evolution_count == 0

    # 断言 2: 演化 #1（d18，L pivot @ 85 < 96）
    evo1_snapshot = snapshots_by_dt["d18"]
    assert evo1_snapshot.system_state == SystemState.TRANSITION
    assert evo1_snapshot.range_evolution_count == 1
    assert evo1_snapshot.range_boundary_now_high == 120
    assert evo1_snapshot.range_boundary_now_low == 85
    assert evo1_snapshot.range_boundary_init_high == 120  # frozen
    assert evo1_snapshot.range_boundary_init_low == 96    # frozen

    # 验证 R2 不变量：boundary 单调扩张
    assert evo1_snapshot.range_boundary_now_low < birth_snapshot.range_boundary_now_low
    # 验证 boundary_init 冻结
    assert evo1_snapshot.range_boundary_init_low == birth_snapshot.range_boundary_init_low


def test_r6_long_lived_unresolved():
    """R6: 长期未 resolve 场景（TRANSITION 持续但无 resolution）。

    验证点：
    - 状态稳定保持 TRANSITION
    - Range 字段持续有效（不被清空）
    - 最终仍未 resolve
    """
    fixture = load_fixture("R6_long_lived_unresolved")
    bars = bars_from_fixture(fixture)

    engine = MALFCoreEngine(k=2)
    snapshots = [engine.on_bar(bar) for bar in bars]
    snapshots_by_dt = {s.bar_dt: s for s in snapshots}

    # 断言 1: Range 诞生（d14）
    birth_snapshot = snapshots_by_dt["d14"]
    assert birth_snapshot.system_state == SystemState.TRANSITION
    assert birth_snapshot.range_birth_bar_dt == "d14"
    assert birth_snapshot.range_boundary_init_high == 120
    assert birth_snapshot.range_boundary_init_low == 96
    assert birth_snapshot.range_boundary_now_high == 120
    assert birth_snapshot.range_boundary_now_low == 96
    assert birth_snapshot.range_evolution_count == 0

    # 断言 2: 中间状态（d19，H pivot @ 102 确认，触发 candidate）
    mid_snapshot = snapshots_by_dt["d19"]
    assert mid_snapshot.system_state == SystemState.TRANSITION
    assert mid_snapshot.range_evolution_count == 1  # L @ 90 触发演化

    # 断言 3: 最终状态（d20，仍处于 TRANSITION）
    final_snapshot = snapshots_by_dt["d20"]
    assert final_snapshot.system_state == SystemState.TRANSITION
    assert final_snapshot.range_evolution_count == 1
    assert final_snapshot.range_boundary_now_high == 120
    assert final_snapshot.range_boundary_now_low == 90
    assert final_snapshot.range_boundary_init_high == 120  # frozen
    assert final_snapshot.range_boundary_init_low == 96    # frozen
    # 验证无 resolution
    assert final_snapshot.range_resolution_bar_dt is None
    assert final_snapshot.range_resolution_type is None
    assert final_snapshot.range_resolution_distance is None
    # 验证 Range 字段仍有效
    assert final_snapshot.range_birth_bar_dt == "d14"
