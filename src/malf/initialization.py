"""MALF Initialization - 初始化判定。

本模块实现 MALF v2.1 Core §3（D18 初始波创建 / O6 初始化失败规则）。

规格权威：MALF v2.1 Core §3

范围声明：
- ✅ **up 方向**的干净序列 `H0 → L1 → H2, H2 > H0`（第一刀已实现）。
- ✅ **down 方向**的干净序列 `L0 → H1 → L2, L2 < L0`（第二刀已实现，对称 up 逻辑）。
- ✅ **【C-07】H0/L0 替换**（H0/L0 确认后、L1/H1 出现前，又来一个更高的 H/更低的 L）：
  选择"更极端"的 pivot 作为初始参考点。更高的 H 替换 H0，更低的 L 替换 L0。
  替换后从新位置继续，不回溯历史 pivot（保持单遍处理）。
- ✅ **【C-07】L1/H1 替换**（L1/H1 确认后、H2/L2 确认前，又来一个更低的 L/更高的 H）：
  选择"最极端"的 guard 候选。更低的 L 替换 L1（UP 方向），更高的 H 替换 H1（DOWN 方向）。

实现策略：使用状态机追踪 first/second pivot，遇到同类型 pivot 时判定是否替换（更极端则替换）。
详细设计参见 docs/C07-RULE-ANALYSIS.md。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from malf.types import Direction, Pivot, PivotType


@dataclass(frozen=True)
class InitialWaveResult:
    """find_initial_wave 的产出。confirmed=False 时其余字段均为 None（O6 失败规则：保持 uninitialized）。"""

    confirmed: bool
    direction: Optional[Direction] = None
    confirm_bar_dt: Optional[str] = None
    guard_price: Optional[int] = None
    guard_extreme_bar_dt: Optional[str] = None
    guard_confirm_bar_dt: Optional[str] = None
    progress_extreme_price: Optional[int] = None
    progress_extreme_bar_dt: Optional[str] = None
    pivots: tuple[Pivot, ...] = ()
    birth_type: str = "initial"


def find_initial_wave(pivots_in_confirm_order: Sequence[Pivot]) -> InitialWaveResult:
    """在按 confirm_bar_dt 排序的 pivot 序列上判定 initial wave 是否成立（D18/O6，up/down 方向）。

    参数必须已按 confirm_bar_dt 升序排列——状态机是逐 bar 推进的，看到 pivot 的时刻
    是它的 confirm_bar_dt，不是 extreme_bar_dt（§2.4 时序不对称）。本函数不做排序，
    调用方（S6 的逐 bar 循环）负责按 bar 顺序喂入。

    结构不足（O6 失败规则）时返回 confirmed=False，不抛异常——这是正常状态，
    不是错误。

    实现 C-07 替换规则：
    - H0/L0 替换：更高的 H 替换 H0，更低的 L 替换 L0
    - L1/H1 替换：更低的 L 替换 L1，更高的 H 替换 H1
    - 不满足替换条件（不够极端）的 pivot 被忽略
    """
    if not pivots_in_confirm_order:
        return InitialWaveResult(confirmed=False)

    first = pivots_in_confirm_order[0]

    # Down direction: L0 → H1 → L2, L2 < L0
    if first.pivot_type == PivotType.L:
        l0 = first
        h1: Optional[Pivot] = None

        for p in pivots_in_confirm_order[1:]:
            if h1 is None:
                # 等待 H1；如果出现第二个 L，检查是否替换 L0（C-07 规则）
                if p.pivot_type == PivotType.L:
                    if p.price < l0.price:
                        # 更低的 L 替换 L0
                        l0 = p
                    # else: 不够低，忽略
                    continue
                h1 = p  # p.pivot_type == PivotType.H
            else:
                # H1 已定；等 L2。如果出现第二个 H，检查是否替换 H1（C-07 规则）
                if p.pivot_type == PivotType.H:
                    if p.price > h1.price:
                        # 更高的 H 替换 H1
                        h1 = p
                    # else: 不够高，忽略
                    continue
                # p.pivot_type == PivotType.L，检查 L2 < L0
                if p.price < l0.price:
                    return InitialWaveResult(
                        confirmed=True,
                        direction=Direction.DOWN,
                        confirm_bar_dt=p.confirm_bar_dt,
                        guard_price=h1.price,
                        guard_extreme_bar_dt=h1.extreme_bar_dt,
                        guard_confirm_bar_dt=h1.confirm_bar_dt,
                        progress_extreme_price=p.price,
                        progress_extreme_bar_dt=p.extreme_bar_dt,
                        pivots=(l0, h1, p),
                    )
                # p.price >= l0.price：不满足严格突破（O3），继续等下一个 L（O6 失败规则）。

        return InitialWaveResult(confirmed=False)

    # Up direction: H0 → L1 → H2, H2 > H0
    h0 = first
    l1: Optional[Pivot] = None

    for p in pivots_in_confirm_order[1:]:
        if l1 is None:
            # 等待 L1；如果出现第二个 H，检查是否替换 H0（C-07 规则）
            if p.pivot_type == PivotType.H:
                if p.price > h0.price:
                    # 更高的 H 替换 H0
                    h0 = p
                # else: 不够高，忽略
                continue
            l1 = p  # p.pivot_type == PivotType.L
        else:
            # L1 已定；等 H2。如果出现第二个 L，检查是否替换 L1（C-07 规则）
            if p.pivot_type == PivotType.L:
                if p.price < l1.price:
                    # 更低的 L 替换 L1
                    l1 = p
                # else: 不够低，忽略
                continue
            if p.price > h0.price:
                return InitialWaveResult(
                    confirmed=True,
                    direction=Direction.UP,
                    confirm_bar_dt=p.confirm_bar_dt,
                    guard_price=l1.price,
                    guard_extreme_bar_dt=l1.extreme_bar_dt,
                    guard_confirm_bar_dt=l1.confirm_bar_dt,
                    progress_extreme_price=p.price,
                    progress_extreme_bar_dt=p.extreme_bar_dt,
                    pivots=(h0, l1, p),
                )
            # p.price <= h0.price：不满足严格突破（O3），继续等下一个 H（O6 失败规则）。

    return InitialWaveResult(confirmed=False)
