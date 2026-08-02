"""T7.1 WaveLifespan 指标计算测试。

测试范围：
- WaveLifespan 数据结构
- 已终止 wave 的生命周期指标提取
- span_bars, price_range, progress_pct 计算
- primitive_count, pivot_count, new_count 统计
- no_new_span 计算
"""

import json
import pytest
from pathlib import Path

from malf.types import WaveLifespan, Direction
from malf.lifespan_engine import LifespanEngine


def test_wave_lifespan_up_terminated():
    """测试 UP wave 终止后的 WaveLifespan 指标计算。

    场景：
    - H0(110) → L1(99) → H2(120) 确认 UP
    - Alive 期间新增 HH(122)
    - Close < guard 触发 break，wave terminated

    预期：
    - span_bars = 5（从 confirmation bar 到 break bar）
    - price_range = 23（122 - 99）
    - progress_pct = 0.086957（v2.1 结构进展公式）
    - new_count = 1（HH）
    - no_new_span = 2（最后新 pivot 到 break）
    """
    fixture_path = Path(__file__).parent / "fixtures" / "t7_1_wave_lifespan_up.json"
    with open(fixture_path, encoding="utf-8") as f:
        fixture = json.load(f)

    expected = fixture["expected_wave_lifespan"]

    # 使用 LifespanEngine 计算 WaveLifespan
    from malf.lifespan_engine import LifespanEngine
    engine = LifespanEngine()

    actual_lifespan = engine.calculate_wave_lifespan(
        wave_id=expected["wave_id"],
        symbol="TEST",
        timeframe="1D",
        direction=Direction.UP,
        wave_start_bar_dt="2024-01-08",
        wave_end_bar_dt="2024-01-12",
        wave_start_price=expected["wave_start_price"],
        wave_end_price=expected["wave_end_price"],
        span_bars=expected["span_bars"],
        primitive_count=expected["primitive_count"],
        pivot_count=expected["pivot_count"],
        new_count=expected["new_count"],
        no_new_span=expected["no_new_span"],
        first_pivot_price=expected["first_pivot_price"],
        guard_price=expected["guard_price"],
    )

    # 验证计算结果
    assert actual_lifespan.wave_id == expected["wave_id"]
    assert actual_lifespan.symbol == "TEST"
    assert actual_lifespan.timeframe == "1D"
    assert actual_lifespan.direction == Direction.UP
    assert actual_lifespan.span_bars == expected["span_bars"]
    assert actual_lifespan.wave_start_price == expected["wave_start_price"]
    assert actual_lifespan.wave_end_price == expected["wave_end_price"]
    assert actual_lifespan.price_range == expected["price_range"]
    assert actual_lifespan.progress_pct == pytest.approx(expected["progress_pct"], abs=0.0001)
    assert actual_lifespan.primitive_count == expected["primitive_count"]
    assert actual_lifespan.pivot_count == expected["pivot_count"]
    assert actual_lifespan.new_count == expected["new_count"]
    assert actual_lifespan.no_new_span == expected["no_new_span"]

    # 验证排名字段初始为 None
    assert actual_lifespan.span_rank is None
    assert actual_lifespan.range_rank is None
    assert actual_lifespan.stagnation_rank is None
    assert actual_lifespan.progress_rank is None


def test_wave_lifespan_fields_structure():
    """测试 WaveLifespan 数据结构字段完整性。"""
    lifespan = WaveLifespan(
        wave_id="TEST_1D_w_1",
        symbol="TEST",
        timeframe="1D",
        direction=Direction.UP,
        wave_start_bar_dt="2024-01-01",
        wave_end_bar_dt="2024-01-05",
        span_bars=5,
        wave_start_price=100,
        wave_end_price=120,
        price_range=20,
        progress_pct=0.20,
        primitive_count=3,
        pivot_count=4,
        new_count=1,
        no_new_span=2
    )

    # 验证必填字段
    assert lifespan.wave_id == "TEST_1D_w_1"
    assert lifespan.direction == Direction.UP
    assert lifespan.span_bars == 5
    assert lifespan.price_range == 20
    assert lifespan.progress_pct == 0.20
    assert lifespan.new_count == 1
    assert lifespan.no_new_span == 2

    # 验证排名字段初始为 None
    assert lifespan.span_rank is None
    assert lifespan.range_rank is None
    assert lifespan.stagnation_rank is None
    assert lifespan.progress_rank is None


def test_wave_lifespan_down_direction():
    """DOWN wave uses the mirrored progress_pct formula."""
    engine = LifespanEngine()
    lifespan = engine.calculate_wave_lifespan(
        wave_id="TEST_1D_w_down",
        symbol="TEST",
        timeframe="1D",
        direction=Direction.DOWN,
        wave_start_bar_dt="2024-01-01",
        wave_start_price=120,
        wave_end_bar_dt="2024-01-05",
        wave_end_price=80,
        span_bars=5,
        primitive_count=3,
        pivot_count=4,
        new_count=1,
        no_new_span=2,
        first_pivot_price=120,
        guard_price=100,
    )

    assert lifespan.direction == Direction.DOWN
    assert lifespan.price_range == 40
    assert lifespan.progress_pct == 2.0
    assert lifespan.span_rank is None
    assert lifespan.range_rank is None
    assert lifespan.stagnation_rank is None
    assert lifespan.progress_rank is None


