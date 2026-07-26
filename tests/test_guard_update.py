"""测试 D9 守护唯一性铁律（Guard Update）。

验证在 alive 状态期间，新的回撤 pivot 确认时是否正确替换 guard。

规格依据：
- 规格 §2.5 / D9 守护唯一性铁律
- IMPLEMENTATION-CONTRACT-PATCH.md C-01
- 推导文档：docs/t5_guard_update_derivation.md
"""

from malf.core_engine import MALFCoreEngine
from malf.types import Direction, PriceBar, SystemState


def test_guard_update_up_alive():
    """UP_ALIVE 状态下，新 L pivot 替换 guard。

    场景：
    1. 初始化 UP wave (H0=110, L1=96, H2=114) → guard=96
    2. 后续出现 L3=98（新的回撤 L pivot）
    3. 验证 guard 更新为 98

    推导依据：docs/t5_guard_update_derivation.md 场景 A
    """
    engine = MALFCoreEngine(k=2)

    # 初始化序列：UP wave
    # H0=110 (extreme=d02, confirm=d04)
    # L1=96 (extreme=d05, confirm=d07) → initial guard
    # H2=114 (extreme=d09, confirm=d11) → UP_ALIVE
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

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 确认初始 guard
    assert snapshot.system_state == SystemState.UP_ALIVE
    assert snapshot.current_effective_guard_price == 96  # L1

    # 添加新 bars，产生 L3=98（新的回撤 pivot，98 > 96）
    # L3=98 (extreme=d13, confirm=d15)
    bars_guard_update = [
        PriceBar("A", "1D", "d12", 108, 110, 105, 107),
        PriceBar("A", "1D", "d13", 107, 108, 98, 102),   # L3 extreme
        PriceBar("A", "1D", "d14", 102, 106, 100, 104),
        PriceBar("A", "1D", "d15", 104, 107, 102, 105),  # L3 confirm
    ]

    for bar in bars_guard_update:
        snapshot = engine.on_bar(bar)

    # D9: guard 应该更新为 98
    assert snapshot.current_effective_guard_price == 98
    assert snapshot.current_effective_guard_extreme_bar_dt == "d13"
    assert snapshot.current_effective_guard_confirm_bar_dt == "d15"
    assert snapshot.system_state == SystemState.UP_ALIVE  # 仍然 alive


def test_guard_update_down_alive():
    """DOWN_ALIVE 状态下，新 H pivot 替换 guard。

    场景：
    1. 初始化 DOWN wave (L0=90, H1=100, L2=80) → guard=100
    2. 后续出现 H3=95（新的回撤 H pivot）
    3. 验证 guard 更新为 95

    推导依据：docs/t5_guard_update_derivation.md 场景 B
    """
    engine = MALFCoreEngine(k=2)

    # 初始化序列：DOWN wave
    # L0=90 (extreme=d02, confirm=d04)
    # H1=100 (extreme=d05, confirm=d07) → initial guard
    # L2=80 (extreme=d09, confirm=d11) → DOWN_ALIVE
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
        PriceBar("A", "1D", "d11", 84, 87, 83, 85),      # L2 confirm → DOWN_ALIVE
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 确认初始 guard
    assert snapshot.system_state == SystemState.DOWN_ALIVE
    assert snapshot.current_effective_guard_price == 100  # H1

    # 添加新 bars，产生 H3=95（新的回撤 pivot，95 < 100）
    # H3=95 (extreme=d13, confirm=d15)
    bars_guard_update = [
        PriceBar("A", "1D", "d12", 85, 87, 82, 84),
        PriceBar("A", "1D", "d13", 84, 95, 83, 92),      # H3 extreme
        PriceBar("A", "1D", "d14", 92, 94, 89, 91),
        PriceBar("A", "1D", "d15", 91, 93, 88, 90),      # H3 confirm
    ]

    for bar in bars_guard_update:
        snapshot = engine.on_bar(bar)

    # D9: guard 应该更新为 95
    assert snapshot.current_effective_guard_price == 95
    assert snapshot.current_effective_guard_extreme_bar_dt == "d13"
    assert snapshot.current_effective_guard_confirm_bar_dt == "d15"
    assert snapshot.system_state == SystemState.DOWN_ALIVE  # 仍然 alive


def test_guard_no_update_on_progress_pivot():
    """UP_ALIVE 状态下，H pivot 不更新 guard（只更新 progress）。

    验证 D9 铁律：HH 只更新 progress，不更新 guard。

    推导依据：docs/t5_guard_update_derivation.md 场景 C1
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
        PriceBar("A", "1D", "d11", 109, 110, 106, 108),
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    original_guard = snapshot.current_effective_guard_price  # 96

    # 添加新 H pivot（推进 progress，但不应该更新 guard）
    # H3=120 (extreme=d13, confirm=d15)
    bars_progress = [
        PriceBar("A", "1D", "d12", 108, 115, 107, 113),
        PriceBar("A", "1D", "d13", 113, 120, 112, 118),  # H3 extreme
        PriceBar("A", "1D", "d14", 118, 119, 115, 117),
        PriceBar("A", "1D", "d15", 117, 118, 114, 116),  # H3 confirm
    ]

    for bar in bars_progress:
        snapshot = engine.on_bar(bar)

    # Guard 不应该改变（仍然是 96）
    assert snapshot.current_effective_guard_price == original_guard
    # 但 progress 应该更新
    assert snapshot.progress_extreme_price == 120


def test_guard_replaces_previous_guard():
    """UP_ALIVE 状态下，新 guard 直接替换旧 guard（单元素栈）。

    场景：
    1. 初始 guard = L1 = 96
    2. 出现 L3 = 98 → guard 更新为 98
    3. 出现 L4 = 99 → guard 更新为 99（替换 L3，不是并存）

    推导依据：docs/t5_guard_update_derivation.md 场景 C2
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
        PriceBar("A", "1D", "d11", 109, 110, 106, 108),
    ]

    for bar in bars:
        snapshot = engine.on_bar(bar)

    assert snapshot.current_effective_guard_price == 96  # L1

    # L3=98
    bars_l3 = [
        PriceBar("A", "1D", "d12", 108, 110, 105, 107),
        PriceBar("A", "1D", "d13", 107, 108, 98, 102),
        PriceBar("A", "1D", "d14", 102, 106, 100, 104),
        PriceBar("A", "1D", "d15", 104, 107, 102, 105),
    ]

    for bar in bars_l3:
        snapshot = engine.on_bar(bar)

    assert snapshot.current_effective_guard_price == 98  # L3 替换 L1

    # L4=99
    bars_l4 = [
        PriceBar("A", "1D", "d16", 105, 108, 104, 106),
        PriceBar("A", "1D", "d17", 106, 107, 99, 103),   # L4 extreme
        PriceBar("A", "1D", "d18", 103, 105, 101, 104),
        PriceBar("A", "1D", "d19", 104, 106, 102, 105),  # L4 confirm
    ]

    for bar in bars_l4:
        snapshot = engine.on_bar(bar)

    # Guard 应该是 99（L4 替换 L3），不是 98
    assert snapshot.current_effective_guard_price == 99
    assert snapshot.current_effective_guard_extreme_bar_dt == "d17"
