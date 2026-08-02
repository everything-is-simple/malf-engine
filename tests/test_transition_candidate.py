"""第四刀单元测试：Transition 期间 Active Candidate 演化。

测试范围：
- 双边界计算（D12）
- 首个 candidate 检测
- Candidate 替换（同向 refresh + 反向 flip-flop）
- New wave 确认（有/无 candidate）
"""

import pytest

from malf.core_engine import MALFCoreEngine
from malf.types import Direction, PriceBar, PivotType, SystemState, WaveCoreState


def test_boundary_calculation_up_break():
    """测试 UP 方向 break 后的双边界计算。

    旧波：up_alive (H0→L1→H2>H0)
    Break: close < L1 (guard)
    预期：
    - boundary_high = H2 (old final HH)
    - boundary_low = L1 (broken guard)
    """
    engine = MALFCoreEngine(k=2)

    # 窗口填充
    bars = [
        PriceBar("TEST", "D1", "2024-01-01", 110, 115, 105, 110),
        PriceBar("TEST", "D1", "2024-01-02", 110, 115, 105, 112),
    ]

    # H0→L1→H2>H0 → up_alive
    bars += [
        PriceBar("TEST", "D1", "2024-01-03", 112, 120, 110, 115),  # H0 extreme
        PriceBar("TEST", "D1", "2024-01-04", 115, 118, 105, 110),
        PriceBar("TEST", "D1", "2024-01-05", 110, 115, 100, 105),  # H0 confirmed; L1 extreme
        PriceBar("TEST", "D1", "2024-01-06", 105, 130, 110, 128),  # L1 右1; H2 extreme
        PriceBar("TEST", "D1", "2024-01-07", 128, 128, 115, 125),  # L1 confirmed
        PriceBar("TEST", "D1", "2024-01-08", 125, 125, 120, 122),  # H2 confirmed → up_alive
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 验证 up_alive
    assert snapshot.system_state == SystemState.UP_ALIVE
    assert snapshot.direction == Direction.UP
    assert snapshot.wave_core_state == WaveCoreState.ALIVE
    assert snapshot.current_effective_guard_price == 100  # L1
    assert snapshot.progress_extreme_price == 130  # H2

    # Guard break
    break_bar = PriceBar("TEST", "D1", "2024-01-09", 122, 127, 95, 95)  # close < guard
    snapshot = engine.on_bar(break_bar)

    # 验证 transition + 双边界
    assert snapshot.system_state == SystemState.TRANSITION
    assert snapshot.wave_core_state == WaveCoreState.TERMINATED
    assert snapshot.transition_boundary_high == 130  # old final HH (H2)
    assert snapshot.transition_boundary_low == 100   # broken guard (L1)


def test_boundary_calculation_down_break():
    """测试 DOWN 方向 break 后的双边界计算（对称实现）。

    旧波：down_alive (L0→H1→L2<L0)
    Break: close > H1 (guard)
    预期：
    - boundary_high = H1 (broken guard)
    - boundary_low = L2 (old final LL)
    """
    engine = MALFCoreEngine(k=2)

    # 窗口填充
    bars = [
        PriceBar("TEST", "D1", "2024-01-01", 110, 115, 105, 110),
        PriceBar("TEST", "D1", "2024-01-02", 110, 115, 105, 108),
    ]

    # L0→H1→L2<L0 → down_alive
    bars += [
        PriceBar("TEST", "D1", "2024-01-03", 108, 110, 100, 105),  # L0 extreme
        PriceBar("TEST", "D1", "2024-01-04", 105, 112, 101, 110),
        PriceBar("TEST", "D1", "2024-01-05", 110, 115, 102, 112),  # L0 confirmed; H1 extreme
        PriceBar("TEST", "D1", "2024-01-06", 112, 113, 90, 92),    # H1 右1; L2 extreme
        PriceBar("TEST", "D1", "2024-01-07", 92, 100, 91, 95),     # H1 confirmed
        PriceBar("TEST", "D1", "2024-01-08", 95, 98, 93, 96),      # L2 confirmed → down_alive
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 验证 down_alive
    assert snapshot.system_state == SystemState.DOWN_ALIVE
    assert snapshot.direction == Direction.DOWN
    assert snapshot.wave_core_state == WaveCoreState.ALIVE
    assert snapshot.current_effective_guard_price == 115  # H1
    assert snapshot.progress_extreme_price == 90  # L2

    # Guard break
    break_bar = PriceBar("TEST", "D1", "2024-01-09", 96, 120, 95, 118)  # close > guard
    snapshot = engine.on_bar(break_bar)

    # 验证 transition + 双边界
    assert snapshot.system_state == SystemState.TRANSITION
    assert snapshot.wave_core_state == WaveCoreState.TERMINATED
    assert snapshot.transition_boundary_high == 115  # broken guard (H1)
    assert snapshot.transition_boundary_low == 90    # old final LL (L2)


def test_first_candidate_detection():
    """测试首个 active candidate 检测。

    场景：UP → transition → L0 candidate
    验证：
    - transition 状态下首个反向 pivot 成为 active candidate
    - active_candidate_direction 正确设置
    """
    engine = MALFCoreEngine(k=2)

    # 复用场景 A 的前 9 根 bars（到 transition）
    bars = [
        PriceBar("TEST", "D1", "2024-01-01", 110, 115, 105, 110),
        PriceBar("TEST", "D1", "2024-01-02", 110, 115, 105, 112),
        PriceBar("TEST", "D1", "2024-01-03", 112, 120, 110, 115),
        PriceBar("TEST", "D1", "2024-01-04", 115, 118, 105, 110),
        PriceBar("TEST", "D1", "2024-01-05", 110, 115, 100, 105),
        PriceBar("TEST", "D1", "2024-01-06", 105, 130, 110, 128),
        PriceBar("TEST", "D1", "2024-01-07", 128, 128, 115, 125),
        PriceBar("TEST", "D1", "2024-01-08", 125, 125, 120, 122),
        PriceBar("TEST", "D1", "2024-01-09", 122, 127, 95, 95),  # → transition
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 验证进入 transition
    assert snapshot.system_state == SystemState.TRANSITION
    assert snapshot.active_candidate_guard_price is None  # 尚无 candidate

    # L0 candidate 出现并确认
    bars = [
        PriceBar("TEST", "D1", "2024-01-10", 95, 100, 90, 92),   # L0 extreme
        PriceBar("TEST", "D1", "2024-01-11", 92, 98, 91, 95),    # 右1
        PriceBar("TEST", "D1", "2024-01-12", 95, 100, 93, 98),   # 右2 → L0 confirmed
    ]

    for bar in bars[:-1]:
        snapshot = engine.on_bar(bar)
        assert snapshot.active_candidate_guard_price is None  # 尚未确认

    # L0 确认时刻
    snapshot = engine.on_bar(bars[-1])
    assert snapshot.system_state == SystemState.TRANSITION
    assert snapshot.active_candidate_guard_price == 90
    assert snapshot.active_candidate_guard_extreme_bar_dt == "2024-01-10"
    assert snapshot.active_candidate_guard_confirm_bar_dt == "2024-01-12"
    assert snapshot.active_candidate_direction == Direction.DOWN  # 反向
    assert snapshot.candidate_replacement_count == 0  # 首个 candidate，无替换


def test_candidate_replacement_same_direction():
    """同向 candidate refresh 只替换 candidate，不触发 new wave。

    该 fixture 先产生一个 UP candidate，再产生 DOWN candidate，随后
    连续产生第二个 DOWN candidate。第二个 DOWN candidate 仍在
    ``transition_boundary_low`` 之上，因此不会满足 new-wave 确认条件，
    但必须按 latest-wins 规则替换旧 candidate。
    """
    engine = MALFCoreEngine(k=2)
    bars = [
        PriceBar("TEST", "D1", "2024-01-01", 110, 115, 105, 110),
        PriceBar("TEST", "D1", "2024-01-02", 110, 115, 105, 108),
        PriceBar("TEST", "D1", "2024-01-03", 108, 110, 100, 105),
        PriceBar("TEST", "D1", "2024-01-04", 105, 112, 101, 110),
        PriceBar("TEST", "D1", "2024-01-05", 110, 115, 102, 112),
        PriceBar("TEST", "D1", "2024-01-06", 112, 113, 90, 92),
        PriceBar("TEST", "D1", "2024-01-07", 92, 100, 91, 95),
        PriceBar("TEST", "D1", "2024-01-08", 95, 98, 93, 96),
        PriceBar("TEST", "D1", "2024-01-09", 96, 120, 95, 118),  # break
        PriceBar("TEST", "D1", "2024-02-01", 118, 125, 117, 118),
        PriceBar("TEST", "D1", "2024-02-02", 118, 127, 106, 114),
        PriceBar("TEST", "D1", "2024-02-03", 114, 119, 106, 114),
        PriceBar("TEST", "D1", "2024-02-04", 114, 124, 109, 113),  # H candidate
        PriceBar("TEST", "D1", "2024-02-05", 113, 120, 108, 117),
        PriceBar("TEST", "D1", "2024-02-06", 117, 119, 99, 109),
        PriceBar("TEST", "D1", "2024-02-07", 109, 118, 95, 105),
        PriceBar("TEST", "D1", "2024-02-08", 105, 110, 95, 97),
        PriceBar("TEST", "D1", "2024-02-09", 97, 110, 91, 108),  # L candidate
        PriceBar("TEST", "D1", "2024-02-10", 108, 120, 106, 111),
        PriceBar("TEST", "D1", "2024-02-11", 111, 118, 104, 110),
        PriceBar("TEST", "D1", "2024-02-12", 110, 121, 101, 117),  # L refresh
        PriceBar("TEST", "D1", "2024-02-13", 117, 128, 108, 120),
        PriceBar("TEST", "D1", "2024-02-14", 120, 121, 107, 116),
    ]

    snapshots = [engine.on_bar(bar) for bar in bars]
    snapshot = snapshots[-1]

    assert snapshot.system_state == SystemState.TRANSITION
    assert snapshot.transition_boundary_low == 90
    assert snapshot.active_candidate_guard_price == 101
    assert snapshot.active_candidate_direction == Direction.DOWN
    assert snapshot.candidate_replacement_count == 2

def test_candidate_flip_flop_opposite_direction():
    """测试反向 candidate 替换（flip-flop）。

    场景：L0(DOWN) → H1(UP)
    验证：
    - active_candidate 从 L0(DOWN) 切换为 H1(UP)
    - candidate_replacement_count += 1
    """
    engine = MALFCoreEngine(k=2)

    # 复用场景 A 到 L0 确认
    bars = [
        PriceBar("TEST", "D1", "2024-01-01", 110, 115, 105, 110),
        PriceBar("TEST", "D1", "2024-01-02", 110, 115, 105, 112),
        PriceBar("TEST", "D1", "2024-01-03", 112, 120, 110, 115),
        PriceBar("TEST", "D1", "2024-01-04", 115, 118, 105, 110),
        PriceBar("TEST", "D1", "2024-01-05", 110, 115, 100, 105),
        PriceBar("TEST", "D1", "2024-01-06", 105, 130, 110, 128),
        PriceBar("TEST", "D1", "2024-01-07", 128, 128, 115, 125),
        PriceBar("TEST", "D1", "2024-01-08", 125, 125, 120, 122),
        PriceBar("TEST", "D1", "2024-01-09", 122, 127, 95, 95),
        PriceBar("TEST", "D1", "2024-01-10", 95, 100, 90, 92),
        PriceBar("TEST", "D1", "2024-01-11", 92, 98, 91, 95),
        PriceBar("TEST", "D1", "2024-01-12", 95, 100, 93, 98),  # L0 confirmed (DOWN)
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 验证 L0(DOWN)
    assert snapshot.active_candidate_guard_price == 90
    assert snapshot.active_candidate_direction == Direction.DOWN
    assert snapshot.candidate_replacement_count == 0

    # H1 出现（反向）
    bars = [
        PriceBar("TEST", "D1", "2024-01-13", 98, 110, 95, 108),   # H1 extreme
        PriceBar("TEST", "D1", "2024-01-14", 108, 108, 100, 105),
        PriceBar("TEST", "D1", "2024-01-15", 105, 107, 102, 106), # H1 confirmed
    ]

    for bar in bars[:-1]:
        snapshot = engine.on_bar(bar)
        assert snapshot.active_candidate_direction == Direction.DOWN  # 仍是 L0

    # H1 确认时刻
    snapshot = engine.on_bar(bars[-1])
    assert snapshot.active_candidate_guard_price == 110  # flip to H1
    assert snapshot.active_candidate_direction == Direction.UP  # 反向
    assert snapshot.candidate_replacement_count == 1  # flip-flop 计数 +1


def test_new_wave_confirmation_with_candidate():
    """测试 new wave 确认（有 active candidate）。

    场景：L0(DOWN) confirmed → H1(UP) > boundary_high
    验证：
    - 触发 new up wave
    - system_state: transition → up_alive
    - guard = L0, progress = H1
    """
    engine = MALFCoreEngine(k=2)

    # 复用场景 A 到 L0 确认
    bars = [
        PriceBar("TEST", "D1", "2024-01-01", 110, 115, 105, 110),
        PriceBar("TEST", "D1", "2024-01-02", 110, 115, 105, 112),
        PriceBar("TEST", "D1", "2024-01-03", 112, 120, 110, 115),
        PriceBar("TEST", "D1", "2024-01-04", 115, 118, 105, 110),
        PriceBar("TEST", "D1", "2024-01-05", 110, 115, 100, 105),
        PriceBar("TEST", "D1", "2024-01-06", 105, 130, 110, 128),
        PriceBar("TEST", "D1", "2024-01-07", 128, 128, 115, 125),
        PriceBar("TEST", "D1", "2024-01-08", 125, 125, 120, 122),
        PriceBar("TEST", "D1", "2024-01-09", 122, 127, 95, 95),
        PriceBar("TEST", "D1", "2024-01-10", 95, 100, 90, 92),
        PriceBar("TEST", "D1", "2024-01-11", 92, 98, 91, 95),
        PriceBar("TEST", "D1", "2024-01-12", 95, 100, 93, 98),  # L0 confirmed
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 验证 transition + L0
    assert snapshot.system_state == SystemState.TRANSITION
    assert snapshot.transition_boundary_high == 130
    assert snapshot.active_candidate_guard_price == 90
    assert snapshot.active_candidate_direction == Direction.DOWN

    # H1 > boundary_high 出现
    bars = [
        PriceBar("TEST", "D1", "2024-01-13", 98, 135, 95, 132),   # H1 extreme (135 > 130)
        PriceBar("TEST", "D1", "2024-01-14", 132, 133, 128, 130),
        PriceBar("TEST", "D1", "2024-01-15", 130, 132, 127, 131), # H1 confirmed
    ]

    for bar in bars[:-1]:
        snapshot = engine.on_bar(bar)
        assert snapshot.system_state == SystemState.TRANSITION  # 仍在 transition

    # H1 确认时刻 → new wave
    snapshot = engine.on_bar(bars[-1])
    assert snapshot.system_state == SystemState.UP_ALIVE  # 新 up wave
    assert snapshot.direction == Direction.UP
    assert snapshot.wave_core_state == WaveCoreState.ALIVE
    assert snapshot.current_effective_guard_price == 90  # guard = L0
    assert snapshot.progress_extreme_price == 135  # progress = H1
    assert snapshot.transition_boundary_high is None  # transition 字段清空
    assert snapshot.transition_boundary_low is None
    assert snapshot.active_candidate_guard_price is None  # candidate 字段清空
