"""Rank Engine - percentile_rank 计算与 peer_sample 过滤。

规格权威：MALF v2.1 Definitive (deepseek-20260726)
- 文档：MALF_03_Lifespan_v2_1-deepseek-20260726.md §4-§6
- 路径：I:\\asteria-riskbench-Definitive-validated\\MALF_Definitive_v2_1-deepseek-20260726\\

作用：计算已终止对象在历史同类中的排名（percentile_rank）

实现进度：
- ✅ T7.2：WaveLifespan rank 计算（完整）
- ✅ T7.4：RangeLifespan rank 计算（完整）

核心算法：
- percentile_rank(x, sample) = count(x_i < x) / N（严格 <，不含等于）
- 样本不足退化：N < 30 → rank = None
- 双轨分池：UP/DOWN wave 独立样本，continuation/reversal range 独立样本
"""

from malf.types import WaveLifespan, Direction, RangeLifespan, RangeResolutionType


class RankEngine:
    """Rank 计算引擎（v2.1 Lifespan §4-§6）。

    职责：
    - 计算 percentile_rank（L4-3 公式）
    - 过滤 peer_sample（同方向、防前视）
    - 计算 WaveLifespan 的 4 个 rank 字段
    - 样本不足退化（N < 30 → None）
    """

    MIN_SAMPLE_SIZE = 30  # v2.1 Lifespan §4.3

    def calculate_percentile_rank(self, x: float, sample: list[float]) -> float:
        """计算 percentile_rank（v2.1 L4-3 公式）。

        公式：percentile_rank(x, sample) = count(x_i < x) / N
        - 严格 <（不含等于）
        - 返回 [0, 1) 范围（最大值时返回 (N-1)/N）

        参数：
            x: 待计算值
            sample: 样本列表

        返回：
            percentile_rank（0.0 到接近 1.0）
        """
        if not sample:
            return 0.0

        n = len(sample)
        count_less = sum(1 for xi in sample if xi < x)
        return count_less / n

    def filter_peer_sample(
        self,
        all_waves: list[WaveLifespan],
        direction: Direction | None = None,
        cutoff_bar_dt: str | None = None
    ) -> list[WaveLifespan]:
        """过滤 peer_sample（v2.1 Lifespan §4.2）。

        过滤规则：
        - 同方向（direction 匹配）
        - 防前视（wave_end_bar_dt <= cutoff_bar_dt）
        - 不包含当前 alive wave（已在 all_waves 中过滤）

        参数：
            all_waves: 所有已终止 wave 列表
            direction: 过滤方向（None = 不过滤）
            cutoff_bar_dt: 截止日期（None = 不过滤）

        返回：
            过滤后的 WaveLifespan 列表
        """
        filtered = all_waves.copy()

        # 过滤同方向
        if direction is not None:
            filtered = [w for w in filtered if w.direction == direction]

        # 防前视
        if cutoff_bar_dt is not None:
            filtered = [w for w in filtered if w.wave_end_bar_dt <= cutoff_bar_dt]

        return filtered

    def calculate_wave_ranks(
        self,
        current_wave: WaveLifespan,
        peer_sample: list[WaveLifespan]
    ) -> dict[str, float | None]:
        """计算 WaveLifespan 的 4 个 rank 字段（v2.1 Lifespan §3）。

        计算：
        - span_rank: span_bars 的 percentile_rank
        - range_rank: price_range 的 percentile_rank
        - stagnation_rank: (span_bars / max(primitive_count, 1)) 的 percentile_rank
        - progress_rank: progress_pct 的 percentile_rank

        样本不足退化：N < 30 → 所有 rank 为 None

        参数：
            current_wave: 当前 wave
            peer_sample: 同方向已终止 wave 列表

        返回：
            字典 {"span_rank": ..., "range_rank": ..., ...}
        """
        # 样本不足退化（v2.1 Lifespan §4.3）
        if len(peer_sample) < self.MIN_SAMPLE_SIZE:
            return {
                "span_rank": None,
                "range_rank": None,
                "stagnation_rank": None,
                "progress_rank": None
            }

        # 提取样本值
        span_sample = [w.span_bars for w in peer_sample]
        range_sample = [w.price_range for w in peer_sample]
        progress_sample = [w.progress_pct for w in peer_sample]
        stagnation_sample = [
            w.span_bars / max(w.primitive_count, 1)
            for w in peer_sample
        ]

        # 计算 rank
        span_rank = self.calculate_percentile_rank(current_wave.span_bars, span_sample)
        range_rank = self.calculate_percentile_rank(current_wave.price_range, range_sample)
        progress_rank = self.calculate_percentile_rank(current_wave.progress_pct, progress_sample)

        # 计算当前 wave 的 stagnation
        current_stagnation = current_wave.span_bars / max(current_wave.primitive_count, 1)
        stagnation_rank = self.calculate_percentile_rank(current_stagnation, stagnation_sample)

        return {
            "span_rank": span_rank,
            "range_rank": range_rank,
            "stagnation_rank": stagnation_rank,
            "progress_rank": progress_rank
        }

    def update_wave_lifespan_with_ranks(
        self,
        wave: WaveLifespan,
        ranks: dict[str, float | None]
    ) -> WaveLifespan:
        """用计算的 rank 值更新 WaveLifespan 对象。

        由于 WaveLifespan 是 frozen dataclass，需要用 replace 创建新对象。

        参数：
            wave: 原始 WaveLifespan
            ranks: 计算的 rank 字典

        返回：
            更新后的 WaveLifespan
        """
        from dataclasses import replace
        return replace(
            wave,
            span_rank=ranks["span_rank"],
            range_rank=ranks["range_rank"],
            stagnation_rank=ranks["stagnation_rank"],
            progress_rank=ranks["progress_rank"]
        )

    def filter_range_peer_sample(
        self,
        all_ranges: list[RangeLifespan],
        range_type: RangeResolutionType | None = None,
        cutoff_bar_dt: str | None = None
    ) -> list[RangeLifespan]:
        """过滤 Range peer_sample（v2.1 Lifespan §5）。

        过滤条件：
        1. 同类型（continuation 或 reversal）
        2. 防前视：range_end_bar_dt <= cutoff_bar_dt

        参数：
            all_ranges: 所有已 resolved Range
            range_type: 过滤类型（None = 全部）
            cutoff_bar_dt: 防前视截止时间（None = 不过滤）

        返回：
            过滤后的 RangeLifespan 列表
        """
        filtered = all_ranges.copy()

        # 按类型过滤（continuation / reversal 分池）
        if range_type is not None:
            filtered = [r for r in filtered if r.range_type == range_type]

        # 防前视过滤
        if cutoff_bar_dt is not None:
            filtered = [r for r in filtered if r.range_end_bar_dt <= cutoff_bar_dt]

        return filtered

    def calculate_range_ranks(
        self,
        current_range: RangeLifespan,
        peer_sample: list[RangeLifespan]
    ) -> dict[str, float | None]:
        """计算 RangeLifespan 的 4 个 rank 字段（v2.1 Lifespan §5）。

        计算：
        - span_rank: span_bars 的 percentile_rank
        - evolution_rank: evolution_count 的 percentile_rank
        - replacement_rank: replacement_count 的 percentile_rank
        - resolution_distance_rank: resolution_distance_pct 的 percentile_rank

        样本不足退化：N < 30 → 所有 rank 为 None

        参数：
            current_range: 当前 Range
            peer_sample: 同类型已 resolved Range 列表

        返回：
            字典 {"span_rank": ..., "evolution_rank": ..., ...}
        """
        # 样本不足退化（v2.1 Lifespan §5.2）
        if len(peer_sample) < self.MIN_SAMPLE_SIZE:
            return {
                "span_rank": None,
                "evolution_rank": None,
                "replacement_rank": None,
                "resolution_distance_rank": None
            }

        # 提取样本值
        span_sample = [r.span_bars for r in peer_sample]
        evolution_sample = [r.evolution_count for r in peer_sample]
        replacement_sample = [r.replacement_count for r in peer_sample]
        resolution_distance_sample = [r.resolution_distance_pct for r in peer_sample]

        # 计算 rank
        span_rank = self.calculate_percentile_rank(current_range.span_bars, span_sample)
        evolution_rank = self.calculate_percentile_rank(current_range.evolution_count, evolution_sample)
        replacement_rank = self.calculate_percentile_rank(current_range.replacement_count, replacement_sample)
        resolution_distance_rank = self.calculate_percentile_rank(
            current_range.resolution_distance_pct,
            resolution_distance_sample
        )

        return {
            "span_rank": span_rank,
            "evolution_rank": evolution_rank,
            "replacement_rank": replacement_rank,
            "resolution_distance_rank": resolution_distance_rank
        }

    def update_range_lifespan_with_ranks(
        self,
        range_lifespan: RangeLifespan,
        ranks: dict[str, float | None]
    ) -> RangeLifespan:
        """用计算的 rank 值更新 RangeLifespan 对象。

        由于 RangeLifespan 是 frozen dataclass，需要用 replace 创建新对象。

        参数：
            range_lifespan: 原始 RangeLifespan
            ranks: 计算的 rank 字典

        返回：
            更新后的 RangeLifespan
        """
        from dataclasses import replace
        return replace(
            range_lifespan,
            span_rank=ranks["span_rank"],
            evolution_rank=ranks["evolution_rank"],
            replacement_rank=ranks["replacement_rank"],
            resolution_distance_rank=ranks["resolution_distance_rank"]
        )
