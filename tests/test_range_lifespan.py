"""Range Lifespan 计算测试 - T7.3。

测试 RangeLifespan 指标计算：
- span_bars: resolution_bar_dt - break_bar_dt
- evolution_count: 从 Range 对象提取
- replacement_count: 从 Range 对象提取
- resolution_distance: 从 Range 对象提取
- resolution_distance_pct: abs(resolution_distance) / amplitude_init
- amplitude_init: boundary_high_init - boundary_low_init
- amplitude_now: boundary_high_now - boundary_low_now
- amplitude_pct: amplitude_now / boundary_low_init
"""

from __future__ import annotations

import pytest
from malf.lifespan_engine import LifespanEngine
from malf.types import RangeResolutionType


def test_calculate_range_lifespan_simple():
    """测试简单 Range 指标计算（无演化）。

    场景：
    - Range 持续 10 bars
    - 无 boundary 演化（evolution_count = 0）
    - 无 candidate 替换（replacement_count = 0）
    - Resolution 距离：10（向上突破）
    - boundary_init: [100, 120]
    - boundary_now: [100, 120]（无演化）
    """
    engine = LifespanEngine()

    lifespan = engine.calculate_range_lifespan(
        range_id="TEST_1d_R1",
        symbol="TEST",
        timeframe="1d",
        range_type=RangeResolutionType.CONTINUATION,
        range_start_bar_dt="d14",
        range_end_bar_dt="d24",
        span_bars=10,
        evolution_count=0,
        replacement_count=0,
        resolution_distance=10,
        boundary_high_init=120,
        boundary_low_init=100,
        boundary_high_now=120,
        boundary_low_now=100
    )

    # 验证基础字段
    assert lifespan.range_id == "TEST_1d_R1"
    assert lifespan.symbol == "TEST"
    assert lifespan.timeframe == "1d"
    assert lifespan.range_type == RangeResolutionType.CONTINUATION
    assert lifespan.range_start_bar_dt == "d14"
    assert lifespan.range_end_bar_dt == "d24"
    assert lifespan.span_bars == 10

    # 验证演化统计
    assert lifespan.evolution_count == 0
    assert lifespan.replacement_count == 0

    # 验证 resolution 距离
    assert lifespan.resolution_distance == 10
    assert lifespan.resolution_distance_pct == pytest.approx(10 / 20)  # 10 / (120 - 100)

    # 验证 amplitude 计算
    assert lifespan.amplitude_init == 20  # 120 - 100
    assert lifespan.amplitude_now == 20   # 120 - 100（无演化）
    assert lifespan.amplitude_pct == pytest.approx(20 / 100)  # 0.2

    # 验证排名字段初始为 None
    assert lifespan.span_rank is None
    assert lifespan.evolution_rank is None
    assert lifespan.replacement_rank is None
    assert lifespan.resolution_distance_rank is None


def test_calculate_range_lifespan_with_evolution():
    """测试带演化的 Range 指标计算。

    场景：
    - Range 持续 15 bars
    - Boundary 演化 3 次（evolution_count = 3）
    - Candidate 替换 2 次（replacement_count = 2）
    - Resolution 距离：-8（向下突破）
    - boundary_init: [80, 110]
    - boundary_now: [75, 115]（演化后扩展）
    """
    engine = LifespanEngine()

    lifespan = engine.calculate_range_lifespan(
        range_id="TEST_1d_R2",
        symbol="TEST",
        timeframe="1d",
        range_type=RangeResolutionType.REVERSAL,
        range_start_bar_dt="d10",
        range_end_bar_dt="d25",
        span_bars=15,
        evolution_count=3,
        replacement_count=2,
        resolution_distance=-8,
        boundary_high_init=110,
        boundary_low_init=80,
        boundary_high_now=115,
        boundary_low_now=75
    )

    # 验证基础字段
    assert lifespan.range_id == "TEST_1d_R2"
    assert lifespan.range_type == RangeResolutionType.REVERSAL
    assert lifespan.span_bars == 15

    # 验证演化统计
    assert lifespan.evolution_count == 3
    assert lifespan.replacement_count == 2

    # 验证 resolution 距离（负数 → 向下突破）
    assert lifespan.resolution_distance == -8
    assert lifespan.resolution_distance_pct == pytest.approx(8 / 30)  # abs(-8) / (110 - 80)

    # 验证 amplitude 计算
    assert lifespan.amplitude_init == 30  # 110 - 80
    assert lifespan.amplitude_now == 40   # 115 - 75（演化后扩展）
    assert lifespan.amplitude_pct == pytest.approx(40 / 80)  # 0.5


def test_calculate_range_lifespan_continuation_vs_reversal():
    """测试 continuation 和 reversal 类型的区分。"""
    engine = LifespanEngine()

    # Continuation Range
    continuation = engine.calculate_range_lifespan(
        range_id="TEST_1d_R3",
        symbol="TEST",
        timeframe="1d",
        range_type=RangeResolutionType.CONTINUATION,
        range_start_bar_dt="d1",
        range_end_bar_dt="d10",
        span_bars=9,
        evolution_count=1,
        replacement_count=0,
        resolution_distance=5,
        boundary_high_init=120,
        boundary_low_init=100,
        boundary_high_now=120,
        boundary_low_now=100
    )

    # Reversal Range
    reversal = engine.calculate_range_lifespan(
        range_id="TEST_1d_R4",
        symbol="TEST",
        timeframe="1d",
        range_type=RangeResolutionType.REVERSAL,
        range_start_bar_dt="d1",
        range_end_bar_dt="d10",
        span_bars=9,
        evolution_count=1,
        replacement_count=0,
        resolution_distance=5,
        boundary_high_init=120,
        boundary_low_init=100,
        boundary_high_now=120,
        boundary_low_now=100
    )

    assert continuation.range_type == RangeResolutionType.CONTINUATION
    assert reversal.range_type == RangeResolutionType.REVERSAL


def test_record_and_get_resolved_ranges():
    """测试 Range 历史记录和检索（分类型）。"""
    engine = LifespanEngine()

    # 创建 3 个 continuation 和 2 个 reversal
    for i in range(3):
        lifespan = engine.calculate_range_lifespan(
            range_id=f"TEST_1d_R{i}",
            symbol="TEST",
            timeframe="1d",
            range_type=RangeResolutionType.CONTINUATION,
            range_start_bar_dt="d1",
            range_end_bar_dt="d10",
            span_bars=9,
            evolution_count=i,
            replacement_count=0,
            resolution_distance=5,
            boundary_high_init=120,
            boundary_low_init=100,
            boundary_high_now=120,
            boundary_low_now=100
        )
        engine.record_resolved_range(lifespan)

    for i in range(2):
        lifespan = engine.calculate_range_lifespan(
            range_id=f"TEST_1d_R{i+3}",
            symbol="TEST",
            timeframe="1d",
            range_type=RangeResolutionType.REVERSAL,
            range_start_bar_dt="d1",
            range_end_bar_dt="d10",
            span_bars=9,
            evolution_count=i,
            replacement_count=0,
            resolution_distance=5,
            boundary_high_init=120,
            boundary_low_init=100,
            boundary_high_now=120,
            boundary_low_now=100
        )
        engine.record_resolved_range(lifespan)

    # 获取全部
    all_ranges = engine.get_resolved_ranges()
    assert len(all_ranges) == 5

    # 获取 continuation
    continuation_ranges = engine.get_resolved_ranges(RangeResolutionType.CONTINUATION)
    assert len(continuation_ranges) == 3
    assert all(r.range_type == RangeResolutionType.CONTINUATION for r in continuation_ranges)

    # 获取 reversal
    reversal_ranges = engine.get_resolved_ranges(RangeResolutionType.REVERSAL)
    assert len(reversal_ranges) == 2
    assert all(r.range_type == RangeResolutionType.REVERSAL for r in reversal_ranges)


def test_resolution_distance_pct_zero_amplitude():
    """测试边界情况：boundary_init 幅度为 0。

    理论上不应该发生（Range 诞生需要有幅度），
    但防御性编程需要处理这种情况。
    """
    engine = LifespanEngine()

    lifespan = engine.calculate_range_lifespan(
        range_id="TEST_1d_R_EDGE",
        symbol="TEST",
        timeframe="1d",
        range_type=RangeResolutionType.CONTINUATION,
        range_start_bar_dt="d1",
        range_end_bar_dt="d10",
        span_bars=9,
        evolution_count=0,
        replacement_count=0,
        resolution_distance=5,
        boundary_high_init=100,
        boundary_low_init=100,  # 幅度为 0
        boundary_high_now=100,
        boundary_low_now=100
    )

    # 验证：amplitude_init = 0 时，resolution_distance_pct = 0.0
    assert lifespan.amplitude_init == 0
    assert lifespan.resolution_distance_pct == 0.0
