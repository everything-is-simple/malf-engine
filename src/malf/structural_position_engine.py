"""Structural Position Engine - 结构位置计算。

规格权威：MALF v2.1 Definitive (deepseek-20260726)
- 文档：MALF_04_Structural_Position_v2_1-deepseek-20260726.md §1-§9
- 路径：I:\\asteria-riskbench-Definitive-validated\\MALF_Definitive_v2_1-deepseek-20260726\\

作用：生成 4 个结构位置视图（P1-P4）

实现进度：
- ⚠️ T8.1：P1 自身分位（实现中）
- ⏸ T8.2：P2 同向对照（待实现）
- ⏸ T8.3：P3 反向对照（待实现）
- ⏸ T8.4：P4 正反对照（待实现）

版本说明：
- v2.1 层名：Structural Position（v2.0 为 Probability）
- 语义等价：所有字段、计算逻辑与 v2.0 完全一致
- 命名变更：WaveProbabilitySnapshot → WaveStructuralSnapshot
"""

from typing import Optional, List
from statistics import mean

from malf.types import (
    WaveLifespan,
    P1SelfRank,
    P2SameDirMomentum,
    P3CrossDirMomentum,
    P4CrossCompare,
    Direction,
)


class StructuralPositionEngine:
    """Structural Position 层引擎（v2.1 Structural Position §1-§9）。

    职责：
    - 生成 P1 自身分位视图（透传 rank）
    - 生成 P2 同向对照视图（same direction momentum）
    - 生成 P3 反向对照视图（opposite direction momentum）
    - 生成 P4 正反对照视图（cross compare）
    """

    def __init__(
        self,
        same_dir_threshold: float = 0.10,
        cross_threshold: float = 0.15
    ):
        """初始化 StructuralPositionEngine。

        参数：
            same_dir_threshold: P2 标签判定阈值（默认 0.10）
            cross_threshold: P3 标签判定阈值（默认 0.15）

        注意：阈值为初始值，未经经验校准（v2.1 SP §7）。
        """
        self.same_dir_threshold = same_dir_threshold
        self.cross_threshold = cross_threshold

    # ========================================================================
    # T8.1: P1 自身分位（Self Rank）
    # ========================================================================

    def build_p1_view(self, wave_lifespan: WaveLifespan) -> P1SelfRank:
        """生成 P1 自身分位视图（v2.1 Structural Position §3）。

        P1 直接透传 WaveLifespan 的 rank 值，不做任何变换。

        参数：
            wave_lifespan: 当前 wave 的生命周期指标（含 rank 值）

        返回：
            P1SelfRank 对象

        不变量：
        - P1: P1 是 Lifespan rank 的透传，不做变换
        - P5: 所有 rank 为 None 时，不 fallback、不补零、不估计
        """
        return P1SelfRank(
            span_rank=wave_lifespan.span_rank,
            range_rank=wave_lifespan.range_rank,
            stagnation_rank=wave_lifespan.stagnation_rank,
            progress_rank=wave_lifespan.progress_rank
        )

    # ========================================================================
    # T8.2: P2 同向对照（Same Direction Momentum）
    # ========================================================================

    def build_p2_view(
        self,
        current_wave: WaveLifespan,
        terminated_waves: List[WaveLifespan]
    ) -> P2SameDirMomentum:
        """生成 P2 同向对照视图（v2.1 Structural Position §4）。

        比较当前 wave（W0）与最近 1-3 个同方向已终止波。

        参数：
            current_wave: 当前 wave（W0）
            terminated_waves: 已终止波列表（按时间倒序，W-1, W-2, W-3, ...）

        返回：
            P2SameDirMomentum 对象

        不变量：
        - P2: P2/P3/P4 的 momentum 是 rank 的向量差，不是概率
        - P3: 标签（accelerating 等）是辅助性的，rank 值始终保留
        """
        # 1. 筛选同向波（从 W-1, W-2, W-3 中选）
        same_dir_peers = [
            w for w in terminated_waves[:3]
            if w.direction == current_wave.direction
        ]

        # 2. 如果无同向波，返回全 None（P5 不变量）
        if not same_dir_peers:
            return P2SameDirMomentum(
                same_dir_span_momentum=None,
                same_dir_range_momentum=None,
                same_dir_stagnation_momentum=None,
                same_dir_label=None
            )

        # 3. 如果当前 wave 的 rank 为 None，返回全 None（P5 不变量）
        if (current_wave.span_rank is None or
            current_wave.range_rank is None or
            current_wave.stagnation_rank is None):
            return P2SameDirMomentum(
                same_dir_span_momentum=None,
                same_dir_range_momentum=None,
                same_dir_stagnation_momentum=None,
                same_dir_label=None
            )

        # 4. 计算 momentum（rank 向量差）
        span_momentum = self._calculate_momentum(
            current_wave.span_rank,
            [w.span_rank for w in same_dir_peers]
        )
        range_momentum = self._calculate_momentum(
            current_wave.range_rank,
            [w.range_rank for w in same_dir_peers]
        )
        stagnation_momentum = self._calculate_momentum(
            current_wave.stagnation_rank,
            [w.stagnation_rank for w in same_dir_peers]
        )

        # 5. 如果任一 momentum 计算失败（peer rank 为 None），返回全 None
        if (span_momentum is None or
            range_momentum is None or
            stagnation_momentum is None):
            return P2SameDirMomentum(
                same_dir_span_momentum=None,
                same_dir_range_momentum=None,
                same_dir_stagnation_momentum=None,
                same_dir_label=None
            )

        # 6. 计算标签（基于 avg_momentum）
        avg_momentum = (span_momentum + range_momentum + stagnation_momentum) / 3
        label = self._label_same_dir_momentum(avg_momentum)

        return P2SameDirMomentum(
            same_dir_span_momentum=span_momentum,
            same_dir_range_momentum=range_momentum,
            same_dir_stagnation_momentum=stagnation_momentum,
            same_dir_label=label
        )

    def _calculate_momentum(
        self,
        current_rank: Optional[float],
        peer_ranks: List[Optional[float]]
    ) -> Optional[float]:
        """计算 momentum（当前 rank - 历史 rank 平均值）。

        参数：
            current_rank: 当前 wave 的 rank
            peer_ranks: 历史波的 rank 列表

        返回：
            momentum 值，如果无法计算则返回 None
        """
        # 过滤掉 None 值
        valid_peer_ranks = [r for r in peer_ranks if r is not None]

        # 如果没有有效 peer rank，返回 None
        if not valid_peer_ranks:
            return None

        # 如果当前 rank 为 None，返回 None
        if current_rank is None:
            return None

        # 计算 momentum = 当前 rank - 历史平均 rank
        peer_mean = mean(valid_peer_ranks)
        return current_rank - peer_mean

    def _label_same_dir_momentum(self, avg_momentum: float) -> str:
        """根据平均 momentum 生成标签（v2.1 SP §4）。

        参数：
            avg_momentum: 三个 momentum 的平均值

        返回：
            "accelerating" | "decelerating" | "flat"
        """
        if avg_momentum > self.same_dir_threshold:
            return "accelerating"
        elif avg_momentum < -self.same_dir_threshold:
            return "decelerating"
        else:
            return "flat"

    # ========================================================================
    # T8.3: P3 反向对照（Opposite Direction Momentum）
    # ========================================================================

    def build_p3_view(
        self,
        current_wave: WaveLifespan,
        terminated_waves: List[WaveLifespan]
    ) -> P3CrossDirMomentum:
        """生成 P3 反向对照视图（v2.1 Structural Position §5）。

        比较当前 wave（W0）与最近 1-3 个反方向已终止波。

        参数：
            current_wave: 当前 wave（W0）
            terminated_waves: 已终止波列表（按时间倒序，W-1, W-2, W-3, ...）

        返回：
            P3CrossDirMomentum 对象

        不变量：
        - P2: P2/P3/P4 的 momentum 是 rank 的向量差，不是概率
        - P3: 标签（self_dominant 等）是辅助性的，rank 值始终保留
        """
        # 1. 筛选反向波（从 W-1, W-2, W-3 中选）
        cross_dir_peers = [
            w for w in terminated_waves[:3]
            if w.direction != current_wave.direction
        ]

        # 2. 如果无反向波，返回全 None（P5 不变量）
        if not cross_dir_peers:
            return P3CrossDirMomentum(
                cross_dir_span_momentum=None,
                cross_dir_range_momentum=None,
                cross_dir_stagnation_momentum=None,
                cross_dir_label=None
            )

        # 3. 如果当前 wave 的 rank 为 None，返回全 None（P5 不变量）
        if (current_wave.span_rank is None or
            current_wave.range_rank is None or
            current_wave.stagnation_rank is None):
            return P3CrossDirMomentum(
                cross_dir_span_momentum=None,
                cross_dir_range_momentum=None,
                cross_dir_stagnation_momentum=None,
                cross_dir_label=None
            )

        # 4. 计算 momentum（rank 向量差）
        span_momentum = self._calculate_momentum(
            current_wave.span_rank,
            [w.span_rank for w in cross_dir_peers]
        )
        range_momentum = self._calculate_momentum(
            current_wave.range_rank,
            [w.range_rank for w in cross_dir_peers]
        )
        stagnation_momentum = self._calculate_momentum(
            current_wave.stagnation_rank,
            [w.stagnation_rank for w in cross_dir_peers]
        )

        # 5. 如果任一 momentum 计算失败（peer rank 为 None），返回全 None
        if (span_momentum is None or
            range_momentum is None or
            stagnation_momentum is None):
            return P3CrossDirMomentum(
                cross_dir_span_momentum=None,
                cross_dir_range_momentum=None,
                cross_dir_stagnation_momentum=None,
                cross_dir_label=None
            )

        # 6. 计算标签（基于 avg_momentum）
        avg_momentum = (span_momentum + range_momentum + stagnation_momentum) / 3
        label = self._label_cross_dir_momentum(avg_momentum)

        return P3CrossDirMomentum(
            cross_dir_span_momentum=span_momentum,
            cross_dir_range_momentum=range_momentum,
            cross_dir_stagnation_momentum=stagnation_momentum,
            cross_dir_label=label
        )

    def _label_cross_dir_momentum(self, avg_momentum: float) -> str:
        """根据平均 momentum 生成标签（v2.1 SP §5）。

        参数：
            avg_momentum: 三个 momentum 的平均值

        返回：
            "self_dominant" | "opposite_dominant" | "balanced"
        """
        if avg_momentum > self.cross_threshold:
            return "self_dominant"
        elif avg_momentum < -self.cross_threshold:
            return "opposite_dominant"
        else:
            return "balanced"

    # ========================================================================
    # T8.4: P4 正反对照（Cross Compare）
    # ========================================================================

    def build_p4_view(
        self,
        current_wave: WaveLifespan,
        w_minus_1: Optional[WaveLifespan],
        current_wave_is_alive: bool
    ) -> P4CrossCompare:
        """生成 P4 正反对照视图（v2.1 Structural Position §6）。

        比较当前 wave（W0）与最近已终止波（W-1，任意方向）。

        参数：
            current_wave: 当前 wave（W0）
            w_minus_1: 最近已终止波（W-1），可能为 None
            current_wave_is_alive: 当前 wave 是否为 alive

        返回：
            P4CrossCompare 对象

        不变量：
        - P2: P2/P3/P4 的 momentum 是 rank 的向量差，不是概率
        - P4: P4 的 cross_alive_warning 必须真实反映当前 wave 的 alive 状态
        """
        # 1. 如果 W-1 不存在，返回全 None（P5 不变量）
        if w_minus_1 is None:
            return P4CrossCompare(
                cross_span_momentum=None,
                cross_range_momentum=None,
                cross_stagnation_momentum=None,
                cross_alive_warning=current_wave_is_alive
            )

        # 2. 如果当前 wave 或 W-1 的 rank 为 None，返回全 None（P5 不变量）
        if (current_wave.span_rank is None or
            current_wave.range_rank is None or
            current_wave.stagnation_rank is None or
            w_minus_1.span_rank is None or
            w_minus_1.range_rank is None or
            w_minus_1.stagnation_rank is None):
            return P4CrossCompare(
                cross_span_momentum=None,
                cross_range_momentum=None,
                cross_stagnation_momentum=None,
                cross_alive_warning=current_wave_is_alive
            )

        # 3. 计算 momentum（W0 - W-1）
        cross_span_momentum = current_wave.span_rank - w_minus_1.span_rank
        cross_range_momentum = current_wave.range_rank - w_minus_1.range_rank
        cross_stagnation_momentum = current_wave.stagnation_rank - w_minus_1.stagnation_rank

        return P4CrossCompare(
            cross_span_momentum=cross_span_momentum,
            cross_range_momentum=cross_range_momentum,
            cross_stagnation_momentum=cross_stagnation_momentum,
            cross_alive_warning=current_wave_is_alive
        )
