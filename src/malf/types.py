"""MALF 数据结构定义。

规格权威：MALF v2.1 Definitive (deepseek-20260726)

版本说明：
- v2.1 与 v2.0 语义等价（v2.1 是清晰表达的重述版本）
- 命名变更：Probability → Structural Position（v2.1 术语更新）
- 本模块遵循 v2.1 规格的所有数据结构定义

v2.1 权威文档路径：
I:\\asteria-riskbench-Definitive-validated\\MALF_Definitive_v2_1-deepseek-20260726\\
- MALF_01_Core_v2_1-deepseek-20260726.md（Core 层数据结构）
- MALF_02_Range_v2_1-deepseek-20260726.md（Range 层数据结构）
- MALF_03_Lifespan_v2_1-deepseek-20260726.md（Lifespan 层数据结构）

实现层级：
- ✅ Core 层：PriceBar, Pivot, CoreStateSnapshot（完整）
- ✅ Range 层：RangeSnapshot, RangeState, RangeResolutionType（完整）
- ⚠️ Lifespan 层：WaveLifespan（完整），RangeLifespan（部分，待 T7.3 补全）
- ⏸ Structural Position 层：P1-P4 视图（待 T8.1-T8.4 实现）

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

    规格 D2 要求：
    - price: 极值价格（extreme bar 的 high/low）
    - confirm_price: 确认 bar 的价格（confirm bar 的 close，用于审计追溯）
    """

    pivot_type: PivotType
    price: int                      # 极值价格（extreme bar 的 high/low）
    extreme_bar_dt: str
    confirm_bar_dt: str
    confirm_price: int              # 确认 bar 的价格（规格 D2 要求）
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
    bar_index: int  # 当前 bar 序号（从 0 开始）
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
    # break（guard break 触发时刻和价格）
    break_bar_dt: Optional[str] = None  # Guard break 触发的 bar 时间
    break_price: Optional[int] = None   # Guard break 触发的价格（UP: bar.low, DOWN: bar.high）
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

    # ========================================================================
    # Range 层字段（第六刀，v2.1 Range §2-§6）
    # ========================================================================
    # Range 诞生和边界
    range_birth_bar_dt: Optional[str] = None  # Range 诞生时间（guard break 那根 bar）
    range_boundary_init_high: Optional[int] = None  # 初始上边界（冻结，用于 resolution 判定）
    range_boundary_init_low: Optional[int] = None   # 初始下边界（冻结）
    range_boundary_now_high: Optional[int] = None   # 当前上边界（演化，用于统计）
    range_boundary_now_low: Optional[int] = None    # 当前下边界（演化）
    # Range 演化和 resolution
    range_evolution_count: int = 0  # Boundary 演化次数（R2 不变量）
    range_resolution_bar_dt: Optional[str] = None  # Resolution 确认时间
    range_resolution_type: Optional[str] = None  # "continuation" | "reversal"
    range_resolution_distance: Optional[int] = None  # Resolution 距离（有符号）


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


@dataclass(frozen=True)
class WaveLifespan:
    """Wave 生命周期统计指标（v2.1 Lifespan §3）。

    只统计已终止的 wave（terminated），不统计 alive wave。
    用于历史排名（percentile_rank）和结构位置视图。
    """
    # 标识
    wave_id: str  # 格式："{symbol}_{timeframe}_w_{序号}"
    symbol: str
    timeframe: str
    direction: Direction

    # 生命周期时间窗
    wave_start_bar_dt: str  # Wave 开始时间（confirmation bar）
    wave_end_bar_dt: str    # Wave 结束时间（break bar）
    span_bars: int          # 持续 bar 数

    # 价格范围
    wave_start_price: int   # Wave 起始价格（confirmation price，v2.1 L4-2）
    wave_end_price: int     # Wave 结束价格（progress_extreme）
    price_range: int        # 价格范围（绝对值，wave_end - wave_start）
    progress_pct: float     # 进展百分比（(end - start) / start）

    # 结构复杂度
    primitive_count: int    # 初始化原语数量（H0/L1/H2 或 L0/H1/L2）
    pivot_count: int        # 总 pivot 数量（含初始化 + alive 期间新增）
    new_count: int          # Alive 期间新确认 pivot 数量（HH/LL）
    no_new_span: int        # 最后一个新 pivot 到 break 的 bar 数

    # 排名字段（计算后填充，初始为 None）
    span_rank: Optional[float] = None           # span_bars 的 percentile_rank
    range_rank: Optional[float] = None          # price_range 的 percentile_rank
    stagnation_rank: Optional[float] = None     # span_bars / max(primitive_count, 1) 的 percentile_rank
    progress_rank: Optional[float] = None       # progress_pct 的 percentile_rank


@dataclass(frozen=True)
class RangeLifespan:
    """Range 生命周期统计指标（v2.1 Lifespan §2）。

    只统计已 resolved 的 Range（resolved_up / resolved_down），不统计 alive Range。
    用于历史排名（percentile_rank）和结构位置视图。

    双类型分池（v2.1 Lifespan §2.2）：
    - continuation_range 样本池
    - reversal_range 样本池
    最小样本量：PEER_SAMPLE_MIN_N = 20
    """
    # 标识
    range_id: str  # 格式："{symbol}_{timeframe}_R{序号}"
    symbol: str
    timeframe: str
    range_type: RangeResolutionType  # continuation / reversal

    # 生命周期时间窗
    range_start_bar_dt: str  # Range 开始时间（break bar）
    range_end_bar_dt: str    # Range 结束时间（resolution bar）
    span_bars: int           # 持续 bar 数

    # Range 演化统计
    evolution_count: int        # Boundary 演化次数（v2.1 Range §3.2）
    replacement_count: int      # Candidate 替换次数（transition 期间）

    # Resolution 距离
    resolution_distance: int    # Resolution 距离（有符号整数，v2.1 Range §5）
    resolution_distance_pct: float  # Resolution 距离百分比（归一化到 boundary_init 幅度）

    # Boundary 幅度
    amplitude_init: int         # boundary_init 范围（boundary_high_init - boundary_low_init）
    amplitude_now: int          # boundary_now 范围（boundary_now_high - boundary_now_low）
    amplitude_pct: float        # boundary_now 幅度百分比（amplitude_now / boundary_low_init）

    # 排名字段（计算后填充，初始为 None）
    span_rank: Optional[float] = None                    # span_bars 的 percentile_rank
    evolution_rank: Optional[float] = None               # evolution_count 的 percentile_rank
    replacement_rank: Optional[float] = None             # replacement_count 的 percentile_rank
    resolution_distance_rank: Optional[float] = None     # resolution_distance_pct 的 percentile_rank


# ============================================================================
# Structural Position 层数据结构（v2.1 Structural Position §3-§6）
# ============================================================================


@dataclass(frozen=True)
class P1SelfRank:
    """P1 自身分位视图（v2.1 Structural Position §3）。

    直接透传 WaveLifespan 的 rank 值，不做任何变换。

    警告（v2.1 SP §3）：
    - P1 输出的是 rank（历史分位），不是概率
    - rank=0.80 意味着"当前波大于 80% 的历史同类波"
    - 不意味"有 80% 概率继续涨"
    """
    span_rank: Optional[float]           # span_bars 的 percentile_rank
    range_rank: Optional[float]          # price_range 的 percentile_rank
    stagnation_rank: Optional[float]     # span_bars / max(primitive_count, 1) 的 percentile_rank
    progress_rank: Optional[float]       # progress_pct 的 percentile_rank


@dataclass(frozen=True)
class P2SameDirMomentum:
    """P2 同向对照视图（v2.1 Structural Position §4）。

    比较当前 wave（W0）与最近 1-3 个同方向已终止波。

    警告（v2.1 SP §4）：
    - P2 输出的是 rank 差（向量差），不是概率
    - "accelerating" 标签是辅助性的，原始 rank 值始终保留
    """
    same_dir_span_momentum: Optional[float]         # W0.span_rank - mean(peers.span_rank)
    same_dir_range_momentum: Optional[float]        # W0.range_rank - mean(peers.range_rank)
    same_dir_stagnation_momentum: Optional[float]   # W0.stagnation_rank - mean(peers.stagnation_rank)
    same_dir_label: Optional[str]                   # "accelerating" | "decelerating" | "flat" | None


@dataclass(frozen=True)
class P3CrossDirMomentum:
    """P3 反向对照视图（v2.1 Structural Position §5）。

    比较当前 wave（W0）与最近 1-3 个反方向已终止波。

    警告（v2.1 SP §5）：
    - P3 输出的是 rank 差（向量差），不是概率
    - "self_dominant" 标签是辅助性的，原始 rank 值始终保留
    """
    cross_dir_span_momentum: Optional[float]         # W0.span_rank - mean(peers.span_rank)
    cross_dir_range_momentum: Optional[float]        # W0.range_rank - mean(peers.range_rank)
    cross_dir_stagnation_momentum: Optional[float]   # W0.stagnation_rank - mean(peers.stagnation_rank)
    cross_dir_label: Optional[str]                   # "self_dominant" | "opposite_dominant" | "balanced" | None


@dataclass(frozen=True)
class P4CrossCompare:
    """P4 正反对照视图（v2.1 Structural Position §6）。

    比较当前 wave（W0）与最近已终止波（W-1，任意方向）。

    警告（v2.1 SP §6）：
    - P4 输出的是 rank 差（向量差），不是概率
    - 当 cross_alive_warning = True 时，P4 信噪比低于 P2/P3
    - W0 为 alive 时 rank 不稳定，与已终止的 W-1 比较是不对称的
    """
    cross_span_momentum: Optional[float]         # W0.span_rank - W-1.span_rank
    cross_range_momentum: Optional[float]        # W0.range_rank - W-1.range_rank
    cross_stagnation_momentum: Optional[float]   # W0.stagnation_rank - W-1.stagnation_rank
    cross_alive_warning: bool                    # True 表示 W0 为 alive，rank 不稳定


# ============================================================================
# Service 层数据结构（v2.1 Service §2-§4）
# ============================================================================


class UsageType(str, Enum):
    """Usage 类型（v2.1 Service §3）。

    用途降级：rejected > research_only > verification_only > operational
    """
    REJECTED = "rejected"               # 输入完整性失败，不可消费
    RESEARCH_ONLY = "research_only"     # 数据合同不满足或模型不完整，仅研究
    VERIFICATION_ONLY = "verification_only"  # 回测验证模式，数据完整但用途受限
    OPERATIONAL = "operational"         # v0.1 禁用，需未来独立审批


@dataclass(frozen=True)
class WaveStructuralSnapshot:
    """WaveStructuralSnapshot - Service 层唯一对外契约（v2.1 Service §2）。

    这是 MALF 对下游的唯一快照结构，整合 Core + Range + Lifespan + Structural Position 四层。

    铁律（v2.1 Service §6）：
    - S1: 唯一对外契约，下游不直接访问内部对象
    - S2: 下游不准写回，快照是只读的
    - S3: 快照不可变，不可原地修改
    - S4: None 不准 fallback，必须向用户展示为"未形成"
    - S5: rule_versions 必须完整
    - S6: reason_codes 必附（任何为 None 的字段必须说明原因）
    """

    # ========== 标识字段 ==========
    symbol: str                             # 标的代码
    timeframe: str                          # 周期（"D"）
    bar_dt: str                             # 当前 bar 时间戳
    bar_index: int                          # 当前 bar 序号

    # ========== Core 层字段 ==========
    system_state: str                       # "UP_ALIVE" | "DOWN_ALIVE" | "TRANSITION" | "UNINITIALIZED"
    direction: Optional[str]                # "UP" | "DOWN" | None
    active_wave_id: Optional[str]           # 当前 alive wave 的 ID
    progress_extreme_price: Optional[int]
    progress_extreme_bar_dt: Optional[str]
    guard_price: Optional[int]
    guard_bar_dt: Optional[str]
    bar_count: Optional[int]                # 当前 wave 的 bar 数（transition 期间为 None）
    break_bar_dt: Optional[str]
    break_price: Optional[int]

    # ========== Transition / Range 层字段 ==========
    transition_boundary_high: Optional[int]
    transition_boundary_low: Optional[int]
    candidate_pivot_type: Optional[str]
    candidate_pivot_price: Optional[int]
    range_boundary_high_now: Optional[int]
    range_boundary_low_now: Optional[int]
    range_evolution_count: Optional[int]
    range_candidate_replacement_count: Optional[int]
    range_type: Optional[str]               # "continuation" | "reversal" | None

    # ========== Lifespan 层（Wave）==========
    wave_span_rank: Optional[float]
    wave_range_rank: Optional[float]
    wave_stagnation_rank: Optional[float]

    # ========== Lifespan 层（Range）==========
    range_span_rank: Optional[float]
    range_evolution_rank: Optional[float]
    range_replacement_rank: Optional[float]
    range_resolution_distance_rank: Optional[float]

    # ========== Structural Position 层 ==========
    p2_same_dir_span_momentum: Optional[float]
    p2_same_dir_range_momentum: Optional[float]
    p2_same_dir_label: Optional[str]
    p3_cross_dir_span_momentum: Optional[float]
    p3_cross_dir_range_momentum: Optional[float]
    p3_cross_dir_label: Optional[str]
    p4_cross_span_momentum: Optional[float]
    p4_cross_range_momentum: Optional[float]
    p4_cross_alive_warning: bool

    # ========== 元数据 ==========
    rule_versions: dict[str, str]           # 参与计算的规则版本（v2.1 Service §5）
    lineage_hash: Optional[str]             # 计算链路哈希（v2.1 Service §5）
    reason_codes: list[str]                 # 字段为 None 的原因代码（v2.1 Service §6 铁律 6）
    usage: str                              # "research_only" | "verification_only" | "rejected" | "operational"
    freshness: str                          # "current" | "stale_research_only"

