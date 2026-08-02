"""测试 RangeLifespan peer_sample + rank 计算（T7.4）。

Golden Fixture 驱动：
- t7_4_range_ranks_continuation.json

测试覆盖：
- continuation/reversal 分池
- 防前视过滤
- percentile_rank 计算（4 个 rank 字段）
- 样本不足退化（N < 30 → None）
"""

import json
from pathlib import Path

import pytest

from malf.rank_engine import RankEngine
from malf.lifespan_engine import LifespanEngine
from malf.types import RangeResolutionType, RangeLifespan


def load_fixture(filename: str) -> dict:
    """加载 golden fixture（UTF-8 编码）。"""
    fixture_path = Path(__file__).parent / "fixtures" / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_range_ranks_continuation_golden_fixture():
    """测试 continuation_range 的 rank 计算（Golden Fixture）。

    场景：35 个 continuation_range 样本池，计算当前 Range 的 4 个 rank
    """
    fixture = load_fixture("t7_4_range_ranks_continuation.json")
    peer_data = fixture["peer_sample"]
    current_data = fixture["current_range"]
    expected = fixture["expected_output"]

    # 构建 peer_sample（35 个 RangeLifespan 对象）
    peer_sample = []
    for p in peer_data:
        lifespan = RangeLifespan(
            range_id=p["range_id"],
            symbol="SH600000",
            timeframe="D",
            range_type=RangeResolutionType(p["range_type"]),
            range_start_bar_dt="2020-01-01",  # 简化，不影响 rank 计算
            range_end_bar_dt=p["range_end_bar_dt"],
            span_bars=p["span_bars"],
            evolution_count=p["evolution_count"],
            replacement_count=p["replacement_count"],
            resolution_distance=0,  # 简化
            resolution_distance_pct=p["resolution_distance_pct"],
            amplitude_init=1000,
            amplitude_now=1000,
            amplitude_pct=0.1
        )
        peer_sample.append(lifespan)

    # 构建当前 Range
    current_range = RangeLifespan(
        range_id=current_data["range_id"],
        symbol=current_data["symbol"],
        timeframe=current_data["timeframe"],
        range_type=RangeResolutionType(current_data["range_type"]),
        range_start_bar_dt=current_data["range_start_bar_dt"],
        range_end_bar_dt=current_data["range_end_bar_dt"],
        span_bars=current_data["span_bars"],
        evolution_count=current_data["evolution_count"],
        replacement_count=current_data["replacement_count"],
        resolution_distance=current_data["resolution_distance"],
        resolution_distance_pct=current_data["resolution_distance_pct"],
        amplitude_init=current_data["amplitude_init"],
        amplitude_now=current_data["amplitude_now"],
        amplitude_pct=current_data["amplitude_pct"]
    )

    # 调用 RankEngine 计算 rank
    rank_engine = RankEngine()
    ranks = rank_engine.calculate_range_ranks(current_range, peer_sample)

    # 验证 rank 字段
    assert ranks["span_rank"] == pytest.approx(expected["span_rank"], abs=1e-6)
    assert ranks["evolution_rank"] == pytest.approx(expected["evolution_rank"], abs=1e-6)
    assert ranks["replacement_rank"] == pytest.approx(expected["replacement_rank"], abs=1e-6)
    assert ranks["resolution_distance_rank"] == pytest.approx(expected["resolution_distance_rank"], abs=1e-6)


def test_range_peer_sample_filtering_by_type():
    """测试 peer_sample 按类型过滤（continuation vs reversal）。"""
    lifespan_engine = LifespanEngine()

    # 创建 3 个 continuation 和 2 个 reversal
    for i in range(3):
        lifespan = RangeLifespan(
            range_id=f"TEST_R{i}",
            symbol="TEST",
            timeframe="D",
            range_type=RangeResolutionType.CONTINUATION,
            range_start_bar_dt="2020-01-01",
            range_end_bar_dt=f"2020-01-{10+i}",
            span_bars=10+i,
            evolution_count=i,
            replacement_count=0,
            resolution_distance=100,
            resolution_distance_pct=0.05,
            amplitude_init=1000,
            amplitude_now=1000,
            amplitude_pct=0.1
        )
        lifespan_engine.record_resolved_range(lifespan)

    for i in range(2):
        lifespan = RangeLifespan(
            range_id=f"TEST_R{i+10}",
            symbol="TEST",
            timeframe="D",
            range_type=RangeResolutionType.REVERSAL,
            range_start_bar_dt="2020-01-01",
            range_end_bar_dt=f"2020-01-{20+i}",
            span_bars=20+i,
            evolution_count=i,
            replacement_count=0,
            resolution_distance=100,
            resolution_distance_pct=0.05,
            amplitude_init=1000,
            amplitude_now=1000,
            amplitude_pct=0.1
        )
        lifespan_engine.record_resolved_range(lifespan)

    # 获取 continuation peer_sample
    rank_engine = RankEngine()
    continuation_sample = rank_engine.filter_range_peer_sample(
        all_ranges=lifespan_engine.get_resolved_ranges(),
        range_type=RangeResolutionType.CONTINUATION
    )
    assert len(continuation_sample) == 3
    assert all(r.range_type == RangeResolutionType.CONTINUATION for r in continuation_sample)

    # 获取 reversal peer_sample
    reversal_sample = rank_engine.filter_range_peer_sample(
        all_ranges=lifespan_engine.get_resolved_ranges(),
        range_type=RangeResolutionType.REVERSAL
    )
    assert len(reversal_sample) == 2
    assert all(r.range_type == RangeResolutionType.REVERSAL for r in reversal_sample)


def test_range_peer_sample_anti_lookahead():
    """测试 peer_sample 防前视过滤。"""
    lifespan_engine = LifespanEngine()

    # 创建 5 个 Range，range_end_bar_dt 递增
    for i in range(5):
        lifespan = RangeLifespan(
            range_id=f"TEST_R{i}",
            symbol="TEST",
            timeframe="D",
            range_type=RangeResolutionType.CONTINUATION,
            range_start_bar_dt="2020-01-01",
            range_end_bar_dt=f"2020-01-{10+i*2:02d}",
            span_bars=10+i,
            evolution_count=i,
            replacement_count=0,
            resolution_distance=100,
            resolution_distance_pct=0.05,
            amplitude_init=1000,
            amplitude_now=1000,
            amplitude_pct=0.1
        )
        lifespan_engine.record_resolved_range(lifespan)

    # 当前 Range 的 range_start_bar_dt = "2020-01-15"
    # peer_sample 应该只包含 range_end_bar_dt <= "2020-01-15" 的 Range
    rank_engine = RankEngine()
    filtered = rank_engine.filter_range_peer_sample(
        all_ranges=lifespan_engine.get_resolved_ranges(),
        range_type=RangeResolutionType.CONTINUATION,
        cutoff_bar_dt="2020-01-15"
    )

    # 验证：只有 range_end_bar_dt <= "2020-01-15" 的 Range
    # R0: 2020-01-10 ✓
    # R1: 2020-01-12 ✓
    # R2: 2020-01-14 ✓
    # R3: 2020-01-16 ✗
    # R4: 2020-01-18 ✗
    assert len(filtered) == 3
    assert all(r.range_end_bar_dt <= "2020-01-15" for r in filtered)


def test_range_ranks_insufficient_sample():
    """测试样本不足时 rank 退化为 None（N < 30）。"""
    # 创建 20 个 Range（< 30）
    peer_sample = []
    for i in range(20):
        lifespan = RangeLifespan(
            range_id=f"TEST_R{i}",
            symbol="TEST",
            timeframe="D",
            range_type=RangeResolutionType.CONTINUATION,
            range_start_bar_dt="2020-01-01",
            range_end_bar_dt=f"2020-01-{10+i}",
            span_bars=10+i,
            evolution_count=i % 5,
            replacement_count=i % 3,
            resolution_distance=100,
            resolution_distance_pct=0.05,
            amplitude_init=1000,
            amplitude_now=1000,
            amplitude_pct=0.1
        )
        peer_sample.append(lifespan)

    # 当前 Range
    current_range = RangeLifespan(
        range_id="TEST_R_CURRENT",
        symbol="TEST",
        timeframe="D",
        range_type=RangeResolutionType.CONTINUATION,
        range_start_bar_dt="2020-02-01",
        range_end_bar_dt="2020-02-15",
        span_bars=15,
        evolution_count=3,
        replacement_count=2,
        resolution_distance=100,
        resolution_distance_pct=0.05,
        amplitude_init=1000,
        amplitude_now=1000,
        amplitude_pct=0.1
    )

    # 计算 rank（样本不足，应返回 None）
    rank_engine = RankEngine()
    ranks = rank_engine.calculate_range_ranks(current_range, peer_sample)

    assert ranks["span_rank"] is None
    assert ranks["evolution_rank"] is None
    assert ranks["replacement_rank"] is None
    assert ranks["resolution_distance_rank"] is None


def test_range_ranks_empty_sample():
    """测试空样本时 rank 返回 None。"""
    current_range = RangeLifespan(
        range_id="TEST_R_CURRENT",
        symbol="TEST",
        timeframe="D",
        range_type=RangeResolutionType.CONTINUATION,
        range_start_bar_dt="2020-02-01",
        range_end_bar_dt="2020-02-15",
        span_bars=15,
        evolution_count=3,
        replacement_count=2,
        resolution_distance=100,
        resolution_distance_pct=0.05,
        amplitude_init=1000,
        amplitude_now=1000,
        amplitude_pct=0.1
    )

    rank_engine = RankEngine()
    ranks = rank_engine.calculate_range_ranks(current_range, [])

    assert ranks["span_rank"] is None
    assert ranks["evolution_rank"] is None
    assert ranks["replacement_rank"] is None
    assert ranks["resolution_distance_rank"] is None
