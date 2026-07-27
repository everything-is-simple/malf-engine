"""Lifespan Engine - 生命周期统计计算。

规格权威：MALF v2.1 Definitive (deepseek-20260726)
- 文档：MALF_03_Lifespan_v2_1-deepseek-20260726.md §1-§7
- 路径：I:\\asteria-riskbench-Definitive-validated\\MALF_Definitive_v2_1-deepseek-20260726\\

作用：为已终止的 Wave 和 Range 计算生命周期指标

实现进度：
- ✅ T7.1：WaveLifespan 指标计算（完整）
- ✅ T7.2：WaveLifespan peer_sample + rank（由 rank_engine.py 实现）
- ✅ T7.3：RangeLifespan 指标计算（完整）
- ⏸ T7.4：RangeLifespan peer_sample + rank（待实现）
"""

from malf.types import (
    CoreStateSnapshot,
    WaveLifespan,
    RangeLifespan,
    Direction,
    WaveCoreState,
    RangeResolutionType,
)


class LifespanEngine:
    """Lifespan 层引擎（v2.1 Lifespan §1-§7）。

    职责：
    - 计算已终止 Wave 的生命周期指标（WaveLifespan）
    - 计算已 resolved Range 的生命周期指标（RangeLifespan）
    - 不做排名计算（percentile_rank 由 RankEngine 处理）
    """

    def __init__(self):
        """初始化 LifespanEngine。"""
        self._terminated_waves = []  # 已终止 wave 历史
        self._resolved_ranges = []   # 已 resolved range 历史

    def calculate_wave_lifespan(
        self,
        wave_id: str,
        symbol: str,
        timeframe: str,
        direction: Direction,
        wave_start_bar_dt: str,
        wave_start_price: int,
        wave_end_bar_dt: str,
        wave_end_price: int,
        span_bars: int,
        primitive_count: int,
        pivot_count: int,
        new_count: int,
        no_new_span: int,
        first_pivot_price: int,
        guard_price: int
    ) -> WaveLifespan:
        """计算 Wave 生命周期指标（v2.1 Lifespan §3）。

        参数：
            wave_id: Wave 唯一标识
            symbol: 标的代码
            timeframe: 时间周期
            direction: Wave 方向（UP/DOWN）
            wave_start_bar_dt: Wave 开始时间（confirmation bar）
            wave_start_price: Wave 起始价格（L4-2: confirmation_price）
            wave_end_bar_dt: Wave 结束时间（break bar）
            wave_end_price: Wave 结束价格（progress_extreme）
            span_bars: 持续 bar 数
            primitive_count: 初始化原语数量（3）
            pivot_count: 总 pivot 数量
            new_count: Alive 期间新确认 pivot 数量
            no_new_span: 最后新 pivot 到 break 的 bar 数
            first_pivot_price: 初始化时第一个 pivot 价格（progress_extreme at init）
            guard_price: Guard 价格

        返回：
            WaveLifespan 对象
        """
        # 计算价格范围（绝对值）
        price_range = abs(wave_end_price - wave_start_price)

        # 计算进展百分比（v2.1 Lifespan §3.1）
        # UP: (progress_extreme_price - first_pivot_price) / (progress_extreme_price - guard_price)
        # DOWN: (first_pivot_price - progress_extreme_price) / (guard_price - progress_extreme_price)
        if direction == Direction.UP:
            numerator = wave_end_price - first_pivot_price
            denominator = wave_end_price - guard_price
        else:  # Direction.DOWN
            numerator = first_pivot_price - wave_end_price
            denominator = guard_price - wave_end_price

        # 避免除以零
        if denominator == 0:
            progress_pct = 0.0
        else:
            progress_pct = numerator / denominator

        # 创建 WaveLifespan 对象（排名字段初始为 None）
        return WaveLifespan(
            wave_id=wave_id,
            symbol=symbol,
            timeframe=timeframe,
            direction=direction,
            wave_start_bar_dt=wave_start_bar_dt,
            wave_end_bar_dt=wave_end_bar_dt,
            span_bars=span_bars,
            wave_start_price=wave_start_price,
            wave_end_price=wave_end_price,
            price_range=price_range,
            progress_pct=progress_pct,
            primitive_count=primitive_count,
            pivot_count=pivot_count,
            new_count=new_count,
            no_new_span=no_new_span,
            # 排名字段由后续 RankEngine 填充
            span_rank=None,
            range_rank=None,
            stagnation_rank=None,
            progress_rank=None
        )

    def record_terminated_wave(self, lifespan: WaveLifespan) -> None:
        """记录已终止 wave 到历史池（用于后续排名）。

        参数：
            lifespan: 已计算的 WaveLifespan 对象
        """
        self._terminated_waves.append(lifespan)

    def get_terminated_waves(self, direction: Direction | None = None) -> list[WaveLifespan]:
        """获取已终止 wave 历史（用于 peer_sample）。

        参数：
            direction: 过滤方向（None = 全部）

        返回：
            WaveLifespan 列表
        """
        if direction is None:
            return self._terminated_waves.copy()
        return [w for w in self._terminated_waves if w.direction == direction]

    def calculate_range_lifespan(
        self,
        range_id: str,
        symbol: str,
        timeframe: str,
        range_type: RangeResolutionType,
        range_start_bar_dt: str,
        range_end_bar_dt: str,
        span_bars: int,
        evolution_count: int,
        replacement_count: int,
        resolution_distance: int,
        boundary_high_init: int,
        boundary_low_init: int,
        boundary_high_now: int,
        boundary_low_now: int,
        resolution_type: str,
        confirmation_pivot_extreme_price: int
    ) -> RangeLifespan:
        """计算 Range 生命周期指标（v2.1 Lifespan §2）。

        参数：
            range_id: Range 唯一标识
            symbol: 标的代码
            timeframe: 时间周期
            range_type: Range 类型（continuation / reversal）
            range_start_bar_dt: Range 开始时间（break bar）
            range_end_bar_dt: Range 结束时间（resolution bar）
            span_bars: 持续 bar 数
            evolution_count: Boundary 演化次数
            replacement_count: Candidate 替换次数
            resolution_distance: Resolution 距离（有符号整数）
            boundary_high_init: 初始上边界
            boundary_low_init: 初始下边界
            boundary_high_now: 当前上边界
            boundary_low_now: 当前下边界
            resolution_type: Resolution 方向（"up" / "down"）
            confirmation_pivot_extreme_price: 确认 pivot 的极值价格

        返回：
            RangeLifespan 对象
        """
        # 计算 boundary_init 幅度
        amplitude_init = boundary_high_init - boundary_low_init

        # 计算 boundary_now 幅度
        amplitude_now = boundary_high_now - boundary_low_now

        # 计算 amplitude_pct（v2.1 Lifespan §2.1）
        # amplitude_pct = amplitude_now / boundary_low_init
        # 注意：boundary_low_init 不会为 0（价格必 > 0）
        amplitude_pct = amplitude_now / boundary_low_init

        # 计算 resolution_distance_pct（v2.1 Range §5）
        # UP 突破：(confirmation_pivot.extreme_price - boundary_high_now) / boundary_high_now
        # DOWN 突破：(boundary_low_now - confirmation_pivot.extreme_price) / boundary_low_now
        if resolution_type == "up":
            if boundary_high_now != 0:
                resolution_distance_pct = (
                    confirmation_pivot_extreme_price - boundary_high_now
                ) / boundary_high_now
            else:
                resolution_distance_pct = 0.0
        elif resolution_type == "down":
            if boundary_low_now != 0:
                resolution_distance_pct = (
                    boundary_low_now - confirmation_pivot_extreme_price
                ) / boundary_low_now
            else:
                resolution_distance_pct = 0.0
        else:
            # 未知 resolution_type，防御性编程
            resolution_distance_pct = 0.0

        # 创建 RangeLifespan 对象（排名字段初始为 None）
        return RangeLifespan(
            range_id=range_id,
            symbol=symbol,
            timeframe=timeframe,
            range_type=range_type,
            range_start_bar_dt=range_start_bar_dt,
            range_end_bar_dt=range_end_bar_dt,
            span_bars=span_bars,
            evolution_count=evolution_count,
            replacement_count=replacement_count,
            resolution_distance=resolution_distance,
            resolution_distance_pct=resolution_distance_pct,
            amplitude_init=amplitude_init,
            amplitude_now=amplitude_now,
            amplitude_pct=amplitude_pct,
            # 排名字段由后续 RankEngine 填充
            span_rank=None,
            evolution_rank=None,
            replacement_rank=None,
            resolution_distance_rank=None
        )

    def record_resolved_range(self, lifespan: RangeLifespan) -> None:
        """记录已 resolved range 到历史池（用于后续排名）。

        参数：
            lifespan: 已计算的 RangeLifespan 对象
        """
        self._resolved_ranges.append(lifespan)

    def get_resolved_ranges(
        self, range_type: RangeResolutionType | None = None
    ) -> list[RangeLifespan]:
        """获取已 resolved range 历史（用于 peer_sample）。

        参数：
            range_type: 过滤类型（None = 全部）

        返回：
            RangeLifespan 列表
        """
        if range_type is None:
            return self._resolved_ranges.copy()
        return [r for r in self._resolved_ranges if r.range_type == range_type]

