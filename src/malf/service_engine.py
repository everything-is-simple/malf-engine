"""
MALF v2.1 Service 层 - Usage 判定与失败模式

规格权威：MALF_05_Service_v2_1-deepseek-20260726.md §3, §6, §8

职责：
- 实现 usage 判定逻辑（rejected / research_only / verification_only / operational）
- 生成 reason_codes（说明任何为 None 的字段的原因）
- 组装 WaveStructuralSnapshot（整合 Core + Range + Lifespan + Position 四层）
"""

from typing import Optional
from .types import (
    CoreStateSnapshot,
    RangeSnapshot,
    WaveLifespan,
    RangeLifespan,
    P1SelfRank,
    P2SameDirMomentum,
    P3CrossDirMomentum,
    P4CrossCompare,
    WaveStructuralSnapshot,
    UsageType,
    SystemState,
)
from .reason_codes import ReasonCode


# ============================================================================
# Usage 判定规则（规格 §3）
# ============================================================================


def determine_usage(
    core: CoreStateSnapshot,
    wave_lifespan: Optional[WaveLifespan],
    range_lifespan: Optional[RangeLifespan],
    p1: Optional[P1SelfRank],
    p2: Optional[P2SameDirMomentum],
    p3: Optional[P3CrossDirMomentum],
    p4: Optional[P4CrossCompare],
    input_integrity_passed: bool = True,
    peer_sample_sufficient: bool = True,
    data_stale: bool = False,
) -> str:
    """
    判定 usage 类型（规格 §3 usage 判定规则）。

    判定优先级：rejected > research_only > verification_only > operational

    Args:
        core: Core 层快照
        wave_lifespan: Wave 生命周期（可选）
        range_lifespan: Range 生命周期（可选）
        p1-p4: Structural Position 视图（可选）
        input_integrity_passed: 输入完整性检查是否通过（G0）
        peer_sample_sufficient: peer_sample 是否充足（G1）
        data_stale: 数据是否过期（G1）

    Returns:
        usage 类型字符串

    规则：
    - rejected: G0 输入完整性失败
    - research_only: G1 数据合同不满足 或 G2 模型不完整
    - verification_only: 数据完整但处于验证模式
    - operational: v0.1 禁用（需未来独立审批）
    """

    # G0: 输入完整性失败 → rejected
    if not input_integrity_passed:
        return UsageType.REJECTED.value

    # G1: 数据合同不满足 → research_only
    if not peer_sample_sufficient or data_stale:
        return UsageType.RESEARCH_ONLY.value

    # G2: 模型不完整（rank 字段为 None）→ research_only
    if wave_lifespan is not None:
        if (wave_lifespan.span_rank is None or
            wave_lifespan.range_rank is None or
            wave_lifespan.stagnation_rank is None):
            return UsageType.RESEARCH_ONLY.value

    # operational 在 v0.1 禁用（规格 §3）
    # 所有条件满足时，降级为 verification_only
    return UsageType.VERIFICATION_ONLY.value


def generate_reason_codes(
    core: CoreStateSnapshot,
    wave_lifespan: Optional[WaveLifespan],
    range_lifespan: Optional[RangeLifespan],
    p1: Optional[P1SelfRank],
    p2: Optional[P2SameDirMomentum],
    p3: Optional[P3CrossDirMomentum],
    p4: Optional[P4CrossCompare],
    active_range: Optional[RangeSnapshot],
    input_integrity_passed: bool = True,
    peer_sample_sufficient: bool = True,
    data_stale: bool = False,
    operational_enabled: bool = False,
) -> list[str]:
    """
    生成 reason_codes（规格 §6 铁律 6 和 §8 失败模式）。

    任何为 None 的字段必须在 reason_codes 中说明原因。

    Args:
        core: Core 层快照
        wave_lifespan: Wave 生命周期（可选）
        range_lifespan: Range 生命周期（可选）
        p1-p4: Structural Position 视图（可选）
        active_range: 当前 Range（可选）
        input_integrity_passed: 输入完整性检查是否通过
        peer_sample_sufficient: peer_sample 是否充足
        data_stale: 数据是否过期
        operational_enabled: operational 模式是否启用

    Returns:
        reason_codes 列表
    """
    codes: list[str] = []

    # 输入完整性失败
    if not input_integrity_passed:
        codes.append(ReasonCode.INPUT_INTEGRITY_FAILURE)
        return codes  # rejected 情况，其他 reason 不再添加

    # Core 层未初始化
    if core.system_state == SystemState.UNINITIALIZED:
        codes.append(ReasonCode.UNINITIALIZED)

    # Transition 期间
    if core.system_state == SystemState.TRANSITION:
        codes.append(ReasonCode.TRANSITION_ACTIVE)

    # Wave 为 alive（未终止）
    if core.wave_core_state and core.wave_core_state.value == "alive":
        codes.append(ReasonCode.WAVE_ALIVE)

    # peer_sample 不足
    if not peer_sample_sufficient:
        codes.append(ReasonCode.PEER_SAMPLE_INSUFFICIENT)

    # 数据过期
    if data_stale:
        codes.append(ReasonCode.DATA_STALE)

    # P2 同向对照不存在
    if p2 is not None and p2.same_dir_span_momentum is None:
        codes.append(ReasonCode.SAME_DIR_PEERS_ABSENT)

    # P3 反向对照不存在
    if p3 is not None and p3.cross_dir_span_momentum is None:
        codes.append(ReasonCode.CROSS_DIR_PEERS_ABSENT)

    # P4 W-1 不存在
    if p4 is not None and p4.cross_span_momentum is None:
        codes.append(ReasonCode.NO_PRIOR_WAVE)

    # Range 未结束
    if active_range is not None and active_range.range_state.value == "alive":
        codes.append(ReasonCode.RANGE_ALIVE)

    # operational 在 v0.1 禁用
    if not operational_enabled:
        codes.append(ReasonCode.OPERATIONAL_DISABLED)

    return codes


# ============================================================================
# Snapshot 组装（规格 §2）
# ============================================================================


def build_wave_structural_snapshot(
    symbol: str,
    timeframe: str,
    bar_dt: str,
    bar_index: int,
    core: CoreStateSnapshot,
    active_range: Optional[RangeSnapshot],
    wave_lifespan: Optional[WaveLifespan],
    range_lifespan: Optional[RangeLifespan],
    p1: Optional[P1SelfRank],
    p2: Optional[P2SameDirMomentum],
    p3: Optional[P3CrossDirMomentum],
    p4: Optional[P4CrossCompare],
    rule_versions: dict[str, str],
    lineage_hash: Optional[str],
    input_integrity_passed: bool = True,
    peer_sample_sufficient: bool = True,
    data_stale: bool = False,
    operational_enabled: bool = False,
) -> WaveStructuralSnapshot:
    """
    组装 WaveStructuralSnapshot（规格 §2）。

    整合 Core + Range + Lifespan + Structural Position 四层数据。

    Args:
        symbol: 标的代码
        timeframe: 周期
        bar_dt: 当前 bar 时间戳
        bar_index: 当前 bar 序号
        core: Core 层快照
        active_range: 当前 Range（可选）
        wave_lifespan: Wave 生命周期（可选）
        range_lifespan: Range 生命周期（可选）
        p1-p4: Structural Position 视图（可选）
        rule_versions: 规则版本字典
        lineage_hash: 计算链路哈希（可选）
        input_integrity_passed: 输入完整性检查是否通过
        peer_sample_sufficient: peer_sample 是否充足
        data_stale: 数据是否过期
        operational_enabled: operational 模式是否启用

    Returns:
        WaveStructuralSnapshot 对象
    """

    # 判定 usage
    usage = determine_usage(
        core=core,
        wave_lifespan=wave_lifespan,
        range_lifespan=range_lifespan,
        p1=p1,
        p2=p2,
        p3=p3,
        p4=p4,
        input_integrity_passed=input_integrity_passed,
        peer_sample_sufficient=peer_sample_sufficient,
        data_stale=data_stale,
    )

    # 生成 reason_codes
    reason_codes = generate_reason_codes(
        core=core,
        wave_lifespan=wave_lifespan,
        range_lifespan=range_lifespan,
        p1=p1,
        p2=p2,
        p3=p3,
        p4=p4,
        active_range=active_range,
        input_integrity_passed=input_integrity_passed,
        peer_sample_sufficient=peer_sample_sufficient,
        data_stale=data_stale,
        operational_enabled=operational_enabled,
    )

    # 确定 freshness
    freshness = "stale_research_only" if data_stale else "current"

    # 组装快照（规格 §2 字段结构）
    return WaveStructuralSnapshot(
        # 标识
        symbol=symbol,
        timeframe=timeframe,
        bar_dt=bar_dt,
        bar_index=bar_index,

        # Core 层
        system_state=core.system_state.value,
        direction=core.direction.value if core.direction else None,
        active_wave_id=core.active_wave_id,
        progress_extreme_price=core.progress_extreme_price,
        progress_extreme_bar_dt=core.progress_extreme_bar_dt,
        guard_price=core.current_effective_guard_price,
        guard_bar_dt=core.current_effective_guard_extreme_bar_dt,
        bar_count=core.bar_count,
        break_bar_dt=core.break_bar_dt,
        break_price=core.break_price,

        # Range 层
        transition_boundary_high=core.transition_boundary_high,
        transition_boundary_low=core.transition_boundary_low,
        candidate_pivot_type=core.active_candidate_direction.value if core.active_candidate_direction else None,
        candidate_pivot_price=core.active_candidate_guard_price,
        range_boundary_high_now=active_range.boundary_now_high if active_range else None,
        range_boundary_low_now=active_range.boundary_now_low if active_range else None,
        range_evolution_count=active_range.evolution_count if active_range else None,
        range_candidate_replacement_count=core.candidate_replacement_count,  # 来自 CoreStateSnapshot
        range_type=active_range.resolution_type.value if active_range and active_range.resolution_type else None,

        # Lifespan 层（Wave）
        wave_span_rank=wave_lifespan.span_rank if wave_lifespan else None,
        wave_range_rank=wave_lifespan.range_rank if wave_lifespan else None,
        wave_stagnation_rank=wave_lifespan.stagnation_rank if wave_lifespan else None,

        # Lifespan 层（Wave 推进 + 身份，T9.15 新增）
        progress_pct=wave_lifespan.progress_pct if wave_lifespan else None,
        new_count=wave_lifespan.new_count if wave_lifespan else None,
        no_new_span=wave_lifespan.no_new_span if wave_lifespan else None,
        progress_rank=wave_lifespan.progress_rank if wave_lifespan else None,
        birth_type=core.active_wave.birth_type if core.active_wave else None,
        wave_id=wave_lifespan.wave_id if wave_lifespan else core.active_wave.wave_id if core.active_wave else None,
        wave_start_bar_dt=wave_lifespan.wave_start_bar_dt if wave_lifespan else (core.active_wave.start_bar_dt if core.active_wave else None),
        wave_end_bar_dt=wave_lifespan.wave_end_bar_dt if wave_lifespan else None,

        # Lifespan 层（Range）
        range_span_rank=range_lifespan.span_rank if range_lifespan else None,
        range_evolution_rank=range_lifespan.evolution_rank if range_lifespan else None,
        range_replacement_rank=range_lifespan.replacement_rank if range_lifespan else None,
        range_resolution_distance_rank=range_lifespan.resolution_distance_rank if range_lifespan else None,

        # Lifespan 层（Range 演化，T9.15 新增）
        range_amplitude_init=range_lifespan.amplitude_init if range_lifespan else None,
        range_amplitude_now=range_lifespan.amplitude_now if range_lifespan else None,
        range_amplitude_pct=range_lifespan.amplitude_pct if range_lifespan else None,
        range_resolution_distance_pct=range_lifespan.resolution_distance_pct if range_lifespan else None,

        # Structural Position 层
        p2_same_dir_span_momentum=p2.same_dir_span_momentum if p2 else None,
        p2_same_dir_range_momentum=p2.same_dir_range_momentum if p2 else None,
        p2_same_dir_label=p2.same_dir_label if p2 else None,
        p3_cross_dir_span_momentum=p3.cross_dir_span_momentum if p3 else None,
        p3_cross_dir_range_momentum=p3.cross_dir_range_momentum if p3 else None,
        p3_cross_dir_label=p3.cross_dir_label if p3 else None,
        p4_cross_span_momentum=p4.cross_span_momentum if p4 else None,
        p4_cross_range_momentum=p4.cross_range_momentum if p4 else None,
        p4_cross_alive_warning=p4.cross_alive_warning if p4 else False,

        # 元数据
        rule_versions=rule_versions,
        lineage_hash=lineage_hash,
        reason_codes=reason_codes,
        usage=usage,
        freshness=freshness,
    )
