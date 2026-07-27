"""T7.2 percentile_rank 计算测试。

测试范围：
- percentile_rank 公式实现（v2.1 L4-3）
- peer_sample 过滤（同方向、防前视）
- span_rank, range_rank, stagnation_rank, progress_rank 计算
- 边界情况（最小值、最大值、等值）
- 样本不足退化（N < 30 → None）
"""

import json
import pytest
from pathlib import Path

from malf.types import WaveLifespan, Direction


def test_percentile_rank_calculation():
    """测试 percentile_rank 基础计算（v2.1 L4-3 公式）。

    公式：percentile_rank(x, sample) = count(x_i < x) / N
    - 严格 <（不含等于）
    - 返回 [0, 1) 范围
    """
    from malf.rank_engine import RankEngine
    rank_engine = RankEngine()

    # 测试基础计算
    x = 5
    sample = [3, 4, 6]
    expected_rank = 2/3  # count(<5) = 2
    actual_rank = rank_engine.calculate_percentile_rank(x, sample)
    assert actual_rank == pytest.approx(expected_rank, abs=0.0001)


def test_percentile_rank_edge_cases():
    """测试 percentile_rank 边界情况。"""
    from malf.rank_engine import RankEngine
    rank_engine = RankEngine()

    # 最小值：count(<2) = 0, rank = 0.0
    actual = rank_engine.calculate_percentile_rank(2, [3, 4, 6])
    assert actual == 0.0

    # 最大值：count(<7) = 3, rank = 1.0
    actual = rank_engine.calculate_percentile_rank(7, [3, 4, 6])
    assert actual == 1.0

    # 等值：count(<4) = 1（严格<，不含=）
    actual = rank_engine.calculate_percentile_rank(4, [3, 4, 6])
    assert actual == pytest.approx(1/3, abs=0.0001)


def test_wave_lifespan_rank_calculation():
    """测试 WaveLifespan 的 4 个 rank 字段计算。"""
    from malf.rank_engine import RankEngine

    rank_engine = RankEngine()

    # 构造 peer_sample（需要 >= 30 个）
    peer_sample = [
        WaveLifespan(
            wave_id=f"TEST_1D_w_{i}", symbol="TEST", timeframe="1D",
            direction=Direction.UP, wave_start_bar_dt="2024-01-01",
            wave_end_bar_dt=f"2024-01-{10+i:02d}", span_bars=3 + (i % 4),
            wave_start_price=100, wave_end_price=115 + (i % 10),
            price_range=15 + (i % 10), progress_pct=0.15 + (i % 10) * 0.01,
            primitive_count=3, pivot_count=4, new_count=1, no_new_span=2
        ) for i in range(30)
    ]

    # 当前 wave
    current_wave = WaveLifespan(
        wave_id="TEST_1D_w_current", symbol="TEST", timeframe="1D",
        direction=Direction.UP, wave_start_bar_dt="2024-02-01",
        wave_end_bar_dt="2024-02-10", span_bars=5, wave_start_price=100,
        wave_end_price=123, price_range=23, progress_pct=0.23,
        primitive_count=3, pivot_count=4, new_count=1, no_new_span=2
    )

    ranks = rank_engine.calculate_wave_ranks(current_wave, peer_sample)

    # 验证 rank 字段都不为 None（样本 >= 30）
    assert ranks["span_rank"] is not None
    assert ranks["range_rank"] is not None
    assert ranks["stagnation_rank"] is not None
    assert ranks["progress_rank"] is not None

    # 验证 rank 范围 [0, 1]
    assert 0.0 <= ranks["span_rank"] <= 1.0
    assert 0.0 <= ranks["range_rank"] <= 1.0
    assert 0.0 <= ranks["stagnation_rank"] <= 1.0
    assert 0.0 <= ranks["progress_rank"] <= 1.0


def test_peer_sample_filter_same_direction():
    """测试 peer_sample 过滤：只包含同方向 wave。"""
    from malf.rank_engine import RankEngine

    rank_engine = RankEngine()

    # 构造混合 UP/DOWN wave
    up_waves = [
        WaveLifespan(
            wave_id=f"TEST_1D_w_{i}", symbol="TEST", timeframe="1D",
            direction=Direction.UP, wave_start_bar_dt="2024-01-01",
            wave_end_bar_dt="2024-01-10", span_bars=5, wave_start_price=100,
            wave_end_price=120, price_range=20, progress_pct=0.20,
            primitive_count=3, pivot_count=4, new_count=1, no_new_span=2
        ) for i in range(3)
    ]
    down_waves = [
        WaveLifespan(
            wave_id=f"TEST_1D_w_{i+10}", symbol="TEST", timeframe="1D",
            direction=Direction.DOWN, wave_start_bar_dt="2024-01-01",
            wave_end_bar_dt="2024-01-10", span_bars=5, wave_start_price=100,
            wave_end_price=80, price_range=20, progress_pct=-0.20,
            primitive_count=3, pivot_count=4, new_count=1, no_new_span=2
        ) for i in range(2)
    ]
    all_waves = up_waves + down_waves

    # 过滤 UP wave
    filtered = rank_engine.filter_peer_sample(all_waves, direction=Direction.UP)
    assert len(filtered) == 3


def test_peer_sample_防前视():
    """测试 peer_sample 过滤：不包含未来 wave。"""
    from malf.rank_engine import RankEngine

    rank_engine = RankEngine()
    current_bar_dt = "2024-02-10"

    waves = [
        WaveLifespan(
            wave_id="TEST_1D_w_1", symbol="TEST", timeframe="1D",
            direction=Direction.UP, wave_start_bar_dt="2024-01-01",
            wave_end_bar_dt="2024-01-10", span_bars=5, wave_start_price=100,
            wave_end_price=120, price_range=20, progress_pct=0.20,
            primitive_count=3, pivot_count=4, new_count=1, no_new_span=2
        ),
        WaveLifespan(
            wave_id="TEST_1D_w_2", symbol="TEST", timeframe="1D",
            direction=Direction.UP, wave_start_bar_dt="2024-02-01",
            wave_end_bar_dt="2024-02-10", span_bars=5, wave_start_price=100,
            wave_end_price=120, price_range=20, progress_pct=0.20,
            primitive_count=3, pivot_count=4, new_count=1, no_new_span=2
        ),
        WaveLifespan(
            wave_id="TEST_1D_w_3", symbol="TEST", timeframe="1D",
            direction=Direction.UP, wave_start_bar_dt="2024-03-01",
            wave_end_bar_dt="2024-03-10", span_bars=5, wave_start_price=100,
            wave_end_price=120, price_range=20, progress_pct=0.20,
            primitive_count=3, pivot_count=4, new_count=1, no_new_span=2
        )
    ]

    filtered = rank_engine.filter_peer_sample(waves, cutoff_bar_dt=current_bar_dt)
    assert len(filtered) == 2


def test_sample_size_constraint():
    """测试样本不足退化：N < 30 → None。"""
    from malf.rank_engine import RankEngine

    rank_engine = RankEngine()

    # 构造小样本（N < 30）
    small_sample = [
        WaveLifespan(
            wave_id=f"TEST_1D_w_{i}", symbol="TEST", timeframe="1D",
            direction=Direction.UP, wave_start_bar_dt="2024-01-01",
            wave_end_bar_dt="2024-01-10", span_bars=5, wave_start_price=100,
            wave_end_price=120, price_range=20, progress_pct=0.20,
            primitive_count=3, pivot_count=4, new_count=1, no_new_span=2
        ) for i in range(10)
    ]

    current_wave = small_sample[0]
    ranks = rank_engine.calculate_wave_ranks(current_wave, small_sample)

    assert ranks["span_rank"] is None
    assert ranks["range_rank"] is None
    assert ranks["stagnation_rank"] is None
    assert ranks["progress_rank"] is None
