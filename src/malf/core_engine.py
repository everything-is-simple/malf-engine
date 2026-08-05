"""MALF Core Engine - 结构状态机。

本模块实现 MALF v2.1 Core 层（§1-§10）和 Range 层（§2）。

版本说明：
- 设计基于：MALF v2.0 Definitive (claude-20260616)
- 权威规格：MALF v2.1 Definitive (deepseek-20260726)
- 语义兼容性：v2.1 与 v2.0 完全等价（v2.1 是清晰表达版本）
- 认定者：东西南北中（2026-07-26 签署）

v2.1 权威文档路径：
I:\\asteria-riskbench-Definitive-validated\\MALF_Definitive_v2_1-deepseek-20260726\\
- MALF_01_Core_v2_1-deepseek-20260726.md（Core 层）
- MALF_02_Range_v2_1-deepseek-20260726.md（Range 层）
- MALF_03_Lifespan_v2_1-deepseek-20260726.md（Lifespan 层）
- MALF_04_Structural_Position_v2_1-deepseek-20260726.md（Structural Position 层）
- MALF_05_Service_v2_1-deepseek-20260726.md（Service 层）

编号对照：
- D1-D18：定义（Definitions）
- T1-T10：定理（Theorems）
- O1-O8：操作边界（Operational Boundaries）

本模块实现：
- §1 Core 层：Pivot 检测、初始化、状态机、快照输出（完整）
- §2 Range 层：震荡区间识别、边界演化、resolution 判定（完整）

实现进度：
- ✅ Core 层（6 刀）：完整状态机（58 passed, 1 skipped）
- ✅ Range 层（4 刀）：T6.1-T6.4 全部完成（6 tests + real data）
- ⚠️ Lifespan 层（2/4 刀）：T7.1-T7.2 完成，T7.3-T7.4 待做
- ⏸ Structural Position 层（0 刀）：T8.1-T8.4 待做
- ⏸ Service 层（0 刀）：T9.1-T9.2 待做
"""

from __future__ import annotations

from dataclasses import replace
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
    RangeResolutionType,
    RangeSnapshot,
    RangeState,
    SystemState,
    WaveCoreState,
    WaveSnapshot,
)
from malf.version import RANGE_RULE_VERSION, RANGE_SNAPSHOT_SCHEMA_VERSION


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
        self._bar_index: int = 0  # 当前 bar 序号（从 0 开始）
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
        self._break_price: Optional[int] = None   # 记录 break price（UP: bar.low, DOWN: bar.high）

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

        # ==================================================================
        # Wave / Range 生命周期事实聚合（DECISION-004）
        # 供 _make_snapshot 构造公开 facts 对象（active_wave / terminated_wave /
        # active_range / resolved_range / active_wave_id），driver 只读公开字段。
        # ==================================================================
        self._wave_seq: int = 0          # wave_id 序号（L4-1：从 1 单调递增，永不复用）
        self._range_seq: int = 0         # range_id 序号（break 那根 bar 递增并定死）
        self._birth_type: str = "initial"  # initial | continuation | reversal
        self._current_wave_pivots: List[Pivot] = []  # 当前 alive wave 已确认 pivot
        self._new_count: int = 0         # D16 progress 更新次数（Lifespan §3 new_count）
        self._last_progress_bar_dt: Optional[str] = None
        self._no_new_span: int = 0       # 两次 progress 更新间的 bar 数（Lifespan §3 no_new_span）
        self._wave_start_price: Optional[int] = None  # wave 起始价（confirmation price，L4-2）
        self._frozen_terminated_wave: Optional[WaveSnapshot] = None  # 一次性事件冻结槽
        self._frozen_resolved_range: Optional[RangeSnapshot] = None  # 一次性事件冻结槽
        self._active_range_snap: Optional[RangeSnapshot] = None      # range alive 期间持续态

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

                # DECISION-004: 初始 wave 聚合（L4-1 seq 从 1 开始）
                self._wave_seq += 1
                self._birth_type = "initial"
                self._current_wave_pivots = list(self._init_result.pivots)
                self._new_count = 0
                self._last_progress_bar_dt = None
                self._no_new_span = 0
                self._wave_start_price = (
                    self._init_result.pivots[-1].price if self._init_result.pivots else None
                )  # L4-2 confirmation price（初始化确认 pivot = 最后一个）

                if self._direction == Direction.UP:
                    self._system_state = SystemState.UP_ALIVE
                elif self._direction == Direction.DOWN:
                    self._system_state = SystemState.DOWN_ALIVE

        # S3: Guard break detection（up/down_alive → transition）
        elif self._system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
            # 递增 bar 计数器（每根新 bar）
            self._wave_bar_counter += 1
            # DECISION-004: 每根 alive bar 递增 no_new_span（无新推进 bar 数）
            self._no_new_span += 1

            # T9.11 对齐权威 O2（Core §3）：break 检查先于 progress/guard 更新（2026-08-05）
            if self._check_guard_break(bar):
                # 计算双边界（D12）
                self._transition_boundary_high, self._transition_boundary_low = self._calculate_boundaries()
                self._system_state = SystemState.TRANSITION
                self._wave_core_state = WaveCoreState.TERMINATED
                self._break_bar_dt = bar.bar_dt  # 记录 break bar（用于 C-05）
                # 记录 break price（触发 break 的价格）
                if self._direction == Direction.UP:
                    self._break_price = bar.low  # UP wave 向下突破
                elif self._direction == Direction.DOWN:
                    self._break_price = bar.high  # DOWN wave 向上突破

                # DECISION-004: 冻结 terminated wave facts（在清空实时值之前）
                self._frozen_terminated_wave = WaveSnapshot(
                    symbol=bar.symbol,
                    timeframe=bar.timeframe,
                    wave_id=f"{bar.symbol}_{bar.timeframe}_{self._wave_seq}",
                    direction=self._direction,
                    birth_type=self._birth_type,
                    wave_state=WaveCoreState.TERMINATED,
                    pivots=tuple(self._current_wave_pivots),
                    start_bar_dt=self._wave_start_bar_dt,
                    start_price=self._wave_start_price,
                    progress_extreme_price=self._progress_extreme_price,
                    progress_extreme_bar_dt=self._progress_extreme_bar_dt,
                    guard_price=self._guard_price,
                    guard_bar_dt=self._guard_extreme_bar_dt,
                    bar_count=self._wave_bar_counter,  # 冻结值（不再清零丢失）
                    break_bar_dt=self._break_bar_dt,
                    break_price=self._break_price,
                    wave_end_price=self._progress_extreme_price,  # = progress_extreme（Lifespan §3）
                    primitive_count=max(len(self._current_wave_pivots) - 1, 0),
                    pivot_count=len(self._current_wave_pivots),
                    first_pivot_price=(
                        self._current_wave_pivots[0].price if self._current_wave_pivots else None
                    ),
                    new_count=self._new_count,
                    no_new_span=self._no_new_span,
                )

                self._wave_start_bar_dt = None  # 清空 wave 开始时间（transition 期间无 active wave）
                self._wave_bar_counter = 0  # 清空计数器（冻结值已存进 facts）
                # DECISION-004: wave 已终止，实时聚合清空（transition 期间无 active wave）
                self._current_wave_pivots = []
                self._new_count = 0
                self._no_new_span = 0

                # Range 诞生（第六刀，v2.1 Range §2）
                # Range 在 guard break 时刻诞生，继承 transition boundary 作为 init 值
                self._range_birth_bar_dt = bar.bar_dt
                self._range_boundary_init_high = self._transition_boundary_high
                self._range_boundary_init_low = self._transition_boundary_low
                self._range_boundary_now_high = self._transition_boundary_high
                self._range_boundary_now_low = self._transition_boundary_low
                self._range_evolution_count = 0
                # Resolution 信息在 new wave 确认时填充

                # DECISION-004: range 序号在 break 诞生那根 bar 递增并定死（fixture R1：d14 诞生即 R1）
                self._range_seq += 1
                break_direction = (
                    Direction.DOWN if self._direction == Direction.UP else Direction.UP
                )
                self._active_range_snap = RangeSnapshot(
                    symbol=bar.symbol,
                    timeframe=bar.timeframe,
                    bar_dt=bar.bar_dt,
                    range_id=f"{bar.symbol}_{bar.timeframe}_R{self._range_seq}",
                    range_state=RangeState.ALIVE,
                    birth_bar_dt=bar.bar_dt,
                    boundary_init_high=self._range_boundary_init_high,
                    boundary_init_low=self._range_boundary_init_low,
                    boundary_now_high=self._range_boundary_now_high,
                    boundary_now_low=self._range_boundary_now_low,
                    break_direction=break_direction,
                    old_wave_direction=self._direction,
                    range_rule_version=RANGE_RULE_VERSION,
                    schema_version=RANGE_SNAPSHOT_SCHEMA_VERSION,
                )

                # 初始化 candidate 状态
                self._active_candidate_guard_price = None
                self._active_candidate_guard_extreme_bar_dt = None
                self._active_candidate_guard_confirm_bar_dt = None
                self._active_candidate_direction = None
                self._candidate_replacement_count = 0

                # O2 第 5 步：break 已将状态切入 Transition；若本 bar 也确认了
                # 非 break-bar 本身的 pivot，必须立刻参与 candidate/Range 演化。
                # 不能等待下一根 bar，否则同 bar 的结构事实会被快照遗漏。
                self._advance_transition(
                    bar,
                    pivots_by_confirm_dt.get(bar.bar_dt),
                )

            else:
                # D16 Progress Confirmation + D9 Guard Update（未 break 时执行；权威 O2 顺序）
                if bar.bar_dt in pivots_by_confirm_dt:
                    new_pivot = pivots_by_confirm_dt[bar.bar_dt]
                    old_progress = self._progress_extreme_price
                    self._update_progress_if_better(new_pivot)
                    # DECISION-004: D16 progress 更新时 new_count += 1、重置 no_new_span
                    if self._progress_extreme_price != old_progress:
                        self._new_count += 1
                        self._last_progress_bar_dt = bar.bar_dt
                        self._no_new_span = 0
                    self._update_guard_if_valid(new_pivot)
                    # DECISION-004: 追加到当前 wave 的 pivot 列表（Core D5 pivots：按时间顺序）
                    self._current_wave_pivots.append(new_pivot)

        # S4: Transition 期间 active candidate 演化（第四刀）
        elif self._system_state == SystemState.TRANSITION:
            # 即使本 bar 没有 pivot，也要把持续态 Range 的观察时间推进到当前 bar。
            self._advance_transition(
                bar,
                pivots_by_confirm_dt.get(bar.bar_dt),
            )

        # 产出当前 bar 的 snapshot
        snapshot = self._make_snapshot(bar)
        self._bar_index += 1  # 递增 bar 序号
        # DECISION-004: 一次性事件消费后清空冻结槽
        # terminated_wave / resolved_range 只在事件发生的 bar 上非空一次，下一根 bar 必须为 None
        # （测试 test_core_lifecycle_facts.py 行 51-52 / 74-75 强制）
        self._frozen_terminated_wave = None
        self._frozen_resolved_range = None
        return snapshot

    def _advance_transition(self, bar: PriceBar, new_pivot: Pivot | None) -> None:
        """执行 Core §9 O2 的 Transition 第 5 步。

        T9.13 撤回（2026-08-06，用户授权）：恢复 T9.11 顺序——R3 边界演化先于 T6 判定。
        确认 pivot 先按 Range §3 演化 boundary_now，R5 百分比使用演化后的 now
        （权威 R3/R5 字面组合下通常为 0）；R5 口径（pct 恒 0 是权威性质还是实现退化）
        留战役 2 单独裁决。T9.13 的正/负/零 fixture 保留为 RED 证据（测试标记 skip，待裁决后恢复）。
        """
        # 持续态 Range 每根 bar 都记录当前观察时点，保证快照时间与 Core 同步。
        if self._active_range_snap is not None:
            self._active_range_snap = replace(self._active_range_snap, bar_dt=bar.bar_dt)

        if new_pivot is None:
            return

        # Range §3：每个已确认 pivot 都检查边界演化（含 break-bar pivot）
        self._evolve_range_boundary(bar, new_pivot)

        # C-05: break bar 自身的极值不进入 candidate/T6
        if new_pivot.extreme_bar_dt == self._break_bar_dt:
            return

        # T6 双条件确认（T9.11 行为：确认 pivot 已按 R3 刷新 boundary_now）
        if self._check_new_wave_confirmation(new_pivot):
            self._enter_new_wave(new_pivot)
            return

        # T5/O4：未创建新波时，最新有效 pivot 成为 active candidate。
        self._update_active_candidate(new_pivot)

    def _evolve_range_boundary(self, bar: PriceBar, pivot: Pivot) -> None:
        """按 Range §3 更新存活 Range 的 ``boundary_now``。

        该方法只维护 Range 的统计边界，不修改 Core 固定的 transition boundary。
        T9.13 撤回（2026-08-06）：恢复 T9.11 顺序，确认 pivot 也参与 R3 演化（先演化后 T6）；
        R5 口径留战役 2 裁决。
        """
        if self._range_boundary_now_high is None or self._range_boundary_now_low is None:
            return

        boundary_changed = False
        if pivot.pivot_type == PivotType.H and pivot.price > self._range_boundary_now_high:
            self._range_boundary_now_high = pivot.price
            self._range_evolution_count += 1
            boundary_changed = True
        elif pivot.pivot_type == PivotType.L and pivot.price < self._range_boundary_now_low:
            self._range_boundary_now_low = pivot.price
            self._range_evolution_count += 1
            boundary_changed = True

        # active_range 是对外持续态对象；边界变化必须与内部状态原子同步。
        if boundary_changed and self._active_range_snap is not None:
            self._active_range_snap = replace(
                self._active_range_snap,
                bar_dt=bar.bar_dt,
                boundary_now_high=self._range_boundary_now_high,
                boundary_now_low=self._range_boundary_now_low,
                evolution_count=self._range_evolution_count,
            )

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
            # LH break: bar 的 low 突破 guard（规格 D10）
            return bar.low < self._guard_price
        elif self._system_state == SystemState.DOWN_ALIVE:
            # HL break: bar 的 high 突破 guard（规格 D10）
            return bar.high > self._guard_price

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

        # 计算 resolution_distance（引擎扩展字段：绝对突破距离仍保留 init 边界）。
        # 权威 R5 的 resolution_distance_pct 则在下方严格使用 resolution 前的
        # boundary_now；该值可正、负或零，不能把确认 pivot 先写入边界后固定为零。
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

        # DECISION-004: 冻结 resolved range facts（一次性事件；resolution 时不递增 range_seq）
        if self._active_range_snap is not None:
            if new_direction == Direction.UP:
                denom = self._range_boundary_now_high
                pct = (confirmation_pivot.price - denom) / denom if denom else 0.0
            else:
                denom = self._range_boundary_now_low
                pct = (denom - confirmation_pivot.price) / denom if denom else 0.0
            self._frozen_resolved_range = replace(
                self._active_range_snap,
                bar_dt=confirmation_pivot.confirm_bar_dt,
                range_state=RangeState.RESOLVED,
                resolution_bar_dt=confirmation_pivot.confirm_bar_dt,
                resolution_type=RangeResolutionType(self._range_resolution_type),
                resolution_distance=self._range_resolution_distance,
                resolution_distance_pct=float(pct),
                confirmation_pivot_extreme_price=confirmation_pivot.price,
                confirmation_pivot_extreme_bar_dt=confirmation_pivot.extreme_bar_dt,
                confirmation_pivot_confirm_bar_dt=confirmation_pivot.confirm_bar_dt,
                new_wave_direction=new_direction,
            )
            self._active_range_snap = None

        # DECISION-004: 新 wave 聚合重置（wave_seq 继续递增不复用——L4-6；birth_type 按方向）
        self._wave_seq += 1
        self._birth_type = (
            "continuation" if new_direction == old_wave_direction else "reversal"
        )
        self._current_wave_pivots = [confirmation_pivot]
        self._new_count = 0
        self._last_progress_bar_dt = None
        self._no_new_span = 0
        self._wave_start_price = confirmation_pivot.price

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
        self._break_price = None

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
                bar_index=self._bar_index,
                system_state=SystemState.UNINITIALIZED,
                runtime_fingerprint=runtime_fingerprint(),
            )
        else:
            # DECISION-004: 构造公开 facts 对象（alive 期间 active_wave 持续态；transition 期间 None）
            if self._system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
                active_wave_id = f"{bar.symbol}_{bar.timeframe}_{self._wave_seq}"
                active_wave = WaveSnapshot(
                    symbol=bar.symbol,
                    timeframe=bar.timeframe,
                    wave_id=active_wave_id,
                    direction=self._direction,
                    birth_type=self._birth_type,
                    wave_state=WaveCoreState.ALIVE,
                    pivots=tuple(self._current_wave_pivots),
                    start_bar_dt=self._wave_start_bar_dt,
                    start_price=self._wave_start_price,
                    progress_extreme_price=self._progress_extreme_price,
                    progress_extreme_bar_dt=self._progress_extreme_bar_dt,
                    guard_price=self._guard_price,
                    guard_bar_dt=self._guard_extreme_bar_dt,
                    bar_count=self._wave_bar_counter,
                    wave_end_price=self._progress_extreme_price,
                    primitive_count=max(len(self._current_wave_pivots) - 1, 0),
                    pivot_count=len(self._current_wave_pivots),
                    first_pivot_price=(
                        self._current_wave_pivots[0].price if self._current_wave_pivots else None
                    ),
                    new_count=self._new_count,
                    no_new_span=self._no_new_span,
                )
            else:
                active_wave_id = None
                active_wave = None

            return CoreStateSnapshot(
                symbol=bar.symbol,
                timeframe=bar.timeframe,
                bar_dt=bar.bar_dt,
                bar_index=self._bar_index,
                system_state=self._system_state,
                direction=self._direction,
                wave_core_state=self._wave_core_state,
                active_wave_id=active_wave_id,
                active_wave=active_wave,
                terminated_wave=self._frozen_terminated_wave,
                active_range=self._active_range_snap,
                resolved_range=self._frozen_resolved_range,
                current_effective_guard_price=self._guard_price,
                current_effective_guard_extreme_bar_dt=self._guard_extreme_bar_dt,
                current_effective_guard_confirm_bar_dt=self._guard_confirm_bar_dt,
                progress_extreme_price=self._progress_extreme_price,
                progress_extreme_bar_dt=self._progress_extreme_bar_dt,
                bar_count=bar_count,  # 第五刀 Task 2: 添加 bar_count
                break_bar_dt=self._break_bar_dt,
                break_price=self._break_price,
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
