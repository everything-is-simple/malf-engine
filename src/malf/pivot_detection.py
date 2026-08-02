"""MALF Pivot Detection - 分形k=2延迟确认。

本模块实现 MALF v2.1 Core §2.4（D2 Pivot 检测规则）。

规格权威：MALF v2.1 Core §2.4
- Pivot 定义（D2）：确认的高点或低点
- 检测算法：fractal k=2（参数可配置但默认k=2）
- 时序不对称：极值发生在i，确认发生在i+k

算法（fractal，参数 k）：
    对每个下标 i（要求左右各有 k 根，即 k <= i <= len(bars)-1-k）：
      - H pivot：bars[i].high 严格大于窗口 [i-k, i+k] 内其余 2k 根的 high
      - L pivot：bars[i].low  严格小于窗口 [i-k, i+k] 内其余 2k 根的 low
    极值发生在 i（extreme_bar_dt = bars[i].bar_dt）。
    确认发生在 i+k（confirm_bar_dt = bars[i+k].bar_dt）——因为要等右侧 k 根出现才能判定
    "严格最优"，这是时序不对称的来源：极值早就发生了，但要延迟 k 根才能确认。

本模块只产出 pivot 列表，不含任何状态机 / guard / wave 逻辑。
零依赖：仅用 malf.types。
"""

from __future__ import annotations

from typing import List, Sequence

from malf.types import Pivot, PivotType, PriceBar


def detect_pivots(bars: Sequence[PriceBar], k: int) -> List[Pivot]:
    """在 bars 上跑分形 k 窗口检测，按 extreme 发生的时间顺序返回 pivot 列表。

    k 必须为正整数（k=0 没有意义：窗口退化为空，任何 bar 都会被判定为"严格最优"）。
    窗口不足（len(bars) < 2k+1）时返回空列表，不抛异常——这是正常的初始化期状态。
    """
    if k <= 0:
        raise ValueError(f"k 必须为正整数，got {k!r}")

    n = len(bars)
    pivots: List[Pivot] = []

    for i in range(k, n - k):
        window_idx = [j for j in range(i - k, i + k + 1) if j != i]

        is_high = all(bars[i].high > bars[j].high for j in window_idx)
        is_low = all(bars[i].low < bars[j].low for j in window_idx)

        confirm_bar = bars[i + k]

        if is_high:
            pivots.append(
                Pivot(
                    pivot_type=PivotType.H,
                    price=bars[i].high,
                    extreme_bar_dt=bars[i].bar_dt,
                    confirm_bar_dt=confirm_bar.bar_dt,
                    confirm_price=confirm_bar.close,  # 确认 bar 的 close（规格 D2）
                )
            )
        if is_low:
            pivots.append(
                Pivot(
                    pivot_type=PivotType.L,
                    price=bars[i].low,
                    extreme_bar_dt=bars[i].bar_dt,
                    confirm_bar_dt=confirm_bar.bar_dt,
                    confirm_price=confirm_bar.close,  # 确认 bar 的 close（规格 D2）
                )
            )

    return pivots
