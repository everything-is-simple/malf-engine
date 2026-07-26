"""MALF Core Engine - 结构状态机。

本模块实现 MALF v2.1 Core 层（§1-§10）。

版本说明：
- 设计基于：MALF v2.0 Definitive (claude-20260616)
- 权威定义：MALF v2.1 Definitive (deepseek-20260726)
- 语义兼容性：v2.1 与 v2.0 完全等价（v2.1 是清晰表达版本）
- 认定者：东西南北中（2026-07-26 签署）

v2.1 权威文档：
I:\\asteria-riskbench-Definitive-validated\\MALF_Definitive_v2_1-deepseek-20260726\\

编号对照：
- D1-D18：定义（Definitions）
- T1-T10：定理（Theorems）
- O1-O8：操作边界（Operational Boundaries）

本模块实现：
- §2：Pivot 检测与确认（fractal k=2，D2）
- §3：初始化逻辑（D18/O6）
- §4-§8：状态机九步顺序（O2）
- §9：快照输出与指纹

实现进度：
- ✅ 第一~五刀：Core 层完整状态机（47 passed, 1 skipped）
- ⏸ 第六刀：Range 层（v2.1 §2 Range）
- ⏸ 第七刀：Lifespan 双轨（v2.1 §3 Lifespan）
- ⏸ 第八刀：Structural Position（v2.1 §4 Structural Position）
- ⏸ 第九刀：Service 集成（v2.1 §5 Service）
"""

from __future__ import annotations

from typing import List, Optional

from malf.fingerprint import runtime_fingerprint
from malf.initialization import InitialWaveResult, find_initial_wave
from malf.pivot_detection import detect_pivots
from malf.types import (
    CoreStateSnapshot,
    Direction,
    Pivot,
    PivotType,
    PriceBar,
    SystemState,
    WaveCoreState,
)


class MALFCoreEngine:
    """MALF 状态机核心引擎。

    逐 bar 推进状态机，产出 CoreStateSnapshot。
    状态转换：uninitialized → up/down_alive → transition → ...
    """

    def __init__(self, k: int = 2):
        """初始化引擎。

        Args:
            k: pivot detection 窗口大小（默认 2）
        """
        self.k = k
        self._bars: List[PriceBar] = []
        self._confirmed_pivots: List[Pivot] = []
        self._system_state = SystemState.UNINITIALIZED
        self._direction: Optional[Direction] = None
        self._wave_core_state: Optional[WaveCoreState] = None
        self._init_result: Optional[InitialWaveResult] = None

        # Guard 和 progress 信息
        self._guard_price: Optional[int] = None
        self._guard_extreme_bar_dt: Optional[str] = None
        self._guard_confirm_bar_dt: Optional[str] = None
        self._progress_extreme_price: Optional[int] = None
        self._progress_extreme_bar_dt: Optional[str] = None

        # Wave duration tracking（第五刀 Task 2）
        self._wave_start_bar_dt: Optional[str] = None  # Wave 开始的 bar_dt（初始化确认时设置）
        self._wave_bar_counter: int = 0  # Wave 持续 bar 数量计数器（O(1)）

        # Transition 相关信息（第四刀）
        self._transition_boundary_high: Optional[int] = None
        self._transition_boundary_low: Optional[int] = None
        self._active_candidate_guard_price: Optional[int] = None
        self._active_candidate_guard_extreme_bar_dt: Optional[str] = None
        self._active_candidate_guard_confirm_bar_dt: Optional[str] = None
        self._active_candidate_direction: Optional[Direction] = None
        self._candidate_replacement_count: int = 0
        self._break_bar_dt: Optional[str] = None  # 记录 break bar 的时间（用于 C-05）

        # Range 层状态（第六刀，v2.1 Range §2-§6）
        self._range_birth_bar_dt: Optional[str] = None
        self._range_boundary_init_high: Optional[int] = None
        self._range_boundary_init_low: Optional[int] = None
        self._range_boundary_now_high: Optional[int] = None
        self._range_boundary_now_low: Optional[int] = None
        self._range_evolution_count: int = 0
        self._range_resolution_bar_dt: Optional[str] = None
        self._range_resolution_type: Optional[str] = None
        self._range_resolution_distance: Optional[int] = None

    def on_bar(self, bar: PriceBar) -> CoreStateSnapshot:
        """逐 bar 推进状态机。

        Args:
            bar: 当前价格 bar

        Returns:
            CoreStateSnapshot: 当前状态快照
        """
        self._bars.append(bar)

        # S1: Pivot detection（检测是否有新的 pivot 在当前 bar 确认）
        all_pivots = detect_pivots(self._bars, k=self.k)
        pivots_by_confirm_dt = {p.confirm_bar_dt: p for p in all_pivots}

        if bar.bar_dt in pivots_by_confirm_dt:
            self._confirmed_pivots.append(pivots_by_confirm_dt[bar.bar_dt])

        # S2: Initialization（uninitialized → up/down_alive）
        if self._system_state == SystemState.UNINITIALIZED:
            self._init_result = find_initial_wave(self._confirmed_pivots)

            if self._init_result.confirmed:
                self._direction = self._init_result.direction
                self._wave_core_state = WaveCoreState.ALIVE
                self._guard_price = self._init_result.guard_price
                self._guard_extreme_bar_dt = self._init_result.guard_extreme_bar_dt
                self._guard_confirm_bar_dt = self._init_result.guard_confirm_bar_dt
                self._progress_extreme_price = self._init_result.progress_extreme_price
                self._progress_extreme_bar_dt = self._init_result.progress_extreme_bar_dt
                self._wave_start_bar_dt = bar.bar_dt  # 第五刀 Task 2: 记录 wave 开始时间
                self._wave_bar_counter = 1  # 初始化时计数器从 1 开始

                if self._direction == Direction.UP:
                    self._system_state = SystemState.UP_ALIVE
                elif self._direction == Direction.DOWN:
                    self._system_state = SystemState.DOWN_ALIVE

        # S3: Guard break detection（up/down_alive → transition）
        elif self._system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
            # 递增 bar 计数器（每根新 bar）
            self._wave_bar_counter += 1

            # D16 Progress Confirmation + D9 Guard Update: 检查是否有新 pivot 确认
            if bar.bar_dt in pivots_by_confirm_dt:
                new_pivot = pivots_by_confirm_dt[bar.bar_dt]
                self._update_progress_if_better(new_pivot)
                self._update_guard_if_valid(new_pivot)

            if self._check_guard_break(bar):
                # 计算双边界（D12）
                self._transition_boundary_high, self._transition_boundary_low = self._calculate_boundaries()
                self._system_state = SystemState.TRANSITION
                self._wave_core_state = WaveCoreState.TERMINATED
                self._break_bar_dt = bar.bar_dt  # 记录 break bar（用于 C-05）
                self._wave_start_bar_dt = None  # 清空 wave 开始时间（transition 期间无 active wave）
                self._wave_bar_counter = 0  # 清空计数器

                # Range 诞生（第六刀，v2.1 Range §2）
                # Range 在 guard break 时刻诞生，继承 transition boundary 作为 init 值
                self._range_birth_bar_dt = bar.bar_dt
                self._range_boundary_init_high = self._transition_boundary_high
                self._range_boundary_init_low = self._transition_boundary_low
                self._range_boundary_now_high = self._transition_boundary_high
                self._range_boundary_now_low = self._transition_boundary_low
                self._range_evolution_count = 0
                # Resolution 信息在 new wave 确认时填充

                # 初始化 candidate 状态
                self._active_candidate_guard_price = None
                self._active_candidate_guard_extreme_bar_dt = None
                self._active_candidate_guard_confirm_bar_dt = None
                self._active_candidate_direction = None
                self._candidate_replacement_count = 0

        # S4: Transition 期间 active candidate 演化（第四刀）
        elif self._system_state == SystemState.TRANSITION:
            # 检测当前 bar 是否有新确认的 pivot
            if bar.bar_dt in pivots_by_confirm_dt:
                new_pivot = pivots_by_confirm_dt[bar.bar_dt]

                # Range boundary 演化（第六刀，R2 不变量）
                # boundary_now 只能单调扩展：high 只能增，low 只能减
                if new_pivot.pivot_type == PivotType.H and new_pivot.price > self._range_boundary_now_high:
                    self._range_boundary_now_high = new_pivot.price
                    self._range_evolution_count += 1

                if new_pivot.pivot_type == PivotType.L and new_pivot.price < self._range_boundary_now_low:
                    self._range_boundary_now_low = new_pivot.price
                    self._range_evolution_count += 1

                # C-05: break bar 自身的极值不进 candidate 逻辑
                if new_pivot.extreme_bar_dt != self._break_bar_dt:
                    # 先检查 new wave 确认（T6 双条件）
                    # 必须在更新 candidate 之前检查，因为 C-02 要求 confirmation 在 active candidate 之后
                    if self._check_new_wave_confirmation(new_pivot):
                        # 进入 new wave
                        self._enter_new_wave(new_pivot)
                    else:
                        # 未触发 new wave，更新 active candidate（O4/T5 flip-flop）
                        self._update_active_candidate(new_pivot)

        # 产出当前 bar 的 snapshot
        return self._make_snapshot(bar)

    def _check_guard_break(self, bar: PriceBar) -> bool:
        """检查当前 bar 是否突破 guard。

        Args:
            bar: 当前价格 bar

        Returns:
            bool: 是否触发 guard break
        """
        if self._guard_price is None:
            return False

        if self._system_state == SystemState.UP_ALIVE:
            # LH break: close < guard
            return bar.close < self._guard_price
        elif self._system_state == SystemState.DOWN_ALIVE:
            # HL break: close > guard
            return bar.close > self._guard_price

        return False

    def _calculate_boundaries(self) -> tuple[int, int]:
        """计算 transition 双边界（D12）。

        Returns:
            tuple[int, int]: (boundary_high, boundary_low)

        UP 方向 break:
            - boundary_high = old final HH (progress_extreme_price)
            - boundary_low = broken guard (guard_price)

        DOWN 方向 break:
            - boundary_high = broken guard (guard_price)
            - boundary_low = old final LL (progress_extreme_price)
        """
        if self._system_state == SystemState.UP_ALIVE:
            # UP break: boundary_high = progress (HH), boundary_low = guard (HL)
            return self._progress_extreme_price, self._guard_price
        elif self._system_state == SystemState.DOWN_ALIVE:
            # DOWN break: boundary_high = guard (LH), boundary_low = progress (LL)
            return self._guard_price, self._progress_extreme_price
        else:
            raise ValueError(f"Invalid state for boundary calculation: {self._system_state}")

    def _update_active_candidate(self, new_pivot: Pivot) -> None:
        """更新 active candidate（O4/T5 flip-flop）。

        Args:
            new_pivot: 新确认的 pivot

        规则（T5）:
        - active_candidate = latest candidate_guard
        - 新候选一出现就替换旧的，不分同向反向（flip-flop）
        - candidate_replacement_count 计所有替换事件
        """
        # 首次 candidate（无替换）
        if self._active_candidate_guard_price is None:
            self._active_candidate_guard_price = new_pivot.price
            self._active_candidate_guard_extreme_bar_dt = new_pivot.extreme_bar_dt
            self._active_candidate_guard_confirm_bar_dt = new_pivot.confirm_bar_dt
            # 根据 pivot 类型确定 direction
            if new_pivot.pivot_type == PivotType.L:
                self._active_candidate_direction = Direction.DOWN
            else:
                self._active_candidate_direction = Direction.UP
            # 首次不计入 replacement
            return

        # 已有 candidate，判断是否替换
        old_direction = self._active_candidate_direction

        # 确定新 pivot 的方向
        if new_pivot.pivot_type == PivotType.L:
            new_direction = Direction.DOWN
        else:
            new_direction = Direction.UP

        # 同向替换（refresh）或反向替换（flip-flop）
        # 规则：latest wins，不管是同向还是反向
        self._active_candidate_guard_price = new_pivot.price
        self._active_candidate_guard_extreme_bar_dt = new_pivot.extreme_bar_dt
        self._active_candidate_guard_confirm_bar_dt = new_pivot.confirm_bar_dt
        self._active_candidate_direction = new_direction
        self._candidate_replacement_count += 1

    def _check_new_wave_confirmation(self, new_pivot: Pivot) -> bool:
        """检查 new wave 确认（T6 双条件）。

        Args:
            new_pivot: 新确认的 pivot

        Returns:
            bool: 是否触发 new wave

        双条件（T6）：
        1. active_candidate_guard 存在
        2. 其后 confirmation 严格突破对侧边界

        UP wave: active candidate L + H > boundary_high
        DOWN wave: active candidate H + L < boundary_low
        """
        # 条件 1：必须有 active candidate
        if self._active_candidate_guard_price is None:
            return False

        # 条件 2：new_pivot 必须在 active candidate 之后（C-02）
        if new_pivot.confirm_bar_dt <= self._active_candidate_guard_confirm_bar_dt:
            return False

        # 检查是否突破对侧边界
        if new_pivot.pivot_type == PivotType.H:
            # H pivot: 检查是否 > boundary_high（触发 UP wave）
            return new_pivot.price > self._transition_boundary_high
        else:
            # L pivot: 检查是否 < boundary_low（触发 DOWN wave）
            return new_pivot.price < self._transition_boundary_low

    def _update_progress_if_better(self, new_pivot: Pivot) -> None:
        """D16 Progress Confirmation: 更新 progress_extreme（如果新 pivot 更优）。

        Args:
            new_pivot: 新确认的 pivot

        规则（D16）：
        - UP wave: 新 H pivot 且 price > progress_extreme_price → 更新
        - DOWN wave: 新 L pivot 且 price < progress_extreme_price → 更新
        """
        if self._system_state == SystemState.UP_ALIVE:
            # UP wave: 检查新 H pivot 是否推进
            if new_pivot.pivot_type == PivotType.H and new_pivot.price > self._progress_extreme_price:
                self._progress_extreme_price = new_pivot.price
                self._progress_extreme_bar_dt = new_pivot.extreme_bar_dt
        elif self._system_state == SystemState.DOWN_ALIVE:
            # DOWN wave: 检查新 L pivot 是否推进
            if new_pivot.pivot_type == PivotType.L and new_pivot.price < self._progress_extreme_price:
                self._progress_extreme_price = new_pivot.price
                self._progress_extreme_bar_dt = new_pivot.extreme_bar_dt

    def _update_guard_if_valid(self, new_pivot: Pivot) -> None:
        """D9 守护唯一性铁律: 更新 guard（如果新 pivot 是回撤类型）。

        Args:
            new_pivot: 新确认的 pivot

        规则（D9）：
        - UP wave: 只有新 L pivot（回撤）才能替换 guard，H pivot 只更新 progress
        - DOWN wave: 只有新 H pivot（回撤）才能替换 guard，L pivot 只更新 progress
        - Guard 是单元素栈，新的回撤 pivot 直接替换旧的
        """
        if self._system_state == SystemState.UP_ALIVE:
            # UP wave: 只有 L pivot（回撤）才能替换 guard
            if new_pivot.pivot_type == PivotType.L:
                self._guard_price = new_pivot.price
                self._guard_extreme_bar_dt = new_pivot.extreme_bar_dt
                self._guard_confirm_bar_dt = new_pivot.confirm_bar_dt
        elif self._system_state == SystemState.DOWN_ALIVE:
            # DOWN wave: 只有 H pivot（回撤）才能替换 guard
            if new_pivot.pivot_type == PivotType.H:
                self._guard_price = new_pivot.price
                self._guard_extreme_bar_dt = new_pivot.extreme_bar_dt
                self._guard_confirm_bar_dt = new_pivot.confirm_bar_dt

    def _enter_new_wave(self, confirmation_pivot: Pivot) -> None:
        """进入 new wave。

        Args:
            confirmation_pivot: 触发 confirmation 的 pivot（H for UP, L for DOWN）

        New wave 设置：
        - guard = active_candidate
        - progress = confirmation_pivot
        - direction = confirmation_pivot 决定
        - 清空 transition 字段
        - 记录 Range resolution（第六刀）
        """
        # 确定新波方向
        if confirmation_pivot.pivot_type == PivotType.H:
            new_direction = Direction.UP
            self._system_state = SystemState.UP_ALIVE
        else:
            new_direction = Direction.DOWN
            self._system_state = SystemState.DOWN_ALIVE

        # Range resolution 判定（第六刀，v2.1 Range §4-§6）
        # 记录 resolution 信息
        self._range_resolution_bar_dt = confirmation_pivot.confirm_bar_dt

        # 计算 resolution_type（基于 break_direction）
        # break_direction 是旧 wave 被 break 的方向（与旧 wave 方向相反）
        old_wave_direction = self._direction  # transition 期间 direction 保持旧 wave 方向
        if old_wave_direction == Direction.UP:
            break_direction = Direction.DOWN  # UP wave 向下 break
        else:
            break_direction = Direction.UP  # DOWN wave 向上 break

        # Continuation/Reversal 判定（相对于 break 方向）
        if break_direction == new_direction:
            self._range_resolution_type = "continuation"  # 延续 break 方向
        else:
            self._range_resolution_type = "reversal"  # 反转 break 方向

        # 计算 resolution_distance（基于 boundary_init）
        if new_direction == Direction.UP:
            self._range_resolution_distance = confirmation_pivot.price - self._range_boundary_init_high
        else:
            self._range_resolution_distance = confirmation_pivot.price - self._range_boundary_init_low

        # 设置 guard = active candidate
        self._guard_price = self._active_candidate_guard_price
        self._guard_extreme_bar_dt = self._active_candidate_guard_extreme_bar_dt
        self._guard_confirm_bar_dt = self._active_candidate_guard_confirm_bar_dt

        # 设置 progress = confirmation pivot
        self._progress_extreme_price = confirmation_pivot.price
        self._progress_extreme_bar_dt = confirmation_pivot.extreme_bar_dt

        # 更新方向和状态
        self._direction = new_direction
        self._wave_core_state = WaveCoreState.ALIVE
        self._wave_start_bar_dt = confirmation_pivot.confirm_bar_dt  # 第五刀 Task 2: 重置 wave 开始时间
        self._wave_bar_counter = 1  # 新 wave 从 1 开始计数

        # 清空 transition 字段
        self._transition_boundary_high = None
        self._transition_boundary_low = None
        self._active_candidate_guard_price = None
        self._active_candidate_guard_extreme_bar_dt = None
        self._active_candidate_guard_confirm_bar_dt = None
        self._active_candidate_direction = None
        self._candidate_replacement_count = 0
        self._break_bar_dt = None

    def _make_snapshot(self, bar: PriceBar) -> CoreStateSnapshot:
        """构造当前 bar 的状态快照。

        Args:
            bar: 当前价格 bar

        Returns:
            CoreStateSnapshot: 状态快照
        """
        # 计算 bar_count（第五刀 Task 2）
        # 使用 O(1) 计数器替代 O(n) 遍历
        bar_count = self._wave_bar_counter if self._wave_bar_counter > 0 else None

        if self._system_state == SystemState.UNINITIALIZED:
            return CoreStateSnapshot(
                symbol=bar.symbol,
                timeframe=bar.timeframe,
                bar_dt=bar.bar_dt,
                system_state=SystemState.UNINITIALIZED,
                runtime_fingerprint=runtime_fingerprint(),
            )
        else:
            return CoreStateSnapshot(
                symbol=bar.symbol,
                timeframe=bar.timeframe,
                bar_dt=bar.bar_dt,
                system_state=self._system_state,
                direction=self._direction,
                wave_core_state=self._wave_core_state,
                current_effective_guard_price=self._guard_price,
                current_effective_guard_extreme_bar_dt=self._guard_extreme_bar_dt,
                current_effective_guard_confirm_bar_dt=self._guard_confirm_bar_dt,
                progress_extreme_price=self._progress_extreme_price,
                progress_extreme_bar_dt=self._progress_extreme_bar_dt,
                bar_count=bar_count,  # 第五刀 Task 2: 添加 bar_count
                # Transition 字段（第四刀）
                transition_boundary_high=self._transition_boundary_high,
                transition_boundary_low=self._transition_boundary_low,
                active_candidate_guard_price=self._active_candidate_guard_price,
                active_candidate_guard_extreme_bar_dt=self._active_candidate_guard_extreme_bar_dt,
                active_candidate_guard_confirm_bar_dt=self._active_candidate_guard_confirm_bar_dt,
                active_candidate_direction=self._active_candidate_direction,
                candidate_replacement_count=self._candidate_replacement_count,
                # Range 字段（第六刀）
                range_birth_bar_dt=self._range_birth_bar_dt,
                range_boundary_init_high=self._range_boundary_init_high,
                range_boundary_init_low=self._range_boundary_init_low,
                range_boundary_now_high=self._range_boundary_now_high,
                range_boundary_now_low=self._range_boundary_now_low,
                range_evolution_count=self._range_evolution_count,
                range_resolution_bar_dt=self._range_resolution_bar_dt,
                range_resolution_type=self._range_resolution_type,
                range_resolution_distance=self._range_resolution_distance,
                runtime_fingerprint=runtime_fingerprint(),
            )
