"""L1 Core：MALF 状态机引擎。

将 pivot detection、initialization、guard break 等模块串联起来，
实现完整的 MALF 状态机（uninitialized → up/down_alive → transition → ...）。

范围声明：
- ✅ pivot detection（k=2，延迟确认）
- ✅ initialization（up/down 方向，H0→L1→H2>H0 / L0→H1→L2<L0）
- ✅ guard break（up_alive: close < guard → transition / down_alive: close > guard → transition）
- ❌ transition 期间 active candidate 演化（第四刀）
- ❌ new wave 确认（第四刀或更后）
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

                if self._direction == Direction.UP:
                    self._system_state = SystemState.UP_ALIVE
                elif self._direction == Direction.DOWN:
                    self._system_state = SystemState.DOWN_ALIVE

        # S3: Guard break detection（up/down_alive → transition）
        elif self._system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
            if self._check_guard_break(bar):
                self._system_state = SystemState.TRANSITION
                self._wave_core_state = WaveCoreState.TERMINATED

                # Active candidate 演化（第四刀）
                raise NotImplementedError(
                    "Transition 期间 active candidate 演化未实现（第四刀）"
                )

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

    def _make_snapshot(self, bar: PriceBar) -> CoreStateSnapshot:
        """构造当前 bar 的状态快照。

        Args:
            bar: 当前价格 bar

        Returns:
            CoreStateSnapshot: 状态快照
        """
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
                runtime_fingerprint=runtime_fingerprint(),
            )
