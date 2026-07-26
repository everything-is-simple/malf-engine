"""Day 0 工具脚本：验证 Core 层状态，辅助推导 Range 层状态。

功能：
1. 加载 bar 序列
2. 运行 Core 引擎，逐 bar 输出快照
3. 识别关键时刻：
   - Pivot 确认时刻
   - Wave 初始化时刻
   - Guard break 时刻（Range 诞生）
   - Transition 演化时刻
4. 打印 Core 层完整状态，供人工推导 Range 层状态

用法：
    python debug_t6.py
"""
import sys
sys.path.insert(0, 'src')

from typing import List
from malf.types import PriceBar, SystemState, Direction
from malf.core_engine import MALFCoreEngine
from malf.pivot_detection import detect_pivots


def print_bar_info(idx: int, bar: PriceBar):
    """打印 bar 基本信息"""
    print(f"\nBar {idx}: symbol={bar.symbol}, timeframe={bar.timeframe}, bar_dt={bar.bar_dt}")
    print(f"  OHLC=({bar.open}, {bar.high}, {bar.low}, {bar.close})")


def print_pivots_detected(bars: List[PriceBar], current_bar_dt: str, k: int):
    """打印在当前 bar 确认的 pivots"""
    all_pivots = detect_pivots(bars, k=k)
    confirmed_now = [p for p in all_pivots if p.confirm_bar_dt == current_bar_dt]

    if confirmed_now:
        for p in confirmed_now:
            print(f"  Pivots detected: [{p.pivot_type.value}(price={p.price}, extreme_bar_dt={p.extreme_bar_dt}, confirm_bar_dt={p.confirm_bar_dt})]")
    else:
        print(f"  Pivots detected: []")


def print_state_transition(prev_state: SystemState, curr_state: SystemState, snapshot):
    """打印状态转换和关键信息"""
    if prev_state != curr_state:
        print(f"  System state: {prev_state.value} → {curr_state.value} (STATE TRANSITION)")

        if curr_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
            print(f"  >>> WAVE INITIALIZED <<<")
            print(f"  Wave direction: {snapshot.direction.value if snapshot.direction else 'None'}")
            print(f"  Guard: price={snapshot.current_effective_guard_price}, extreme={snapshot.current_effective_guard_extreme_bar_dt}, confirm={snapshot.current_effective_guard_confirm_bar_dt}")
            print(f"  Progress: price={snapshot.progress_extreme_price}, extreme={snapshot.progress_extreme_bar_dt}")

        elif curr_state == SystemState.TRANSITION:
            print(f"  >>> RANGE BORN HERE (Guard Break) <<<")
            print(f"  Break direction: {'DOWN' if snapshot.direction == Direction.UP else 'UP'} (bar broke guard)")
            print(f"  Old wave direction: {snapshot.direction.value if snapshot.direction else 'None'}")
            print(f"  Transition boundary: high={snapshot.transition_boundary_high}, low={snapshot.transition_boundary_low}")
            print(f"  >>> Range State at Birth <<<")
            print(f"  Range birth_bar_dt: {snapshot.bar_dt}")
            print(f"  boundary_init: (high={snapshot.transition_boundary_high}, low={snapshot.transition_boundary_low})")
            print(f"  boundary_now: (high={snapshot.transition_boundary_high}, low={snapshot.transition_boundary_low})")
            print(f"  break_direction: {'DOWN' if snapshot.direction == Direction.UP else 'UP'}")
            print(f"  old_wave_direction: {snapshot.direction.value if snapshot.direction else 'None'}")
            print(f"  evolution_count: 0")
    else:
        print(f"  System state: {curr_state.value}")


def print_transition_info(snapshot):
    """打印 transition 期间的详细信息"""
    if snapshot.system_state == SystemState.TRANSITION:
        print(f"  Transition boundary: high={snapshot.transition_boundary_high}, low={snapshot.transition_boundary_low}")
        if snapshot.active_candidate_guard_price is not None:
            print(f"  Active candidate: direction={snapshot.active_candidate_direction.value if snapshot.active_candidate_direction else 'None'}, guard={snapshot.active_candidate_guard_price}")
            print(f"    candidate_extreme={snapshot.active_candidate_guard_extreme_bar_dt}, candidate_confirm={snapshot.active_candidate_guard_confirm_bar_dt}")
            print(f"    candidate_replacement_count={snapshot.candidate_replacement_count}")


def print_resolution_check(snapshot, bars: List[PriceBar], current_bar_dt: str, k: int):
    """检查是否触发 Range resolution（transition → new wave）"""
    if snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
        # 检查是否从 transition 转换过来
        all_pivots = detect_pivots(bars, k=k)
        confirmed_now = [p for p in all_pivots if p.confirm_bar_dt == current_bar_dt]

        if confirmed_now:
            print(f"  >>> RANGE RESOLVED HERE (New Wave Confirmed) <<<")
            pivot = confirmed_now[0]
            print(f"  Confirmation pivot: {pivot.pivot_type.value}(price={pivot.price}, extreme={pivot.extreme_bar_dt}, confirm={pivot.confirm_bar_dt})")
            print(f"  New wave direction: {snapshot.direction.value if snapshot.direction else 'None'}")

            # 推导 resolution_type（基于 break_direction 和 new_wave_direction）
            # 注意：这里我们需要知道之前的 break_direction，暂时从 direction 推断
            # 实际应该从之前保存的状态中获取
            print(f"  Resolution type: [需要根据 break_direction 判定]")
            print(f"  Resolution distance: [需要根据 boundary_init 计算]")


def debug_fixture(bars: List[PriceBar], k: int = 2, title: str = "Debug Fixture"):
    """调试 fixture 的完整流程"""
    print("=" * 80)
    print(f"{title}")
    print("=" * 80)

    print("\n--- Bar Sequence ---")
    for i, bar in enumerate(bars):
        print(f"Bar {i} ({bar.bar_dt}): H={bar.high}, L={bar.low}, OHLC=({bar.open},{bar.high},{bar.low},{bar.close})")

    print("\n--- All Pivots Detection ---")
    all_pivots = detect_pivots(bars, k=k)
    for p in all_pivots:
        print(f"  {p.pivot_type.value} @ {p.extreme_bar_dt} (price={p.price}), confirmed @ {p.confirm_bar_dt}")
    print(f"Total: {len(all_pivots)} pivots")

    print("\n--- Engine Progression (Bar by Bar) ---")
    engine = MALFCoreEngine(k=k)
    prev_state = SystemState.UNINITIALIZED
    prev_transition_boundary_high = None
    prev_transition_boundary_low = None

    for i, bar in enumerate(bars):
        print_bar_info(i, bar)
        print_pivots_detected(bars[:i+1], bar.bar_dt, k)

        snapshot = engine.on_bar(bar)
        print_state_transition(prev_state, snapshot.system_state, snapshot)

        # 检查是否在 transition 期间
        if snapshot.system_state == SystemState.TRANSITION:
            print_transition_info(snapshot)
            # 保存 boundary 用于后续 resolution 判定
            prev_transition_boundary_high = snapshot.transition_boundary_high
            prev_transition_boundary_low = snapshot.transition_boundary_low

        # 检查是否 resolve（从 transition 回到 alive）
        if prev_state == SystemState.TRANSITION and snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
            print_resolution_check(snapshot, bars[:i+1], bar.bar_dt, k)
            if prev_transition_boundary_high is not None:
                print(f"  boundary_init was: (high={prev_transition_boundary_high}, low={prev_transition_boundary_low})")

        prev_state = snapshot.system_state

    print("\n" + "=" * 80)
    print(f"Final state: {snapshot.system_state.value}")
    print("=" * 80)


# ============================================================================
# 示例 Fixture：R1 - Continuation Range (下 break → 下突破)
# ============================================================================

def example_r1_continuation():
    """R1: UP wave → 下 break → Range alive → 下突破 (continuation)

    Pivot 时序设计（k=2）：
    - L0: extreme @ bar 2, confirm @ bar 4 (i+k=2+2=4)
    - H1: extreme @ bar 3, confirm @ bar 5
    - L2: extreme @ bar 5, confirm @ bar 7 (需要 bar 3-4 左侧 + bar 6-7 右侧都满足 low > L2)

    等等，这里有问题：H1 @ bar 3, L2 @ bar 5，但 L2 的左侧窗口包括 bar 3-4
    Bar 3 是 H1 extreme，它的 low 必须不能破坏 L2 的窗口检查

    正确设计：参考现有 fixture，使用连续上升-下降-上升的模式
    """
    bars = [
        # 窗口填充（2 根）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d00", open=100, high=102, low=99, close=101),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d01", open=101, high=105, low=100, close=104),

        # H0 @ bar 2 (extreme @ d02, confirm @ d04)
        # 左侧窗口: bar 0-1, 右侧窗口: bar 3-4
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d02", open=104, high=110, low=103, close=108),

        # 下降开始（为 L1 做准备）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d03", open=108, high=107, low=104, close=105),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d04", open=105, high=106, low=102, close=103),  # H0 确认

        # L1 @ bar 5 (extreme @ d05, confirm @ d07)
        # 左侧窗口: bar 3-4 (low=104, 102), 右侧窗口: bar 6-7
        # 需要 low=96 < 102, 104
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d05", open=103, high=104, low=96, close=98),

        # 上升开始（为 H2 做准备）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d06", open=98, high=101, low=97, close=100),  # low > 96 ✓
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d07", open=100, high=103, low=98, close=102),  # L1 确认, low > 96 ✓

        # H2 @ bar 8 (extreme @ d08, confirm @ d10)
        # 左侧窗口: bar 6-7 (high=101, 103), 右侧窗口: bar 9-10
        # 需要 high=115 > 101, 103
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d08", open=102, high=115, low=101, close=113),

        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d09", open=113, high=112, low=108, close=110),  # high < 115 ✓
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d10", open=110, high=113, low=107, close=111),  # H2 确认, high < 115 ✓
        # 初始化完成 @ d10: direction=UP, guard=96 (L1), progress=115 (H2)

        # UP alive，创建新 H pivot 更新 guard
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d11", open=111, high=120, low=110, close=118),  # H extreme @ d11
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d12", open=118, high=117, low=113, close=115),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d13", open=115, high=118, low=112, close=116),  # H @ d11 确认 @ d13, guard 仍是 96

        # Guard break（bar.low < guard=96）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d14", open=116, high=117, low=90, close=92),  # break
        # Transition: boundary_init = (high=120, low=96)

        # Range alive（3-5 根）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d15", open=92, high=98, low=91, close=95),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d16", open=95, high=100, low=94, close=97),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d17", open=97, high=102, low=95, close=99),

        # 下突破 L pivot (price=85 < boundary_init_low=96)
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d18", open=99, high=100, low=85, close=87),  # L extreme @ d18
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d19", open=87, high=91, low=86, close=89),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d20", open=89, high=93, low=88, close=91),  # L @ d18 确认 @ d20
        # Resolution @ d20: type=CONTINUATION, distance=85-96=-11
    ]

    debug_fixture(bars, k=2, title="R1 - Continuation Range (下 break → 下突破)")


def example_r2_reversal():
    """R2: UP wave → 下 break → Range alive → 上突破 (reversal)

    与 R1 的区别：resolution 方向与 break 方向相反
    - R1: DOWN break → DOWN resolution (continuation)
    - R2: DOWN break → UP resolution (reversal)

    关键设计（T6 双条件）：
    1. 必须先有 UP candidate（L pivot 在 break bar 之后确认）
    2. 然后 H pivot（confirmation pivot）突破 boundary_init_high
    3. confirmation pivot 必须在 candidate 之后确认（C-02）
    """
    bars = [
        # 窗口填充（2 根）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d00", open=100, high=102, low=99, close=101),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d01", open=101, high=105, low=100, close=104),

        # H0 @ bar 2
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d02", open=104, high=110, low=103, close=108),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d03", open=108, high=107, low=104, close=105),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d04", open=105, high=106, low=102, close=103),  # H0 确认

        # L1 @ bar 5
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d05", open=103, high=104, low=96, close=98),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d06", open=98, high=101, low=97, close=100),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d07", open=100, high=103, low=98, close=102),  # L1 确认

        # H2 @ bar 8
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d08", open=102, high=115, low=101, close=113),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d09", open=113, high=112, low=108, close=110),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d10", open=110, high=113, low=107, close=111),  # H2 确认，初始化

        # UP alive，创建新 H pivot
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d11", open=111, high=120, low=110, close=118),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d12", open=118, high=117, low=113, close=115),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d13", open=115, high=118, low=112, close=116),  # H @ d11 确认

        # Guard break
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d14", open=116, high=117, low=90, close=92),  # break
        # Transition: boundary_init = (high=120, low=96)

        # Range alive，先创建 L candidate（UP candidate）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d15", open=92, high=95, low=88, close=90),  # L extreme @ d15
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d16", open=90, high=94, low=89, close=92),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d17", open=92, high=96, low=91, close=94),  # L @ d15 确认 @ d17
        # UP candidate 就位 @ d17: L pivot (price=88)

        # 然后创建 H pivot 突破 boundary_init_high
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d18", open=94, high=125, low=93, close=123),  # H extreme @ d18
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d19", open=123, high=122, low=118, close=120),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d20", open=120, high=121, low=117, close=119),  # H @ d18 确认 @ d20
        # Resolution @ d20: H pivot (125 > 120), type=REVERSAL
    ]

    debug_fixture(bars, k=2, title="R2 - Reversal Range (下 break → 上突破)")


def example_r3_continuation():
    """R3: DOWN wave → 上 break → Range alive → 上突破 (continuation)

    与 R1 对称：
    - R1: UP wave, DOWN break, DOWN resolution
    - R3: DOWN wave, UP break, UP resolution

    设计要点：
    - L0, H1, L2 初始化（L2 < L0）
    - DOWN alive，guard = H1
    - 上 break（bar.high > guard）
    - 上突破（H pivot.price > boundary_init_high）
    """
    bars = [
        # 窗口填充（2 根）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d00", open=100, high=105, low=95, close=98),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d01", open=98, high=103, low=94, close=96),

        # L0 @ bar 2 (extreme @ d02, price=90)
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d02", open=96, high=98, low=90, close=92),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d03", open=92, high=95, low=91, close=93),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d04", open=93, high=96, low=92, close=94),  # L0 确认

        # H1 @ bar 5 (extreme @ d05, price=110)
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d05", open=94, high=110, low=93, close=108),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d06", open=108, high=107, low=103, close=105),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d07", open=105, high=106, low=102, close=104),  # H1 确认

        # L2 @ bar 8 (extreme @ d08, price=85 < L0=90)
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d08", open=104, high=103, low=85, close=87),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d09", open=87, high=90, low=86, close=88),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d10", open=88, high=91, low=87, close=89),  # L2 确认，初始化
        # 初始化完成 @ d10: direction=DOWN, guard=110 (H1), progress=85 (L2)

        # DOWN alive，创建新 L pivot 更新 progress
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d11", open=89, high=88, low=80, close=82),  # L extreme @ d11
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d12", open=82, high=86, low=81, close=84),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d13", open=84, high=88, low=83, close=86),  # L @ d11 确认

        # Guard break（bar.high > guard=110）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d14", open=86, high=115, low=85, close=113),  # break
        # Transition: boundary_init = (high=110, low=80)

        # Range alive（3-5 根）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d15", open=113, high=112, low=107, close=109),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d16", open=109, high=108, low=103, close=105),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d17", open=105, high=107, low=102, close=104),

        # 上突破 H pivot (price=120 > boundary_init_high=110)
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d18", open=104, high=120, low=103, close=118),  # H extreme
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d19", open=118, high=117, low=113, close=115),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d20", open=115, high=116, low=112, close=114),  # H @ d18 确认
        # Resolution @ d20: type=CONTINUATION (break_direction=UP, new_wave=UP)
        # Resolution distance: 120 - 110 = 10
    ]

    debug_fixture(bars, k=2, title="R3 - Continuation Range (上 break → 上突破)")


def example_r4_reversal():
    """R4: DOWN wave → 上 break → Range alive → 下突破 (reversal)

    与 R2 对称：
    - R2: UP wave, DOWN break, UP resolution (reversal)
    - R4: DOWN wave, UP break, DOWN resolution (reversal)

    关键设计（T6 双条件）：
    1. 必须先有 DOWN candidate（H pivot）
    2. 然后 L pivot（confirmation pivot）突破 boundary_init_low
    3. confirmation pivot 必须在 candidate 之后确认（C-02）
    """
    bars = [
        # 窗口填充（2 根）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d00", open=100, high=105, low=95, close=98),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d01", open=98, high=103, low=94, close=96),

        # L0 @ bar 2
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d02", open=96, high=98, low=90, close=92),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d03", open=92, high=95, low=91, close=93),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d04", open=93, high=96, low=92, close=94),  # L0 确认

        # H1 @ bar 5
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d05", open=94, high=110, low=93, close=108),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d06", open=108, high=107, low=103, close=105),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d07", open=105, high=106, low=102, close=104),  # H1 确认

        # L2 @ bar 8
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d08", open=104, high=103, low=85, close=87),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d09", open=87, high=90, low=86, close=88),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d10", open=88, high=91, low=87, close=89),  # L2 确认，初始化
        # 初始化完成 @ d10: direction=DOWN, guard=110, progress=85

        # DOWN alive，创建新 L pivot
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d11", open=89, high=88, low=80, close=82),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d12", open=82, high=86, low=81, close=84),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d13", open=84, high=88, low=83, close=86),  # L @ d11 确认

        # Guard break（bar.high > guard=110）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d14", open=86, high=115, low=85, close=113),  # break
        # Transition: boundary_init = (high=110, low=80)

        # Range alive，先创建 H candidate（DOWN candidate）
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d15", open=113, high=118, low=112, close=116),  # H extreme @ d15
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d16", open=116, high=115, low=111, close=113),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d17", open=113, high=114, low=109, close=111),  # H @ d15 确认 @ d17
        # UP candidate 就位 @ d17: H pivot (price=118)

        # 然后创建 L pivot 突破 boundary_init_low
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d18", open=111, high=110, low=75, close=77),  # L extreme @ d18
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d19", open=77, high=81, low=76, close=79),
        PriceBar(symbol="TEST", timeframe="1d", bar_dt="d20", open=79, high=83, low=78, close=81),  # L @ d18 确认 @ d20
        # Resolution @ d20: L pivot (75 < 80), type=REVERSAL
    ]

    debug_fixture(bars, k=2, title="R4 - Reversal Range (上 break → 下突破)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        fixture_name = sys.argv[1]
        if fixture_name == "r1":
            example_r1_continuation()
        elif fixture_name == "r2":
            example_r2_reversal()
        elif fixture_name == "r3":
            example_r3_continuation()
        elif fixture_name == "r4":
            example_r4_reversal()
        else:
            print(f"Unknown fixture: {fixture_name}")
            print("Available: r1, r2, r3, r4")
    else:
        # 默认运行 R1
        example_r1_continuation()
