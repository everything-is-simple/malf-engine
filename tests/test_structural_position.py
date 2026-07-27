"""Structural Position 层测试（v2.1 Structural Position §3-§6）。

规格权威：MALF v2.1 Definitive (deepseek-20260726)
- 文档：MALF_04_Structural_Position_v2_1-deepseek-20260726.md
- 路径：I:\\asteria-riskbench-Definitive-validated\\MALF_Definitive_v2_1-deepseek-20260726\\

测试覆盖：
- T8.1: P1 自身分位（透传 rank）
- T8.2: P2 同向对照（same direction momentum）
- T8.3: P3 反向对照（opposite direction momentum）
- T8.4: P4 正反对照（cross compare）

验证不变量：
- P1: P1 是 Lifespan rank 的透传，不做变换
- P2: P2/P3/P4 的 momentum 是 rank 的向量差，不是概率
- P3: 标签（accelerating 等）是辅助性的，rank 值始终保留
- P4: P4 的 cross_alive_warning 必须真实反映当前 wave 的 alive 状态
- P5: 所有 rank 为 None 时，不 fallback、不补零、不估计
"""

import json
import pytest
from pathlib import Path

from malf.types import WaveLifespan, Direction, P1SelfRank
from malf.structural_position_engine import StructuralPositionEngine


# ============================================================================
# Fixture 加载工具
# ============================================================================

def load_fixture(filename: str) -> dict:
    """从 tests/fixtures/ 加载 JSON fixture。"""
    fixture_path = Path(__file__).parent / "fixtures" / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# T8.1: P1 自身分位（透传 rank）
# ============================================================================

def test_p1_no_ranks():
    """T8.1-1: P1 透传 None（peer_sample 不足时）。

    验证不变量：
    - P5: 所有 rank 为 None 时，不 fallback、不补零、不估计
    - P1: P1 是 Lifespan rank 的透传，不做变换
    """
    fixture = load_fixture("t8_1_p1_no_ranks.json")
    input_data = fixture["input"]["wave_lifespan"]
    expected = fixture["expected_output"]["p1_self_rank"]

    # 构造 WaveLifespan 对象
    wave_lifespan = WaveLifespan(
        wave_id=input_data["wave_id"],
        symbol=input_data["symbol"],
        timeframe=input_data["timeframe"],
        direction=Direction(input_data["direction"]),
        wave_start_bar_dt=input_data["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["wave_end_bar_dt"],
        span_bars=input_data["span_bars"],
        wave_start_price=input_data["wave_start_price"],
        wave_end_price=input_data["wave_end_price"],
        price_range=input_data["price_range"],
        progress_pct=input_data["progress_pct"],
        primitive_count=input_data["primitive_count"],
        pivot_count=input_data["pivot_count"],
        new_count=input_data["new_count"],
        no_new_span=input_data["no_new_span"],
        span_rank=input_data["span_rank"],
        range_rank=input_data["range_rank"],
        stagnation_rank=input_data["stagnation_rank"],
        progress_rank=input_data["progress_rank"]
    )

    # 调用 P1 视图生成
    engine = StructuralPositionEngine()
    p1 = engine.build_p1_view(wave_lifespan)

    # 验证：所有 rank 为 None
    assert p1.span_rank is None, "span_rank 应为 None"
    assert p1.range_rank is None, "range_rank 应为 None"
    assert p1.stagnation_rank is None, "stagnation_rank 应为 None"
    assert p1.progress_rank is None, "progress_rank 应为 None"

    # 验证与 fixture 预期一致
    assert p1.span_rank == expected["span_rank"]
    assert p1.range_rank == expected["range_rank"]
    assert p1.stagnation_rank == expected["stagnation_rank"]
    assert p1.progress_rank == expected["progress_rank"]


def test_p1_with_ranks():
    """T8.1-2: P1 透传完整 rank 值（peer_sample >= 30）。

    验证不变量：
    - P1: P1 是 Lifespan rank 的透传，不做变换
    """
    fixture = load_fixture("t8_1_p1_with_ranks.json")
    input_data = fixture["input"]["wave_lifespan"]
    expected = fixture["expected_output"]["p1_self_rank"]

    # 构造 WaveLifespan 对象
    wave_lifespan = WaveLifespan(
        wave_id=input_data["wave_id"],
        symbol=input_data["symbol"],
        timeframe=input_data["timeframe"],
        direction=Direction(input_data["direction"]),
        wave_start_bar_dt=input_data["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["wave_end_bar_dt"],
        span_bars=input_data["span_bars"],
        wave_start_price=input_data["wave_start_price"],
        wave_end_price=input_data["wave_end_price"],
        price_range=input_data["price_range"],
        progress_pct=input_data["progress_pct"],
        primitive_count=input_data["primitive_count"],
        pivot_count=input_data["pivot_count"],
        new_count=input_data["new_count"],
        no_new_span=input_data["no_new_span"],
        span_rank=input_data["span_rank"],
        range_rank=input_data["range_rank"],
        stagnation_rank=input_data["stagnation_rank"],
        progress_rank=input_data["progress_rank"]
    )

    # 调用 P1 视图生成
    engine = StructuralPositionEngine()
    p1 = engine.build_p1_view(wave_lifespan)

    # 验证：rank 值完全透传
    assert p1.span_rank == input_data["span_rank"], "span_rank 应透传输入值"
    assert p1.range_rank == input_data["range_rank"], "range_rank 应透传输入值"
    assert p1.stagnation_rank == input_data["stagnation_rank"], "stagnation_rank 应透传输入值"
    assert p1.progress_rank == input_data["progress_rank"], "progress_rank 应透传输入值"

    # 验证与 fixture 预期一致
    assert p1.span_rank == expected["span_rank"]
    assert p1.range_rank == expected["range_rank"]
    assert p1.stagnation_rank == expected["stagnation_rank"]
    assert p1.progress_rank == expected["progress_rank"]


def test_p1_invariant_no_transformation():
    """T8.1-3: P1 不变量验证 - 不做任何变换。

    验证不变量：
    - P1: P1 是 Lifespan rank 的透传，不做变换

    边界情况：rank 值为 0.0, 0.99
    """
    # 边界情况 1：rank = 0.0（最低）
    wave_lifespan_min = WaveLifespan(
        wave_id="TEST_1min_w_min",
        symbol="TEST",
        timeframe="1min",
        direction=Direction.UP,
        wave_start_bar_dt="2026-01-01T09:00:00",
        wave_end_bar_dt="2026-01-01T09:05:00",
        span_bars=5,
        wave_start_price=10000,
        wave_end_price=10100,
        price_range=100,
        progress_pct=0.01,
        primitive_count=3,
        pivot_count=3,
        new_count=0,
        no_new_span=5,
        span_rank=0.0,
        range_rank=0.0,
        stagnation_rank=0.0,
        progress_rank=0.0
    )

    engine = StructuralPositionEngine()
    p1_min = engine.build_p1_view(wave_lifespan_min)

    assert p1_min.span_rank == 0.0
    assert p1_min.range_rank == 0.0
    assert p1_min.stagnation_rank == 0.0
    assert p1_min.progress_rank == 0.0

    # 边界情况 2：rank = 0.99（最高）
    wave_lifespan_max = WaveLifespan(
        wave_id="TEST_1min_w_max",
        symbol="TEST",
        timeframe="1min",
        direction=Direction.DOWN,
        wave_start_bar_dt="2026-01-01T10:00:00",
        wave_end_bar_dt="2026-01-01T10:30:00",
        span_bars=30,
        wave_start_price=10000,
        wave_end_price=9000,
        price_range=1000,
        progress_pct=-0.10,
        primitive_count=3,
        pivot_count=15,
        new_count=12,
        no_new_span=2,
        span_rank=0.99,
        range_rank=0.99,
        stagnation_rank=0.99,
        progress_rank=0.99
    )

    p1_max = engine.build_p1_view(wave_lifespan_max)

    assert p1_max.span_rank == 0.99
    assert p1_max.range_rank == 0.99
    assert p1_max.stagnation_rank == 0.99
    assert p1_max.progress_rank == 0.99


# ============================================================================
# T8.2: P2 同向对照（Same Direction Momentum）
# ============================================================================

def test_p2_sufficient_same_dir_peers():
    """T8.2-1: P2 充足同向波（≥ 1 个）。

    验证不变量：
    - P2: momentum 是 rank 的向量差，不是概率
    - P3: 标签是辅助性的，原始 rank 值始终保留
    """
    fixture = load_fixture("t8_2_p2_sufficient_peers.json")
    input_data = fixture["input"]
    expected = fixture["expected_output"]["p2_same_dir_momentum"]

    # 构造当前 wave
    current_wave = WaveLifespan(
        wave_id=input_data["current_wave"]["wave_id"],
        symbol=input_data["current_wave"]["symbol"],
        timeframe=input_data["current_wave"]["timeframe"],
        direction=Direction(input_data["current_wave"]["direction"]),
        wave_start_bar_dt=input_data["current_wave"]["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["current_wave"]["wave_end_bar_dt"],
        span_bars=input_data["current_wave"]["span_bars"],
        wave_start_price=input_data["current_wave"]["wave_start_price"],
        wave_end_price=input_data["current_wave"]["wave_end_price"],
        price_range=input_data["current_wave"]["price_range"],
        progress_pct=input_data["current_wave"]["progress_pct"],
        primitive_count=input_data["current_wave"]["primitive_count"],
        pivot_count=input_data["current_wave"]["pivot_count"],
        new_count=input_data["current_wave"]["new_count"],
        no_new_span=input_data["current_wave"]["no_new_span"],
        span_rank=input_data["current_wave"]["span_rank"],
        range_rank=input_data["current_wave"]["range_rank"],
        stagnation_rank=input_data["current_wave"]["stagnation_rank"],
        progress_rank=input_data["current_wave"]["progress_rank"]
    )

    # 构造已终止波列表
    terminated_waves = []
    for w_data in input_data["terminated_waves"]:
        terminated_waves.append(WaveLifespan(
            wave_id=w_data["wave_id"],
            symbol="TEST",
            timeframe="1min",
            direction=Direction(w_data["direction"]),
            wave_start_bar_dt=w_data["wave_end_bar_dt"],  # 简化
            wave_end_bar_dt=w_data["wave_end_bar_dt"],
            span_bars=10,  # 简化
            wave_start_price=10000,
            wave_end_price=10100,
            price_range=100,
            progress_pct=0.01,
            primitive_count=3,
            pivot_count=5,
            new_count=2,
            no_new_span=2,
            span_rank=w_data["span_rank"],
            range_rank=w_data["range_rank"],
            stagnation_rank=w_data["stagnation_rank"],
            progress_rank=None
        ))

    # 调用 P2 视图生成
    engine = StructuralPositionEngine()
    p2 = engine.build_p2_view(current_wave, terminated_waves)

    # 验证 momentum 值（允许浮点误差）
    assert p2.same_dir_span_momentum is not None
    assert abs(p2.same_dir_span_momentum - expected["same_dir_span_momentum"]) < 0.01
    assert abs(p2.same_dir_range_momentum - expected["same_dir_range_momentum"]) < 0.01
    assert abs(p2.same_dir_stagnation_momentum - expected["same_dir_stagnation_momentum"]) < 0.01

    # 验证标签
    assert p2.same_dir_label == expected["same_dir_label"]


def test_p2_insufficient_same_dir_peers():
    """T8.2-2: P2 不足同向波（1 个）。

    验证不变量：
    - P2: 有几个同向波用几个，不要求必须 3 个
    """
    fixture = load_fixture("t8_2_p2_insufficient_peers.json")
    input_data = fixture["input"]
    expected = fixture["expected_output"]["p2_same_dir_momentum"]

    # 构造当前 wave
    current_wave = WaveLifespan(
        wave_id=input_data["current_wave"]["wave_id"],
        symbol=input_data["current_wave"]["symbol"],
        timeframe=input_data["current_wave"]["timeframe"],
        direction=Direction(input_data["current_wave"]["direction"]),
        wave_start_bar_dt=input_data["current_wave"]["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["current_wave"]["wave_end_bar_dt"],
        span_bars=input_data["current_wave"]["span_bars"],
        wave_start_price=input_data["current_wave"]["wave_start_price"],
        wave_end_price=input_data["current_wave"]["wave_end_price"],
        price_range=input_data["current_wave"]["price_range"],
        progress_pct=input_data["current_wave"]["progress_pct"],
        primitive_count=input_data["current_wave"]["primitive_count"],
        pivot_count=input_data["current_wave"]["pivot_count"],
        new_count=input_data["current_wave"]["new_count"],
        no_new_span=input_data["current_wave"]["no_new_span"],
        span_rank=input_data["current_wave"]["span_rank"],
        range_rank=input_data["current_wave"]["range_rank"],
        stagnation_rank=input_data["current_wave"]["stagnation_rank"],
        progress_rank=input_data["current_wave"]["progress_rank"]
    )

    # 构造已终止波列表
    terminated_waves = []
    for w_data in input_data["terminated_waves"]:
        terminated_waves.append(WaveLifespan(
            wave_id=w_data["wave_id"],
            symbol="TEST",
            timeframe="1min",
            direction=Direction(w_data["direction"]),
            wave_start_bar_dt=w_data["wave_end_bar_dt"],
            wave_end_bar_dt=w_data["wave_end_bar_dt"],
            span_bars=10,
            wave_start_price=10000,
            wave_end_price=10100,
            price_range=100,
            progress_pct=0.01,
            primitive_count=3,
            pivot_count=5,
            new_count=2,
            no_new_span=2,
            span_rank=w_data["span_rank"],
            range_rank=w_data["range_rank"],
            stagnation_rank=w_data["stagnation_rank"],
            progress_rank=None
        ))

    # 调用 P2 视图生成
    engine = StructuralPositionEngine()
    p2 = engine.build_p2_view(current_wave, terminated_waves)

    # 验证 momentum 值
    assert abs(p2.same_dir_span_momentum - expected["same_dir_span_momentum"]) < 0.01
    assert abs(p2.same_dir_range_momentum - expected["same_dir_range_momentum"]) < 0.01
    assert abs(p2.same_dir_stagnation_momentum - expected["same_dir_stagnation_momentum"]) < 0.01

    # 验证标签
    assert p2.same_dir_label == expected["same_dir_label"]


def test_p2_no_same_dir_peers():
    """T8.2-3: P2 无同向波。

    验证不变量：
    - P5: peer_waves 为空时，不 fallback、不补零、不估计
    """
    fixture = load_fixture("t8_2_p2_no_peers.json")
    input_data = fixture["input"]
    expected = fixture["expected_output"]["p2_same_dir_momentum"]

    # 构造当前 wave
    current_wave = WaveLifespan(
        wave_id=input_data["current_wave"]["wave_id"],
        symbol=input_data["current_wave"]["symbol"],
        timeframe=input_data["current_wave"]["timeframe"],
        direction=Direction(input_data["current_wave"]["direction"]),
        wave_start_bar_dt=input_data["current_wave"]["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["current_wave"]["wave_end_bar_dt"],
        span_bars=input_data["current_wave"]["span_bars"],
        wave_start_price=input_data["current_wave"]["wave_start_price"],
        wave_end_price=input_data["current_wave"]["wave_end_price"],
        price_range=input_data["current_wave"]["price_range"],
        progress_pct=input_data["current_wave"]["progress_pct"],
        primitive_count=input_data["current_wave"]["primitive_count"],
        pivot_count=input_data["current_wave"]["pivot_count"],
        new_count=input_data["current_wave"]["new_count"],
        no_new_span=input_data["current_wave"]["no_new_span"],
        span_rank=input_data["current_wave"]["span_rank"],
        range_rank=input_data["current_wave"]["range_rank"],
        stagnation_rank=input_data["current_wave"]["stagnation_rank"],
        progress_rank=input_data["current_wave"]["progress_rank"]
    )

    # 构造已终止波列表（全是反向波）
    terminated_waves = []
    for w_data in input_data["terminated_waves"]:
        terminated_waves.append(WaveLifespan(
            wave_id=w_data["wave_id"],
            symbol="TEST",
            timeframe="1min",
            direction=Direction(w_data["direction"]),
            wave_start_bar_dt=w_data["wave_end_bar_dt"],
            wave_end_bar_dt=w_data["wave_end_bar_dt"],
            span_bars=10,
            wave_start_price=10000,
            wave_end_price=10100,
            price_range=100,
            progress_pct=0.01,
            primitive_count=3,
            pivot_count=5,
            new_count=2,
            no_new_span=2,
            span_rank=w_data["span_rank"],
            range_rank=w_data["range_rank"],
            stagnation_rank=w_data["stagnation_rank"],
            progress_rank=None
        ))

    # 调用 P2 视图生成
    engine = StructuralPositionEngine()
    p2 = engine.build_p2_view(current_wave, terminated_waves)

    # 验证：所有字段为 None
    assert p2.same_dir_span_momentum is None
    assert p2.same_dir_range_momentum is None
    assert p2.same_dir_stagnation_momentum is None
    assert p2.same_dir_label is None

    # 验证与 fixture 预期一致
    assert p2.same_dir_span_momentum == expected["same_dir_span_momentum"]
    assert p2.same_dir_range_momentum == expected["same_dir_range_momentum"]
    assert p2.same_dir_stagnation_momentum == expected["same_dir_stagnation_momentum"]
    assert p2.same_dir_label == expected["same_dir_label"]


# ============================================================================
# T8.3: P3 反向对照（Opposite Direction Momentum）
# ============================================================================

def test_p3_sufficient_cross_dir_peers():
    """T8.3-1: P3 充足反向波（≥ 1 个）。

    验证不变量：
    - P2: momentum 是 rank 的向量差，不是概率
    - P3: 标签是辅助性的，原始 rank 值始终保留
    """
    fixture = load_fixture("t8_3_p3_sufficient_peers.json")
    input_data = fixture["input"]
    expected = fixture["expected_output"]["p3_cross_dir_momentum"]

    # 构造当前 wave
    current_wave = WaveLifespan(
        wave_id=input_data["current_wave"]["wave_id"],
        symbol=input_data["current_wave"]["symbol"],
        timeframe=input_data["current_wave"]["timeframe"],
        direction=Direction(input_data["current_wave"]["direction"]),
        wave_start_bar_dt=input_data["current_wave"]["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["current_wave"]["wave_end_bar_dt"],
        span_bars=input_data["current_wave"]["span_bars"],
        wave_start_price=input_data["current_wave"]["wave_start_price"],
        wave_end_price=input_data["current_wave"]["wave_end_price"],
        price_range=input_data["current_wave"]["price_range"],
        progress_pct=input_data["current_wave"]["progress_pct"],
        primitive_count=input_data["current_wave"]["primitive_count"],
        pivot_count=input_data["current_wave"]["pivot_count"],
        new_count=input_data["current_wave"]["new_count"],
        no_new_span=input_data["current_wave"]["no_new_span"],
        span_rank=input_data["current_wave"]["span_rank"],
        range_rank=input_data["current_wave"]["range_rank"],
        stagnation_rank=input_data["current_wave"]["stagnation_rank"],
        progress_rank=input_data["current_wave"]["progress_rank"]
    )

    # 构造已终止波列表
    terminated_waves = []
    for w_data in input_data["terminated_waves"]:
        terminated_waves.append(WaveLifespan(
            wave_id=w_data["wave_id"],
            symbol="TEST",
            timeframe="1min",
            direction=Direction(w_data["direction"]),
            wave_start_bar_dt=w_data["wave_end_bar_dt"],
            wave_end_bar_dt=w_data["wave_end_bar_dt"],
            span_bars=10,
            wave_start_price=10000,
            wave_end_price=10100,
            price_range=100,
            progress_pct=0.01,
            primitive_count=3,
            pivot_count=5,
            new_count=2,
            no_new_span=2,
            span_rank=w_data["span_rank"],
            range_rank=w_data["range_rank"],
            stagnation_rank=w_data["stagnation_rank"],
            progress_rank=None
        ))

    # 调用 P3 视图生成
    engine = StructuralPositionEngine()
    p3 = engine.build_p3_view(current_wave, terminated_waves)

    # 验证 momentum 值（允许浮点误差）
    assert p3.cross_dir_span_momentum is not None
    assert abs(p3.cross_dir_span_momentum - expected["cross_dir_span_momentum"]) < 0.01
    assert abs(p3.cross_dir_range_momentum - expected["cross_dir_range_momentum"]) < 0.01
    assert abs(p3.cross_dir_stagnation_momentum - expected["cross_dir_stagnation_momentum"]) < 0.01

    # 验证标签
    assert p3.cross_dir_label == expected["cross_dir_label"]


def test_p3_insufficient_cross_dir_peers():
    """T8.3-2: P3 不足反向波（1 个）。

    验证不变量：
    - P2: 有几个反向波用几个，不要求必须 3 个
    """
    fixture = load_fixture("t8_3_p3_insufficient_peers.json")
    input_data = fixture["input"]
    expected = fixture["expected_output"]["p3_cross_dir_momentum"]

    # 构造当前 wave
    current_wave = WaveLifespan(
        wave_id=input_data["current_wave"]["wave_id"],
        symbol=input_data["current_wave"]["symbol"],
        timeframe=input_data["current_wave"]["timeframe"],
        direction=Direction(input_data["current_wave"]["direction"]),
        wave_start_bar_dt=input_data["current_wave"]["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["current_wave"]["wave_end_bar_dt"],
        span_bars=input_data["current_wave"]["span_bars"],
        wave_start_price=input_data["current_wave"]["wave_start_price"],
        wave_end_price=input_data["current_wave"]["wave_end_price"],
        price_range=input_data["current_wave"]["price_range"],
        progress_pct=input_data["current_wave"]["progress_pct"],
        primitive_count=input_data["current_wave"]["primitive_count"],
        pivot_count=input_data["current_wave"]["pivot_count"],
        new_count=input_data["current_wave"]["new_count"],
        no_new_span=input_data["current_wave"]["no_new_span"],
        span_rank=input_data["current_wave"]["span_rank"],
        range_rank=input_data["current_wave"]["range_rank"],
        stagnation_rank=input_data["current_wave"]["stagnation_rank"],
        progress_rank=input_data["current_wave"]["progress_rank"]
    )

    # 构造已终止波列表
    terminated_waves = []
    for w_data in input_data["terminated_waves"]:
        terminated_waves.append(WaveLifespan(
            wave_id=w_data["wave_id"],
            symbol="TEST",
            timeframe="1min",
            direction=Direction(w_data["direction"]),
            wave_start_bar_dt=w_data["wave_end_bar_dt"],
            wave_end_bar_dt=w_data["wave_end_bar_dt"],
            span_bars=10,
            wave_start_price=10000,
            wave_end_price=10100,
            price_range=100,
            progress_pct=0.01,
            primitive_count=3,
            pivot_count=5,
            new_count=2,
            no_new_span=2,
            span_rank=w_data["span_rank"],
            range_rank=w_data["range_rank"],
            stagnation_rank=w_data["stagnation_rank"],
            progress_rank=None
        ))

    # 调用 P3 视图生成
    engine = StructuralPositionEngine()
    p3 = engine.build_p3_view(current_wave, terminated_waves)

    # 验证 momentum 值
    assert abs(p3.cross_dir_span_momentum - expected["cross_dir_span_momentum"]) < 0.01
    assert abs(p3.cross_dir_range_momentum - expected["cross_dir_range_momentum"]) < 0.01
    assert abs(p3.cross_dir_stagnation_momentum - expected["cross_dir_stagnation_momentum"]) < 0.01

    # 验证标签
    assert p3.cross_dir_label == expected["cross_dir_label"]


def test_p3_no_cross_dir_peers():
    """T8.3-3: P3 无反向波。

    验证不变量：
    - P5: peer_waves 为空时，不 fallback、不补零、不估计
    """
    fixture = load_fixture("t8_3_p3_no_peers.json")
    input_data = fixture["input"]
    expected = fixture["expected_output"]["p3_cross_dir_momentum"]

    # 构造当前 wave
    current_wave = WaveLifespan(
        wave_id=input_data["current_wave"]["wave_id"],
        symbol=input_data["current_wave"]["symbol"],
        timeframe=input_data["current_wave"]["timeframe"],
        direction=Direction(input_data["current_wave"]["direction"]),
        wave_start_bar_dt=input_data["current_wave"]["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["current_wave"]["wave_end_bar_dt"],
        span_bars=input_data["current_wave"]["span_bars"],
        wave_start_price=input_data["current_wave"]["wave_start_price"],
        wave_end_price=input_data["current_wave"]["wave_end_price"],
        price_range=input_data["current_wave"]["price_range"],
        progress_pct=input_data["current_wave"]["progress_pct"],
        primitive_count=input_data["current_wave"]["primitive_count"],
        pivot_count=input_data["current_wave"]["pivot_count"],
        new_count=input_data["current_wave"]["new_count"],
        no_new_span=input_data["current_wave"]["no_new_span"],
        span_rank=input_data["current_wave"]["span_rank"],
        range_rank=input_data["current_wave"]["range_rank"],
        stagnation_rank=input_data["current_wave"]["stagnation_rank"],
        progress_rank=input_data["current_wave"]["progress_rank"]
    )

    # 构造已终止波列表（全是同向波）
    terminated_waves = []
    for w_data in input_data["terminated_waves"]:
        terminated_waves.append(WaveLifespan(
            wave_id=w_data["wave_id"],
            symbol="TEST",
            timeframe="1min",
            direction=Direction(w_data["direction"]),
            wave_start_bar_dt=w_data["wave_end_bar_dt"],
            wave_end_bar_dt=w_data["wave_end_bar_dt"],
            span_bars=10,
            wave_start_price=10000,
            wave_end_price=10100,
            price_range=100,
            progress_pct=0.01,
            primitive_count=3,
            pivot_count=5,
            new_count=2,
            no_new_span=2,
            span_rank=w_data["span_rank"],
            range_rank=w_data["range_rank"],
            stagnation_rank=w_data["stagnation_rank"],
            progress_rank=None
        ))

    # 调用 P3 视图生成
    engine = StructuralPositionEngine()
    p3 = engine.build_p3_view(current_wave, terminated_waves)

    # 验证：所有字段为 None
    assert p3.cross_dir_span_momentum is None
    assert p3.cross_dir_range_momentum is None
    assert p3.cross_dir_stagnation_momentum is None
    assert p3.cross_dir_label is None

    # 验证与 fixture 预期一致
    assert p3.cross_dir_span_momentum == expected["cross_dir_span_momentum"]
    assert p3.cross_dir_range_momentum == expected["cross_dir_range_momentum"]
    assert p3.cross_dir_stagnation_momentum == expected["cross_dir_stagnation_momentum"]
    assert p3.cross_dir_label == expected["cross_dir_label"]


# ============================================================================
# T8.4: P4 正反对照（Cross Compare）
# ============================================================================

def test_p4_with_w_minus_1():
    """T8.4-1: P4 W-1 存在且已终止。

    验证不变量：
    - P2: momentum 是 rank 的向量差，不是概率
    - P4: cross_alive_warning 必须真实反映当前 wave 的 alive 状态
    """
    fixture = load_fixture("t8_4_p4_with_w_minus_1.json")
    input_data = fixture["input"]
    expected = fixture["expected_output"]["p4_cross_compare"]

    # 构造当前 wave
    current_wave = WaveLifespan(
        wave_id=input_data["current_wave"]["wave_id"],
        symbol=input_data["current_wave"]["symbol"],
        timeframe=input_data["current_wave"]["timeframe"],
        direction=Direction(input_data["current_wave"]["direction"]),
        wave_start_bar_dt=input_data["current_wave"]["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["current_wave"]["wave_end_bar_dt"],
        span_bars=input_data["current_wave"]["span_bars"],
        wave_start_price=input_data["current_wave"]["wave_start_price"],
        wave_end_price=input_data["current_wave"]["wave_end_price"],
        price_range=input_data["current_wave"]["price_range"],
        progress_pct=input_data["current_wave"]["progress_pct"],
        primitive_count=input_data["current_wave"]["primitive_count"],
        pivot_count=input_data["current_wave"]["pivot_count"],
        new_count=input_data["current_wave"]["new_count"],
        no_new_span=input_data["current_wave"]["no_new_span"],
        span_rank=input_data["current_wave"]["span_rank"],
        range_rank=input_data["current_wave"]["range_rank"],
        stagnation_rank=input_data["current_wave"]["stagnation_rank"],
        progress_rank=input_data["current_wave"]["progress_rank"]
    )

    # 构造 W-1
    w_minus_1_data = input_data["w_minus_1"]
    w_minus_1 = WaveLifespan(
        wave_id=w_minus_1_data["wave_id"],
        symbol="TEST",
        timeframe="1min",
        direction=Direction(w_minus_1_data["direction"]),
        wave_start_bar_dt=w_minus_1_data["wave_end_bar_dt"],
        wave_end_bar_dt=w_minus_1_data["wave_end_bar_dt"],
        span_bars=10,
        wave_start_price=10000,
        wave_end_price=10100,
        price_range=100,
        progress_pct=0.01,
        primitive_count=3,
        pivot_count=5,
        new_count=2,
        no_new_span=2,
        span_rank=w_minus_1_data["span_rank"],
        range_rank=w_minus_1_data["range_rank"],
        stagnation_rank=w_minus_1_data["stagnation_rank"],
        progress_rank=None
    )

    # 调用 P4 视图生成
    engine = StructuralPositionEngine()
    p4 = engine.build_p4_view(current_wave, w_minus_1, input_data["current_wave_is_alive"])

    # 验证 momentum 值（允许浮点误差）
    assert p4.cross_span_momentum is not None
    assert abs(p4.cross_span_momentum - expected["cross_span_momentum"]) < 0.01
    assert abs(p4.cross_range_momentum - expected["cross_range_momentum"]) < 0.01
    assert abs(p4.cross_stagnation_momentum - expected["cross_stagnation_momentum"]) < 0.01

    # 验证 cross_alive_warning
    assert p4.cross_alive_warning == expected["cross_alive_warning"]


def test_p4_no_w_minus_1():
    """T8.4-2: P4 W-1 不存在（第一个 wave）。

    验证不变量：
    - P5: W-1 不存在时，不 fallback、不补零、不估计
    """
    fixture = load_fixture("t8_4_p4_no_w_minus_1.json")
    input_data = fixture["input"]
    expected = fixture["expected_output"]["p4_cross_compare"]

    # 构造当前 wave
    current_wave = WaveLifespan(
        wave_id=input_data["current_wave"]["wave_id"],
        symbol=input_data["current_wave"]["symbol"],
        timeframe=input_data["current_wave"]["timeframe"],
        direction=Direction(input_data["current_wave"]["direction"]),
        wave_start_bar_dt=input_data["current_wave"]["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["current_wave"]["wave_end_bar_dt"],
        span_bars=input_data["current_wave"]["span_bars"],
        wave_start_price=input_data["current_wave"]["wave_start_price"],
        wave_end_price=input_data["current_wave"]["wave_end_price"],
        price_range=input_data["current_wave"]["price_range"],
        progress_pct=input_data["current_wave"]["progress_pct"],
        primitive_count=input_data["current_wave"]["primitive_count"],
        pivot_count=input_data["current_wave"]["pivot_count"],
        new_count=input_data["current_wave"]["new_count"],
        no_new_span=input_data["current_wave"]["no_new_span"],
        span_rank=input_data["current_wave"]["span_rank"],
        range_rank=input_data["current_wave"]["range_rank"],
        stagnation_rank=input_data["current_wave"]["stagnation_rank"],
        progress_rank=input_data["current_wave"]["progress_rank"]
    )

    # W-1 不存在
    w_minus_1 = None

    # 调用 P4 视图生成
    engine = StructuralPositionEngine()
    p4 = engine.build_p4_view(current_wave, w_minus_1, input_data["current_wave_is_alive"])

    # 验证：所有 momentum 为 None
    assert p4.cross_span_momentum is None
    assert p4.cross_range_momentum is None
    assert p4.cross_stagnation_momentum is None

    # 验证 cross_alive_warning
    assert p4.cross_alive_warning == expected["cross_alive_warning"]

    # 验证与 fixture 预期一致
    assert p4.cross_span_momentum == expected["cross_span_momentum"]
    assert p4.cross_range_momentum == expected["cross_range_momentum"]
    assert p4.cross_stagnation_momentum == expected["cross_stagnation_momentum"]


def test_p4_w0_alive():
    """T8.4-3: P4 W0 为 alive（cross_alive_warning = True）。

    验证不变量：
    - P4: cross_alive_warning 必须真实反映当前 wave 的 alive 状态
    """
    fixture = load_fixture("t8_4_p4_w0_alive.json")
    input_data = fixture["input"]
    expected = fixture["expected_output"]["p4_cross_compare"]

    # 构造当前 wave
    current_wave = WaveLifespan(
        wave_id=input_data["current_wave"]["wave_id"],
        symbol=input_data["current_wave"]["symbol"],
        timeframe=input_data["current_wave"]["timeframe"],
        direction=Direction(input_data["current_wave"]["direction"]),
        wave_start_bar_dt=input_data["current_wave"]["wave_start_bar_dt"],
        wave_end_bar_dt=input_data["current_wave"]["wave_end_bar_dt"],
        span_bars=input_data["current_wave"]["span_bars"],
        wave_start_price=input_data["current_wave"]["wave_start_price"],
        wave_end_price=input_data["current_wave"]["wave_end_price"],
        price_range=input_data["current_wave"]["price_range"],
        progress_pct=input_data["current_wave"]["progress_pct"],
        primitive_count=input_data["current_wave"]["primitive_count"],
        pivot_count=input_data["current_wave"]["pivot_count"],
        new_count=input_data["current_wave"]["new_count"],
        no_new_span=input_data["current_wave"]["no_new_span"],
        span_rank=input_data["current_wave"]["span_rank"],
        range_rank=input_data["current_wave"]["range_rank"],
        stagnation_rank=input_data["current_wave"]["stagnation_rank"],
        progress_rank=input_data["current_wave"]["progress_rank"]
    )

    # 构造 W-1
    w_minus_1_data = input_data["w_minus_1"]
    w_minus_1 = WaveLifespan(
        wave_id=w_minus_1_data["wave_id"],
        symbol="TEST",
        timeframe="1min",
        direction=Direction(w_minus_1_data["direction"]),
        wave_start_bar_dt=w_minus_1_data["wave_end_bar_dt"],
        wave_end_bar_dt=w_minus_1_data["wave_end_bar_dt"],
        span_bars=10,
        wave_start_price=10000,
        wave_end_price=10100,
        price_range=100,
        progress_pct=0.01,
        primitive_count=3,
        pivot_count=5,
        new_count=2,
        no_new_span=2,
        span_rank=w_minus_1_data["span_rank"],
        range_rank=w_minus_1_data["range_rank"],
        stagnation_rank=w_minus_1_data["stagnation_rank"],
        progress_rank=None
    )

    # 调用 P4 视图生成
    engine = StructuralPositionEngine()
    p4 = engine.build_p4_view(current_wave, w_minus_1, input_data["current_wave_is_alive"])

    # 验证 momentum 值
    assert abs(p4.cross_span_momentum - expected["cross_span_momentum"]) < 0.01
    assert abs(p4.cross_range_momentum - expected["cross_range_momentum"]) < 0.01
    assert abs(p4.cross_stagnation_momentum - expected["cross_stagnation_momentum"]) < 0.01

    # 验证 cross_alive_warning（关键：必须为 True）
    assert p4.cross_alive_warning == True
    assert p4.cross_alive_warning == expected["cross_alive_warning"]
