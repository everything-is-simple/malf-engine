"""MALF 数据结构定义。

规格权威：MALF v2.1 Definitive (deepseek-20260726)
- Core 层：v2.1 §1 Core（D1 PriceBar / D2 Pivot / §9 CoreStateSnapshot）
- 版本兼容：v2.1 与 v2.0 语义等价（v2.1 是清晰表达版本）
- 命名变更：Probability → Structural Position（v2.1 重命名，本模块未来会扩展）

本文件只定义数据的形状，不含任何状态机逻辑。纯 stdlib dataclass + enum。

价格为整数（int_fixed，v2.1 Core §9）——领域核心不出现 float，从根上规避 float 精度问题。
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
    """Core 层状态快照（v2.1 Core §9）。

    实现进度：
    - 第一刀（uninitialized → up_alive）：最小字段集 ✅
    - 第二刀（uninitialized → down_alive）：对称实现 ✅
    - 第三刀（guard break → transition）：system_state = transition ✅
    - 第四刀（transition 演化）：transition_* 和 active_candidate_* 字段 ✅
    - 第五刀（guard 更新 + bar_count + replay）：D9 守护更新 + O8 确定性 ✅

    v2.1 对应：
    - 本快照对应 v2.1 Core §9 的完整字段
    - 未来会被 WaveStructuralSnapshot 包装（v2.1 Service §2）
    - WaveStructuralSnapshot = Core + Range + Lifespan + Structural Position

    version 字段组含 runtime_fingerprint（v2.1 Core §9，审计用，不进 lineage_hash）。
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


# ============================================================================
# Range 层数据结构（v2.1 Range §2-§6）
# ============================================================================


class RangeState(str, Enum):
    """Range 生命周期状态（v2.1 Range §4）。"""

    ALIVE = "alive"        # Range 活跃中（尚未 resolve）
    RESOLVED = "resolved"  # Range 已解决（new wave 确认）


class RangeResolutionType(str, Enum):
    """Range resolution 分类（v2.1 Range §6）。

    命名陷阱警告（v2.1 Range §6.2）：
    - continuation: 延续 **break 方向**（不是旧 wave 方向）
    - reversal: 反转 **break 方向**

    例子：
    - UP wave → 下 break（break_direction=DOWN）→ 下突破 → continuation
    - UP wave → 下 break（break_direction=DOWN）→ 上突破 → reversal
    - DOWN wave → 上 break（break_direction=UP）→ 上突破 → continuation
    - DOWN wave → 上 break（break_direction=UP）→ 下突破 → reversal
    """

    CONTINUATION = "continuation"  # 延续 break 方向
    REVERSAL = "reversal"          # 反转 break 方向


@dataclass(frozen=True)
class RangeSnapshot:
    """Range 层状态快照（v2.1 Range §2）。

    Range 是 transition 的升格版本，有自己的边界、生命周期、分类。

    两层边界模型（v2.1 Range §3）：
    - boundary_init: 冻结边界（Core 层使用，用于 resolution 判定）
    - boundary_now: 演化边界（Range 层使用，逐 pivot 扩展）

    使用场景对照表：
    - Resolution 判定（T6）：使用 boundary_init
    - Resolution distance 计算：使用 boundary_init
    - Range 统计（width, evolution_count）：使用 boundary_now
    - Range 分类（continuation/reversal）：基于 break_direction

    混用 init/now 会导致状态机不稳定或统计失真。
    """

    # identity
    symbol: str
    timeframe: str
    bar_dt: str
    range_id: str  # 格式："{symbol}_{timeframe}_R{序号}"

    # 生命周期
    range_state: RangeState  # alive / resolved
    birth_bar_dt: str  # Range 诞生时间（guard break 那根 bar）

    # 两层边界（v2.1 Range §3 核心设计）
    boundary_init_high: int  # 初始上边界（冻结，用于 resolution 判定）
    boundary_init_low: int   # 初始下边界（冻结）
    boundary_now_high: int   # 当前上边界（演化，用于统计）
    boundary_now_low: int    # 当前下边界（演化）

    # Break 方向（决定 continuation/reversal 分类）
    break_direction: Direction  # 从哪个方向 break 出来的（UP wave → 下 break，DOWN wave → 上 break）
    old_wave_direction: Direction  # 旧 wave 方向（用于命名陷阱警告）

    # 版本信息
    range_rule_version: str
    schema_version: str

    # 演化统计（带默认值）
    evolution_count: int = 0  # Boundary 演化次数（R2）

    # Resolution 信息（resolved 时填充，带默认值）
    resolution_bar_dt: Optional[str] = None  # Resolution 确认时间
    resolution_type: Optional[RangeResolutionType] = None  # continuation / reversal
    resolution_distance: Optional[int] = None  # 突破距离（有符号整数，v2.1 Range §5）
    confirmation_pivot_extreme_price: Optional[int] = None  # 触发 resolution 的 pivot 极值价格
    confirmation_pivot_extreme_bar_dt: Optional[str] = None  # 极值时间
    confirmation_pivot_confirm_bar_dt: Optional[str] = None  # 确认时间
    new_wave_direction: Optional[Direction] = None  # 新 wave 方向
