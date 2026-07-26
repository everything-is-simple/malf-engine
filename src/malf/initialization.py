"""L1 Core：初始化判定（D18 / O6）。

规格权威：spec §2.4（初始化序列表、O6 失败规则、【填洞 C-07】H0 替换规则）。

范围声明：
- ✅ **up 方向**的干净序列 `H0 → L1 → H2, H2 > H0`（第一刀已实现）。
- ✅ **down 方向**的干净序列 `L0 → H1 → L2, L2 < L0`（第二刀已实现，对称 up 逻辑）。
- **【填洞 C-07】H0/L0 替换**（H0/L0 确认后、L1/H1 出现前，又来一个更高的 H/更低的 L）：
  spec 只说"更高的 H 可替换 H0，且替换后需重新评估条件"，但没规定替换后
  L1 的候选范围如何变化（是否只认替换点之后的 L，还是可以是更早的 L）。
  这是一处真正的规格模糊，本刀不猜——**任何在 L1/H1 确认前出现的第二个 H/L**
  （无论高低）都显式报错，逼这条路径必须有专门 fixture 才能实现。
- **L1/H1 替换**（L1/H1 确认后、H2/L2 确认前，又来一个更低的 L/更高的 H）：spec 完全没提这一支
  是否允许替换 guard 候选。同样显式报错，不猜。

这两处留白已记入 docs/BUILD-PLAN.md「已发现待处理」，不在代码里悄悄拍死。
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


def find_initial_wave(pivots_in_confirm_order: Sequence[Pivot]) -> InitialWaveResult:
    """在按 confirm_bar_dt 排序的 pivot 序列上判定 initial wave 是否成立（D18/O6，up/down 方向）。

    参数必须已按 confirm_bar_dt 升序排列——状态机是逐 bar 推进的，看到 pivot 的时刻
    是它的 confirm_bar_dt，不是 extreme_bar_dt（§2.4 时序不对称）。本函数不做排序，
    调用方（S6 的逐 bar 循环）负责按 bar 顺序喂入。

    结构不足（O6 失败规则）时返回 confirmed=False，不抛异常——这是正常状态，
    不是错误。只有真正未实现的分支（H0/L0 替换 / L1/H1 替换）才抛
    NotImplementedError（见模块 docstring 范围声明）。
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
                # 还在等 H1；此时出现的任何第二个 L 都是【填洞 C-07】场景，未实现。
                if p.pivot_type == PivotType.L:
                    raise NotImplementedError(
                        "L0 之后、H1 确认前出现第二个 L（【填洞 C-07】替换场景）暂未实现："
                        "spec 未规定替换后 H1 候选范围如何变化，不猜。"
                    )
                h1 = p  # p.pivot_type == PivotType.H
            else:
                # H1 已定；等 L2。此时出现的任何第二个 H 是否替换 H1，spec 未提，未实现。
                if p.pivot_type == PivotType.H:
                    raise NotImplementedError(
                        "H1 确认后、L2 确认前又出现一个 H（是否替换 guard 候选）暂未实现："
                        "spec 未提及这一支，不猜。"
                    )
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
                    )
                # p.price >= l0.price：不满足严格突破（O3），继续等下一个 L（O6 失败规则）。

        return InitialWaveResult(confirmed=False)

    # Up direction: H0 → L1 → H2, H2 > H0
    h0 = first
    l1: Optional[Pivot] = None

    for p in pivots_in_confirm_order[1:]:
        if l1 is None:
            # 还在等 L1；此时出现的任何第二个 H 都是【填洞 C-07】场景，未实现。
            if p.pivot_type == PivotType.H:
                raise NotImplementedError(
                    "H0 之后、L1 确认前出现第二个 H（【填洞 C-07】替换场景）暂未实现："
                    "spec 未规定替换后 L1 候选范围如何变化，不猜。"
                )
            l1 = p  # p.pivot_type == PivotType.L
        else:
            # L1 已定；等 H2。此时出现的任何第二个 L 是否替换 L1，spec 未提，未实现。
            if p.pivot_type == PivotType.L:
                raise NotImplementedError(
                    "L1 确认后、H2 确认前又出现一个 L（是否替换 guard 候选）暂未实现："
                    "spec 未提及这一支，不猜。"
                )
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
                )
            # p.price <= h0.price：不满足严格突破（O3），继续等下一个 H（O6 失败规则）。

    return InitialWaveResult(confirmed=False)
