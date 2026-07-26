"""MALF Core 最小数据结构（S3）。

规格权威：spec §2.2（D1 PriceBar / D2 Pivot）、§2.9（CoreStateSnapshot 字段）。
本文件只定义数据的形状，不含任何状态机逻辑。纯 stdlib dataclass + enum。

价格为整数（int_fixed，spec §7.1）——领域核心不出现 float，从根上规避 float 精度问题。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SystemState(str, Enum):
    """D11 系统状态。与 wave_core_state 永不混用。"""

    UNINITIALIZED = "uninitialized"
    UP_ALIVE = "up_alive"
    DOWN_ALIVE = "down_alive"
    TRANSITION = "transition"


class Direction(str, Enum):
    """D5 结构方向。"""

    UP = "up"
    DOWN = "down"


class WaveCoreState(str, Enum):
    """D8 波段核心状态。只有 alive / terminated，不会出现 transition。"""

    ALIVE = "alive"
    TERMINATED = "terminated"


class PivotType(str, Enum):
    """D2 确认极值类型。"""

    H = "H"
    L = "L"


@dataclass(frozen=True)
class PriceBar:
    """D1 价格 bar。一切结构最终追溯到它。价格为整数（int_fixed）。"""

    symbol: str
    timeframe: str
    bar_dt: str
    open: int
    high: int
    low: int
    close: int


@dataclass(frozen=True)
class Pivot:
    """D2 确认极值。存双时间戳：extreme（极值真正发生）+ confirm（延迟 k 根后确认）。

    双时间戳是"以后看得懂"的关键：画图时高/低点画在 extreme_bar_dt，
    旁注 confirm_bar_dt——回答"为什么这个 pivot 到这根才生效"（spec §2.4 时序不对称）。
    """

    pivot_type: PivotType
    price: int
    extreme_bar_dt: str
    confirm_bar_dt: str
    pivot_id: Optional[str] = None  # 生成规则见后续；第一刀可为 None


@dataclass(frozen=True)
class CoreStateSnapshot:
    """§2.9 O7 逐 bar 发布契约。

    第一刀（uninitialized → up_alive）：最小字段集
    第二刀（uninitialized → down_alive）：对称实现
    第三刀（guard break → transition）：system_state = transition
    第四刀（transition 演化）：transition_* 和 active_candidate_* 字段

    version 字段组含 runtime_fingerprint（L4-6，审计用，不进 lineage_hash）。
    """

    # identity
    symbol: str
    timeframe: str
    bar_dt: str
    # system
    system_state: SystemState
    # wave（uninitialized 期间多为 None）
    direction: Optional[Direction] = None
    wave_core_state: Optional[WaveCoreState] = None
    active_wave_id: Optional[str] = None
    # guard（first guard = 触发确认的那个 HL/LH）
    current_effective_guard_price: Optional[int] = None
    current_effective_guard_extreme_bar_dt: Optional[str] = None
    current_effective_guard_confirm_bar_dt: Optional[str] = None
    # progress
    progress_extreme_price: Optional[int] = None
    progress_extreme_bar_dt: Optional[str] = None
    # wave duration（第五刀：T2）
    bar_count: Optional[int] = None  # Wave 持续 bar 数量，uninitialized 时为 None
    # transition（第四刀：D12 双边界 + O4/T5 active candidate）
    transition_boundary_high: Optional[int] = None
    transition_boundary_low: Optional[int] = None
    active_candidate_guard_price: Optional[int] = None
    active_candidate_guard_extreme_bar_dt: Optional[str] = None
    active_candidate_guard_confirm_bar_dt: Optional[str] = None
    active_candidate_direction: Optional[Direction] = None
    candidate_replacement_count: int = 0
    # version（replay 契约）
    core_rule_version: str = "core-v0.0.1"
    pivot_detection_rule_version: str = "fractal-k2-v1"
    price_policy: str = "int_fixed"
    runtime_fingerprint: str = ""  # 由引擎发布时填入；审计元数据，不进 lineage_hash
    # audit
    schema_version: str = "malf-core-snapshot-v0"  # 【填洞 L4-7 预留】
    note: str = field(default="", compare=False)  # 人读注释，不参与相等比较
