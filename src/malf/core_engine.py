"""L1 Core：MALF 状态机引擎。

将 pivot detection、initialization、guard break 等模块串联起来，
实现完整的 MALF 状态机（uninitialized → up/down_alive → transition → new wave）。

范围声明：
- ✅ pivot detection（k=2，延迟确认）
- ✅ initialization（up/down 方向，H0→L1→H2>H0 / L0→H1→L2<L0）
- ✅ guard break（up_alive: close < guard → transition / down_alive: close > guard → transition）
- ✅ transition 期间 active candidate 演化（第四刀）
- ✅ new wave 确认（第四刀）
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

        # Transition 相关信息（第四刀）
        self._transition_boundary_high: Optional[int] = None
        self._transition_boundary_low: Optional[int] = None
        self._active_candidate_guard_price: Optional[int] = None
        self._active_candidate_guard_extreme_bar_dt: Optional[str] = None
        self._active_candidate_guard_confirm_bar_dt: Optional[str] = None
        self._active_candidate_direction: Optional[Direction] = None
        self._candidate_replacement_count: int = 0
        self._break_bar_dt: Optional[str] = None  # 记录 break bar 的时间（用于 C-05）

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

                if self._direction == Direction.UP:
                    self._system_state = SystemState.UP_ALIVE
                elif self._direction == Direction.DOWN:
                    self._system_state = SystemState.DOWN_ALIVE

        # S3: Guard break detection（up/down_alive → transition）
        elif self._system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
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
        """
        # 确定新波方向
        if confirmation_pivot.pivot_type == PivotType.H:
            new_direction = Direction.UP
            self._system_state = SystemState.UP_ALIVE
        else:
            new_direction = Direction.DOWN
            self._system_state = SystemState.DOWN_ALIVE

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
        bar_count = None
        if self._wave_start_bar_dt is not None:
            # 计算从 wave 开始到当前 bar 的数量
            start_idx = None
            current_idx = None
            for i, b in enumerate(self._bars):
                if b.bar_dt == self._wave_start_bar_dt:
                    start_idx = i
                if b.bar_dt == bar.bar_dt:
                    current_idx = i

            if start_idx is not None and current_idx is not None:
                bar_count = current_idx - start_idx + 1

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
                runtime_fingerprint=runtime_fingerprint(),
            )
