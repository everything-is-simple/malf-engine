"""测试 D16 Progress Confirmation（进展确认）。

验证在 alive 状态期间，新的同方向 pivot 确认时是否正确更新 progress_extreme。
"""

from malf.core_engine import MALFCoreEngine
from malf.types import Direction, PriceBar, SystemState


def test_progress_update_up_alive():
    """UP_ALIVE 状态下，新 H pivot 推进 progress_extreme。

    场景：
    1. 初始化 UP wave (H0=110, L1=96, H2=114) 确认于 d11
    2. 后续出现更高的 H3=120，确认于 d15
    3. 验证 progress_extreme 更新为 120
    """
    engine = MALFCoreEngine(k=2)

    # 初始化序列：复用 golden fixture 模式
    # H0=110 (extreme=d02, confirm=d04)
    # L1=96 (extreme=d05, confirm=d07)
    # H2=114 (extreme=d09, confirm=d11) -> UP_ALIVE
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
        PriceBar("A", "1D", "d11", 109, 110, 106, 108),  # H2 confirm -> UP_ALIVE
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 确认已初始化为 UP_ALIVE
    assert snapshot.system_state == SystemState.UP_ALIVE
    assert snapshot.direction == Direction.UP
    assert snapshot.progress_extreme_price == 114  # H2

    # 添加新 bars，产生 H3=120 (更高的 pivot)
    # H3=120 (extreme=d13, confirm=d15)
    bars_progress = [
        PriceBar("A", "1D", "d12", 108, 115, 107, 113),
        PriceBar("A", "1D", "d13", 113, 120, 112, 118),  # H3 extreme
        PriceBar("A", "1D", "d14", 118, 119, 115, 117),
        PriceBar("A", "1D", "d15", 117, 118, 114, 116),  # H3 confirm
    ]

    for bar in bars_progress:
        snapshot = engine.on_bar(bar)

    # D16: progress_extreme 应该更新为 120
    assert snapshot.progress_extreme_price == 120
    assert snapshot.progress_extreme_bar_dt == "d13"
    assert snapshot.system_state == SystemState.UP_ALIVE


def test_progress_update_down_alive():
    """DOWN_ALIVE 状态下，新 L pivot 推进 progress_extreme。

    场景：
    1. 初始化 DOWN wave (L0=90, H1=100, L2=80)
    2. 后续出现更低的 L3=70
    3. 验证 progress_extreme 更新为 70
    """
    engine = MALFCoreEngine(k=2)

    # 初始化序列：DOWN wave 模式
    # L0=90 (extreme=d02, confirm=d04)
    # H1=100 (extreme=d05, confirm=d07)
    # L2=80 (extreme=d09, confirm=d11) -> DOWN_ALIVE
    bars = [
        PriceBar("A", "1D", "d00", 95, 98, 94, 96),
        PriceBar("A", "1D", "d01", 96, 97, 92, 93),
        PriceBar("A", "1D", "d02", 93, 95, 90, 92),      # L0 extreme
        PriceBar("A", "1D", "d03", 92, 96, 91, 95),
        PriceBar("A", "1D", "d04", 95, 98, 94, 97),      # L0 confirm
        PriceBar("A", "1D", "d05", 97, 100, 96, 98),     # H1 extreme
        PriceBar("A", "1D", "d06", 98, 99, 95, 96),
        PriceBar("A", "1D", "d07", 96, 97, 94, 95),      # H1 confirm
        PriceBar("A", "1D", "d08", 95, 94, 88, 90),
        PriceBar("A", "1D", "d09", 90, 91, 80, 82),      # L2 extreme
        PriceBar("A", "1D", "d10", 82, 86, 81, 84),
        PriceBar("A", "1D", "d11", 84, 87, 83, 85),      # L2 confirm -> DOWN_ALIVE
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 确认已初始化为 DOWN_ALIVE
    assert snapshot.system_state == SystemState.DOWN_ALIVE
    assert snapshot.direction == Direction.DOWN
    assert snapshot.progress_extreme_price == 80  # L2

    # 添加新 bars，产生 L3=70 (更低的 pivot)
    # L3=70 (extreme=d13, confirm=d15)
    bars_progress = [
        PriceBar("A", "1D", "d12", 85, 87, 82, 84),
        PriceBar("A", "1D", "d13", 84, 85, 70, 72),      # L3 extreme
        PriceBar("A", "1D", "d14", 72, 78, 71, 75),
        PriceBar("A", "1D", "d15", 75, 79, 74, 77),      # L3 confirm
    ]

    for bar in bars_progress:
        snapshot = engine.on_bar(bar)

    # D16: progress_extreme 应该更新为 70
    assert snapshot.progress_extreme_price == 70
    assert snapshot.progress_extreme_bar_dt == "d13"
    assert snapshot.system_state == SystemState.DOWN_ALIVE


def test_progress_no_update_if_not_better():
    """UP_ALIVE 状态下，新 H pivot 不如当前 progress 时不更新。"""
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
        PriceBar("A", "1D", "d09", 107, 120, 106, 118),  # H2=120 (更高)
        PriceBar("A", "1D", "d10", 118, 119, 115, 117),
        PriceBar("A", "1D", "d11", 117, 118, 114, 116),
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    assert snapshot.progress_extreme_price == 120

    # 添加新 H pivot，但价格只有 115 (< 120)
    # H3=115 (extreme=d13, confirm=d15)
    bars_weaker = [
        PriceBar("A", "1D", "d12", 116, 117, 112, 114),
        PriceBar("A", "1D", "d13", 114, 115, 110, 112),  # H3=115 (weaker)
        PriceBar("A", "1D", "d14", 112, 113, 108, 110),
        PriceBar("A", "1D", "d15", 110, 112, 107, 109),  # H3 confirm
    ]

    for bar in bars_weaker:
        snapshot = engine.on_bar(bar)

    # progress_extreme 不应该更新（仍然是 120）
    assert snapshot.progress_extreme_price == 120
    assert snapshot.progress_extreme_bar_dt == "d09"


def test_progress_no_update_on_wrong_pivot_type():
    """UP_ALIVE 状态下，L pivot 不更新 progress（只有 H pivot 才更新）。"""
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
        PriceBar("A", "1D", "d11", 109, 110, 106, 108),
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    original_progress = snapshot.progress_extreme_price

    # 添加新 L pivot (guard 候选，但不应该更新 progress)
    # L=95 (extreme=d13, confirm=d15)
    bars_guard = [
        PriceBar("A", "1D", "d12", 108, 110, 105, 107),
        PriceBar("A", "1D", "d13", 107, 108, 95, 100),   # L=95
        PriceBar("A", "1D", "d14", 100, 105, 98, 103),
        PriceBar("A", "1D", "d15", 103, 107, 102, 105),  # L confirm
    ]

    for bar in bars_guard:
        snapshot = engine.on_bar(bar)

    # progress_extreme 不应该改变（L pivot 不更新 progress）
    assert snapshot.progress_extreme_price == original_progress
