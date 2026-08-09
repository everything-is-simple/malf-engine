"""
T9.15 测试：56 字段契约扩展（Wave 推进 + Range 演化 + Wave 身份）

背景（用户裁决 2026-08-10）：
- 44 字段投影丢弃了引擎内部已计算的丰富信息（progress_pct/new_count/no_new_span/
  progress_rank/birth_type/amplitude_*/resolution_distance_pct/wave_id/birth 时间）
- 方案 A：WaveStructuralSnapshot 44→56 字段（增列，不改语义）
- 处置 1：新字段排除出 lineage_hash（calculate_lineage_hash 已是字段子集哈希，
  新增字段不进入 hash_input —— 本测试断言该事实，防止回归）

测试场景：
1. 契约字段数 = 56（44 既有 + 12 新增）
2. 新字段默认值 None/False（dataclass 增列不破坏既有构造）
3. 组装函数透传新字段（Wave 推进 5 + Range 演化 4 + Wave 身份 3）
4. lineage_hash 不因新字段变化（排除出 hash_input）
5. 序列化/反序列化往返包含新字段
"""

import pytest
import json

from src.malf.types import WaveStructuralSnapshot, WaveLifespan, RangeLifespan
from src.malf.persistence import serialize_snapshot, deserialize_snapshot, calculate_lineage_hash
from src.malf.service_engine import build_wave_structural_snapshot
from src.malf.core_engine import MALFCoreEngine
from src.malf.types import CoreStateSnapshot


# ========== 场景 1：契约字段数 = 56 ==========

NEW_FIELDS = [
    # Wave 推进（5）
    "progress_pct", "new_count", "no_new_span", "progress_rank", "birth_type",
    # Range 演化（4）
    "range_amplitude_init", "range_amplitude_now", "range_amplitude_pct",
    "range_resolution_distance_pct",
    # Wave 身份（3）
    "wave_id", "wave_start_bar_dt", "wave_end_bar_dt",
]

LEGACY_FIELDS = [
    "symbol", "timeframe", "bar_dt", "bar_index",
    "system_state", "direction", "active_wave_id",
    "progress_extreme_price", "progress_extreme_bar_dt",
    "guard_price", "guard_bar_dt", "bar_count", "break_bar_dt", "break_price",
    "transition_boundary_high", "transition_boundary_low",
    "candidate_pivot_type", "candidate_pivot_price",
    "range_boundary_high_now", "range_boundary_low_now",
    "range_evolution_count", "range_candidate_replacement_count", "range_type",
    "wave_span_rank", "wave_range_rank", "wave_stagnation_rank",
    "range_span_rank", "range_evolution_rank", "range_replacement_rank",
    "range_resolution_distance_rank",
    "p2_same_dir_span_momentum", "p2_same_dir_range_momentum", "p2_same_dir_label",
    "p3_cross_dir_span_momentum", "p3_cross_dir_range_momentum", "p3_cross_dir_label",
    "p4_cross_span_momentum", "p4_cross_range_momentum", "p4_cross_alive_warning",
    "rule_versions", "lineage_hash", "reason_codes", "usage", "freshness",
]


def make_legacy_kwargs():
    """构造既有 44 字段的 kwargs（兼容旧测试构造风格）。"""
    return {
        "symbol": "TEST", "timeframe": "D1", "bar_dt": "2024-01-01", "bar_index": 0,
        "system_state": "UP_ALIVE", "direction": "UP", "active_wave_id": "wave_001",
        "progress_extreme_price": 115, "progress_extreme_bar_dt": "2024-01-01",
        "guard_price": 99, "guard_bar_dt": "2023-12-31", "bar_count": 5,
        "break_bar_dt": None, "break_price": None,
        "transition_boundary_high": None, "transition_boundary_low": None,
        "candidate_pivot_type": None, "candidate_pivot_price": None,
        "range_boundary_high_now": None, "range_boundary_low_now": None,
        "range_evolution_count": None, "range_candidate_replacement_count": None,
        "range_type": None,
        "wave_span_rank": 0.65, "wave_range_rank": 0.72, "wave_stagnation_rank": 0.45,
        "range_span_rank": None, "range_evolution_rank": None,
        "range_replacement_rank": None, "range_resolution_distance_rank": None,
        "p2_same_dir_span_momentum": 0.1, "p2_same_dir_range_momentum": 0.2,
        "p2_same_dir_label": "accelerating",
        "p3_cross_dir_span_momentum": -0.1, "p3_cross_dir_range_momentum": -0.2,
        "p3_cross_dir_label": "opposite_dominant",
        "p4_cross_span_momentum": 0.3, "p4_cross_range_momentum": 0.4,
        "p4_cross_alive_warning": False,
        "rule_versions": {"core_version": "v2.1", "range_version": "v2.1",
                          "lifespan_version": "v2.1", "structural_position_version": "v2.1",
                          "pivot_rule": "fractal_k2_v1.0",
                          "price_domain": "source_integer_fixed_point_v0.1",
                          "adapter": "malf-v2.0-etf-tick-v0.1"},
        "lineage_hash": "0" * 64,
        "reason_codes": [],
        "usage": "research_only",
        "freshness": "current",
    }


def test_contract_field_count_is_56():
    """场景 1：契约字段数必须为 56（44 既有 + 12 新增）。"""
    from dataclasses import fields
    all_fields = {f.name for f in fields(WaveStructuralSnapshot)}
    assert len(all_fields) == 56, f"期望 56 字段，实际 {len(all_fields)}: {sorted(all_fields)}"


def test_legacy_fields_preserved():
    """场景 1b：既有 44 字段全部保留，无删改。"""
    from dataclasses import fields
    all_fields = {f.name for f in fields(WaveStructuralSnapshot)}
    for f in LEGACY_FIELDS:
        assert f in all_fields, f"既有字段缺失: {f}"


def test_new_fields_present():
    """场景 1c：12 个新增字段全部存在。"""
    from dataclasses import fields
    all_fields = {f.name for f in fields(WaveStructuralSnapshot)}
    for f in NEW_FIELDS:
        assert f in all_fields, f"新增字段缺失: {f}"


# ========== 场景 2：新字段默认值（不破坏既有构造）==========

def test_new_fields_have_defaults():
    """场景 2：新字段必须有默认值（None/False），旧构造代码不传新字段也能工作。"""
    kwargs = make_legacy_kwargs()
    s = WaveStructuralSnapshot(**kwargs)  # 只传 44 个既有字段
    for f in NEW_FIELDS:
        assert getattr(s, f) is None or getattr(s, f) is False, \
            f"新字段 {f} 应有默认值，实际 {getattr(s, f)}"


# ========== 场景 3：组装函数透传新字段 ==========

class _FakeWaveLifespan:
    """模拟 WaveLifespan（避免构造完整对象，聚焦组装透传）。"""
    def __init__(self):
        self.span_rank = 0.90
        self.range_rank = 0.85
        self.stagnation_rank = 0.60
        self.progress_rank = 0.95
        self.progress_pct = 0.88
        self.new_count = 12
        self.no_new_span = 7
        self.span_bars = 45
        self.wave_id = "TEST_D1_w_001"
        self.wave_start_bar_dt = "2024-01-01"
        self.wave_end_bar_dt = "2024-02-01"


class _FakeRangeLifespan:
    def __init__(self):
        self.span_rank = 0.7
        self.evolution_rank = 0.6
        self.replacement_rank = 0.5
        self.resolution_distance_rank = 0.4
        self.amplitude_init = 100
        self.amplitude_now = 130
        self.amplitude_pct = 0.3
        self.resolution_distance_pct = 0.42
        self.span_bars = 20


def test_build_snapshot_passes_wave_progress_fields():
    """场景 3a：组装函数透传 Wave 推进字段。"""
    from src.malf.types import PriceBar, SystemState, Direction, WaveCoreState

    kwargs = make_legacy_kwargs()
    # 用最小 fake core（engine 需要真实 core，枚举值须用枚举类）
    core = CoreStateSnapshot(
        symbol="TEST", timeframe="D1", bar_dt="2024-01-01", bar_index=0,
        system_state=SystemState.UP_ALIVE, direction=Direction.UP, wave_core_state=None,
        active_wave_id="wave_001", active_wave=None, terminated_wave=None,
        active_range=None, resolved_range=None,
        current_effective_guard_price=99, current_effective_guard_extreme_bar_dt="2023-12-31",
        current_effective_guard_confirm_bar_dt=None,
        progress_extreme_price=115, progress_extreme_bar_dt="2024-01-01",
        bar_count=5, break_bar_dt=None, break_price=None,
        transition_boundary_high=None, transition_boundary_low=None,
        active_candidate_guard_price=None, active_candidate_guard_extreme_bar_dt=None,
        active_candidate_guard_confirm_bar_dt=None, active_candidate_direction=None,
        candidate_replacement_count=0, core_rule_version="v2.1",
        pivot_detection_rule_version="fractal_k2_v1.0", price_policy="source_integer_fixed_point",
        runtime_fingerprint="fp-test", schema_version="v2.1", note=None,
        range_id=None, range_birth_bar_dt=None,
        range_boundary_init_high=None, range_boundary_init_low=None,
        range_boundary_now_high=None, range_boundary_now_low=None,
        range_evolution_count=0, range_resolution_bar_dt=None,
        range_resolution_type=None, range_resolution_distance=None,
    )
    # 组装（用 fake lifespan 替换真实对象，验证透传逻辑）
    s = build_wave_structural_snapshot(
        symbol="TEST", timeframe="D1", bar_dt="2024-01-01", bar_index=0,
        core=core, active_range=None,
        wave_lifespan=_FakeWaveLifespan(),  # type: ignore[arg-type]
        range_lifespan=_FakeRangeLifespan(),  # type: ignore[arg-type]
        p1=None, p2=None, p3=None, p4=None,
        rule_versions=kwargs["rule_versions"],
        lineage_hash=kwargs["lineage_hash"],
    )
    # Wave 推进透传
    assert s.progress_pct == 0.88, "progress_pct 未透传"
    assert s.new_count == 12, "new_count 未透传"
    assert s.no_new_span == 7, "no_new_span 未透传"
    assert s.progress_rank == 0.95, "progress_rank 未透传"
    # Range 演化透传
    assert s.range_amplitude_init == 100, "range_amplitude_init 未透传"
    assert s.range_amplitude_now == 130, "range_amplitude_now 未透传"
    assert s.range_amplitude_pct == 0.3, "range_amplitude_pct 未透传"
    assert s.range_resolution_distance_pct == 0.42, "range_resolution_distance_pct 未透传"
    # 既有字段不破坏
    assert s.wave_span_rank == 0.90
    assert s.direction == "up"  # Direction.UP.value（枚举小写）


# ========== 场景 4：lineage_hash 不因新字段变化 ==========

def test_lineage_hash_ignores_new_fields():
    """场景 4：新增字段不进入 lineage_hash（处置 1，D5 先例）。"""
    # 构造同一快照，仅新字段不同 → hash 必须一致
    data = make_legacy_kwargs()
    base = {k: v for k, v in data.items()}
    h1 = calculate_lineage_hash(base)

    data2 = dict(data)
    data2["progress_pct"] = 0.99
    data2["new_count"] = 99
    data2["no_new_span"] = 99
    data2["progress_rank"] = 0.99
    data2["birth_type"] = "reversal"
    h2 = calculate_lineage_hash(data2)

    assert h1 == h2, "新字段进入 lineage_hash，违反处置 1（D5 先例）"


# ========== 场景 5：序列化/反序列化往返包含新字段 ==========

def test_serialization_roundtrip_includes_new_fields():
    """场景 5：新字段参与序列化往返，不丢失。"""
    kwargs = make_legacy_kwargs()
    kwargs.update({
        "progress_pct": 0.88, "new_count": 12, "no_new_span": 7,
        "progress_rank": 0.95, "birth_type": "continuation",
        "range_amplitude_init": 100, "range_amplitude_now": 130,
        "range_amplitude_pct": 0.3, "range_resolution_distance_pct": 0.42,
        "wave_id": "wave_001", "wave_start_bar_dt": "2024-01-01",
        "wave_end_bar_dt": "2024-01-01",
    })
    s = WaveStructuralSnapshot(**kwargs)
    js = serialize_snapshot(s)
    s2 = deserialize_snapshot(js)
    for f in NEW_FIELDS:
        assert getattr(s2, f) == getattr(s, f), f"往返丢失新字段: {f}"
