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
    assert resolution_snapshot.range_boundary_now_low == 85  # 演化到 85
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
    assert resolution_snapshot.range_boundary_now_high == 125  # 上边界演化
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
    assert resolution_snapshot.range_boundary_now_high == 120
    assert resolution_snapshot.range_evolution_count == 2  # 两次演化（对称 R1）


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
    assert resolution_snapshot.range_boundary_now_low == 75
    assert resolution_snapshot.range_evolution_count == 2
