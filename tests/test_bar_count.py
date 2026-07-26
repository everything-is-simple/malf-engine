"""测试 Wave bar_count 计算（第五刀 Task 2）。

验证 wave 持续时间（bar 数量）的正确计算。

需求：
- uninitialized 时 bar_count = None
- 初始化确认的 bar：bar_count = 1
- 后续每根 bar：bar_count 递增
- break 时记录最终 bar_count
- new wave 后 bar_count 重新从 1 开始
"""

from malf.core_engine import MALFCoreEngine
from malf.types import PriceBar, SystemState


def test_bar_count_uninitialized():
    """Uninitialized 状态下，bar_count 应该为 None。"""
    engine = MALFCoreEngine(k=2)

    # 喂入不足以初始化的 bars
    bars = [
        PriceBar("A", "1D", "d00", 100, 102, 99, 101),
        PriceBar("A", "1D", "d01", 101, 105, 100, 104),
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    assert snapshot.system_state == SystemState.UNINITIALIZED
    assert snapshot.bar_count is None


def test_bar_count_starts_at_one_on_initialization():
    """初始化确认的 bar，bar_count 应该从 1 开始。

    场景：H0→L1→H2>H0 在 d11 确认 UP_ALIVE
    预期：d11 的 bar_count = 1
    """
    engine = MALFCoreEngine(k=2)

    # 初始化序列
    bars = [
        PriceBar("A", "1D", "d00", 100, 102, 99, 101),
        PriceBar("A", "1D", "d01", 101, 105, 100, 104),
        PriceBar("A", "1D", "d02", 104, 110, 103, 108),  # H0 extreme
        PriceBar("A", "1D", "d03", 108, 107, 104, 105),
        PriceBar("A", "1D", "d04", 105, 106, 102, 103),  # H0 confirm
        PriceBar("A", "1D", "d05", 103, 104, 96, 98),    # L1 extreme
        PriceBar("A", "1D", "d06", 98, 101, 97, 100),
        PriceBar("A", "1D", "d07", 100, 103, 98, 102),   # L1 confirm
        PriceBar("A", "1D", "d08", 102, 108, 101, 107),
        PriceBar("A", "1D", "d09", 107, 114, 106, 112),  # H2 extreme
        PriceBar("A", "1D", "d10", 112, 111, 108, 109),
        PriceBar("A", "1D", "d11", 109, 110, 106, 108),  # H2 confirm → UP_ALIVE
    ]

    snapshot = None
    for bar in bars:
        snapshot = engine.on_bar(bar)

    assert snapshot.system_state == SystemState.UP_ALIVE
    assert snapshot.bar_count == 1  # 初始化确认的 bar，计数从 1 开始


def test_bar_count_increments_in_alive_state():
    """Alive 状态下，每根新 bar 使 bar_count 递增。

    场景：初始化后继续喂入 5 根 bars
    预期：bar_count 从 1 递增到 6
    """
    engine = MALFCoreEngine(k=2)

    # 初始化序列
    bars = [
        PriceBar("A", "1D", "d00", 100, 102, 99, 101),
        PriceBar("A", "1D", "d01", 101, 105, 100, 104),
        PriceBar("A", "1D", "d02", 104, 110, 103, 108),
        PriceBar("A", "1D", "d03", 108, 107, 104, 105),
        PriceBar("A", "1D", "d04", 105, 106, 102, 103),
        PriceBar("A", "1D", "d05", 103, 104, 96, 98),
        PriceBar("A", "1D", "d06", 98, 101, 97, 100),
        PriceBar("A", "1D", "d07", 100, 103, 98, 102),
        PriceBar("A", "1D", "d08", 102, 108, 101, 107),
        PriceBar("A", "1D", "d09", 107, 114, 106, 112),
        PriceBar("A", "1D", "d10", 112, 111, 108, 109),
        PriceBar("A", "1D", "d11", 109, 110, 106, 108),  # UP_ALIVE, bar_count=1
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    assert snapshot.bar_count == 1

    # 继续喂入 5 根 bars
    additional_bars = [
        PriceBar("A", "1D", "d12", 108, 112, 107, 110),  # bar_count=2
        PriceBar("A", "1D", "d13", 110, 113, 109, 111),  # bar_count=3
        PriceBar("A", "1D", "d14", 111, 115, 110, 114),  # bar_count=4
        PriceBar("A", "1D", "d15", 114, 116, 113, 115),  # bar_count=5
        PriceBar("A", "1D", "d16", 115, 118, 114, 117),  # bar_count=6
    ]

    for i, bar in enumerate(additional_bars, start=2):
        snapshot = engine.on_bar(bar)
        assert snapshot.bar_count == i


def test_bar_count_at_break():
    """Break 时记录最终 bar_count。

    场景：UP_ALIVE 持续 5 根 bar 后发生 guard break
    预期：break 时 bar_count = 5
    """
    engine = MALFCoreEngine(k=2)

    # 初始化序列
    bars = [
        PriceBar("A", "1D", "d00", 100, 102, 99, 101),
        PriceBar("A", "1D", "d01", 101, 105, 100, 104),
        PriceBar("A", "1D", "d02", 104, 110, 103, 108),
        PriceBar("A", "1D", "d03", 108, 107, 104, 105),
        PriceBar("A", "1D", "d04", 105, 106, 102, 103),
        PriceBar("A", "1D", "d05", 103, 104, 96, 98),    # L1 = 96 (guard)
        PriceBar("A", "1D", "d06", 98, 101, 97, 100),
        PriceBar("A", "1D", "d07", 100, 103, 98, 102),
        PriceBar("A", "1D", "d08", 102, 108, 101, 107),
        PriceBar("A", "1D", "d09", 107, 114, 106, 112),
        PriceBar("A", "1D", "d10", 112, 111, 108, 109),
        PriceBar("A", "1D", "d11", 109, 110, 106, 108),  # UP_ALIVE, bar_count=1
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 继续 4 根 bar（bar_count 2-5）
    bars_before_break = [
        PriceBar("A", "1D", "d12", 108, 112, 107, 110),  # bar_count=2
        PriceBar("A", "1D", "d13", 110, 111, 109, 110),  # bar_count=3
        PriceBar("A", "1D", "d14", 110, 111, 108, 109),  # bar_count=4
        PriceBar("A", "1D", "d15", 109, 110, 107, 108),  # bar_count=5
    ]

    for bar in bars_before_break:
        snapshot = engine.on_bar(bar)

    assert snapshot.system_state == SystemState.UP_ALIVE
    assert snapshot.bar_count == 5

    # Break bar (close < guard = 96)
    break_bar = PriceBar("A", "1D", "d16", 108, 109, 90, 92)  # close=92 < guard=96
    snapshot = engine.on_bar(break_bar)

    assert snapshot.system_state == SystemState.TRANSITION
    # Break 时 bar_count 应该保持为旧 wave 的最终值
    # 注：transition 后 bar_count 的语义需要明确（是保持旧值还是变为 None）
    # 这里先假设保持旧值，待实现时确认
    assert snapshot.bar_count == 6 or snapshot.bar_count is None  # 待明确


def test_bar_count_resets_on_new_wave():
    """New wave 后 bar_count 重新从 1 开始。

    场景：transition → new wave 确认
    预期：new wave 的第一根 bar，bar_count = 1
    """
    engine = MALFCoreEngine(k=2)

    # 初始化 + break + transition + new wave 的完整序列
    # （这个测试需要较长的 bar 序列，先标记为 TODO）
    # 等 new wave 逻辑完善后再补充
    pass  # TODO: 待 new wave 完整实现后补充
