"""
测试 Service 层 usage 判定逻辑和 reason_codes 生成

测试场景（根据规格 §3 和 §8）：
1. rejected - 输入完整性失败
2. research_only - peer_sample 不足
3. verification_only - 数据完整，验证模式
4. operational_disabled - operational 在 v0.1 禁用
"""

import pytest
from src.malf.service_engine import determine_usage, generate_reason_codes
from src.malf.types import (
    CoreStateSnapshot,
    SystemState,
    Direction,
    WaveCoreState,
    UsageType,
)
from src.malf.reason_codes import ReasonCode


def test_usage_rejected_on_input_integrity_failure():
    """测试场景 1: 输入完整性失败 → rejected"""

    # 构造最小 Core 快照（UNINITIALIZED）
    core = CoreStateSnapshot(
        symbol="TEST",
        timeframe="D1",
        bar_dt="2024-01-01",
        bar_index=0,
        system_state=SystemState.UNINITIALIZED,
        direction=None,
        wave_core_state=None,
        active_wave_id=None,
        current_effective_guard_price=None,
        current_effective_guard_extreme_bar_dt=None,
        current_effective_guard_confirm_bar_dt=None,
        progress_extreme_price=None,
        progress_extreme_bar_dt=None,
        bar_count=None,
        transition_boundary_high=None,
        transition_boundary_low=None,
        active_candidate_guard_price=None,
        active_candidate_guard_extreme_bar_dt=None,
        active_candidate_guard_confirm_bar_dt=None,
        active_candidate_direction=None,
        schema_version="malf-core-snapshot-v0",
    )

    usage = determine_usage(
        core=core,
        wave_lifespan=None,
        range_lifespan=None,
        p1=None,
        p2=None,
        p3=None,
        p4=None,
        input_integrity_passed=False,  # G0 失败
        peer_sample_sufficient=True,
        data_stale=False,
    )

    assert usage == UsageType.REJECTED.value

    # 验证 reason_codes
    codes = generate_reason_codes(
        core=core,
        wave_lifespan=None,
        range_lifespan=None,
        p1=None,
        p2=None,
        p3=None,
        p4=None,
        active_range=None,
        input_integrity_passed=False,
        peer_sample_sufficient=True,
        data_stale=False,
        operational_enabled=False,
    )

    assert ReasonCode.INPUT_INTEGRITY_FAILURE in codes


def test_usage_research_only_on_peer_sample_insufficient():
    """测试场景 2: peer_sample 不足 → research_only"""

    core = CoreStateSnapshot(
        symbol="TEST",
        timeframe="D1",
        bar_dt="2024-01-07",
        bar_index=6,
        system_state=SystemState.UP_ALIVE,
        direction=Direction.UP,
        wave_core_state=WaveCoreState.ALIVE,
        active_wave_id="wave_001",
        current_effective_guard_price=99,
        current_effective_guard_extreme_bar_dt="2024-01-06",
        current_effective_guard_confirm_bar_dt="2024-01-06",
        progress_extreme_price=115,
        progress_extreme_bar_dt="2024-01-07",
        bar_count=5,
        transition_boundary_high=None,
        transition_boundary_low=None,
        active_candidate_guard_price=None,
        active_candidate_guard_extreme_bar_dt=None,
        active_candidate_guard_confirm_bar_dt=None,
        active_candidate_direction=None,
        schema_version="malf-core-snapshot-v0",
    )

    usage = determine_usage(
        core=core,
        wave_lifespan=None,
        range_lifespan=None,
        p1=None,
        p2=None,
        p3=None,
        p4=None,
        input_integrity_passed=True,
        peer_sample_sufficient=False,  # G1 失败
        data_stale=False,
    )

    assert usage == UsageType.RESEARCH_ONLY.value

    # 验证 reason_codes
    codes = generate_reason_codes(
        core=core,
        wave_lifespan=None,
        range_lifespan=None,
        p1=None,
        p2=None,
        p3=None,
        p4=None,
        active_range=None,
        input_integrity_passed=True,
        peer_sample_sufficient=False,
        data_stale=False,
        operational_enabled=False,
    )

    assert ReasonCode.PEER_SAMPLE_INSUFFICIENT in codes
    assert ReasonCode.WAVE_ALIVE in codes


def test_usage_verification_only_on_complete_data():
    """测试场景 3: 数据完整 → verification_only"""

    core = CoreStateSnapshot(
        symbol="TEST",
        timeframe="D1",
        bar_dt="2024-01-07",
        bar_index=6,
        system_state=SystemState.UP_ALIVE,
        direction=Direction.UP,
        wave_core_state=WaveCoreState.ALIVE,
        active_wave_id="wave_001",
        current_effective_guard_price=99,
        current_effective_guard_extreme_bar_dt="2024-01-06",
        current_effective_guard_confirm_bar_dt="2024-01-06",
        progress_extreme_price=115,
        progress_extreme_bar_dt="2024-01-07",
        bar_count=5,
        transition_boundary_high=None,
        transition_boundary_low=None,
        active_candidate_guard_price=None,
        active_candidate_guard_extreme_bar_dt=None,
        active_candidate_guard_confirm_bar_dt=None,
        active_candidate_direction=None,
        schema_version="malf-core-snapshot-v0",
    )

    usage = determine_usage(
        core=core,
        wave_lifespan=None,
        range_lifespan=None,
        p1=None,
        p2=None,
        p3=None,
        p4=None,
        input_integrity_passed=True,
        peer_sample_sufficient=True,
        data_stale=False,
    )

    assert usage == UsageType.VERIFICATION_ONLY.value

    # 验证 reason_codes
    codes = generate_reason_codes(
        core=core,
        wave_lifespan=None,
        range_lifespan=None,
        p1=None,
        p2=None,
        p3=None,
        p4=None,
        active_range=None,
        input_integrity_passed=True,
        peer_sample_sufficient=True,
        data_stale=False,
        operational_enabled=False,
    )

    assert ReasonCode.OPERATIONAL_DISABLED in codes
    assert ReasonCode.WAVE_ALIVE in codes


def test_operational_disabled_in_v01():
    """测试场景 4: operational 在 v0.1 禁用"""

    core = CoreStateSnapshot(
        symbol="TEST",
        timeframe="D1",
        bar_dt="2024-01-07",
        bar_index=6,
        system_state=SystemState.UP_ALIVE,
        direction=Direction.UP,
        wave_core_state=WaveCoreState.ALIVE,
        active_wave_id="wave_001",
        current_effective_guard_price=99,
        current_effective_guard_extreme_bar_dt="2024-01-06",
        current_effective_guard_confirm_bar_dt="2024-01-06",
        progress_extreme_price=115,
        progress_extreme_bar_dt="2024-01-07",
        bar_count=5,
        transition_boundary_high=None,
        transition_boundary_low=None,
        active_candidate_guard_price=None,
        active_candidate_guard_extreme_bar_dt=None,
        active_candidate_guard_confirm_bar_dt=None,
        active_candidate_direction=None,
        schema_version="malf-core-snapshot-v0",
    )

    # 即使所有条件满足，operational 也应该被禁用
    usage = determine_usage(
        core=core,
        wave_lifespan=None,
        range_lifespan=None,
        p1=None,
        p2=None,
        p3=None,
        p4=None,
        input_integrity_passed=True,
        peer_sample_sufficient=True,
        data_stale=False,
    )

    # v0.1 禁用 operational，应降级为 verification_only
    assert usage == UsageType.VERIFICATION_ONLY.value

    # 验证 reason_codes 包含 operational_disabled
    codes = generate_reason_codes(
        core=core,
        wave_lifespan=None,
        range_lifespan=None,
        p1=None,
        p2=None,
        p3=None,
        p4=None,
        active_range=None,
        input_integrity_passed=True,
        peer_sample_sufficient=True,
        data_stale=False,
        operational_enabled=False,  # v0.1 禁用
    )

    assert ReasonCode.OPERATIONAL_DISABLED in codes


def test_usage_priority_rejected_over_research_only():
    """测试 usage 判定优先级: rejected > research_only"""

    core = CoreStateSnapshot(
        symbol="TEST",
        timeframe="D1",
        bar_dt="2024-01-01",
        bar_index=0,
        system_state=SystemState.UNINITIALIZED,
        direction=None,
        wave_core_state=None,
        active_wave_id=None,
        current_effective_guard_price=None,
        current_effective_guard_extreme_bar_dt=None,
        current_effective_guard_confirm_bar_dt=None,
        progress_extreme_price=None,
        progress_extreme_bar_dt=None,
        bar_count=None,
        transition_boundary_high=None,
        transition_boundary_low=None,
        active_candidate_guard_price=None,
        active_candidate_guard_extreme_bar_dt=None,
        active_candidate_guard_confirm_bar_dt=None,
        active_candidate_direction=None,
        schema_version="malf-core-snapshot-v0",
    )

    # 同时满足 rejected 和 research_only 的条件
    usage = determine_usage(
        core=core,
        wave_lifespan=None,
        range_lifespan=None,
        p1=None,
        p2=None,
        p3=None,
        p4=None,
        input_integrity_passed=False,  # rejected
        peer_sample_sufficient=False,  # research_only
        data_stale=False,
    )

    # 应该返回 rejected（优先级更高）
    assert usage == UsageType.REJECTED.value
