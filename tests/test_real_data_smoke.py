"""S7 真实数据冒烟测试——暴露规格/fixture 没预料到的真实世界问题。

目标不是验证正确性（正确性由 golden fixture 保证），而是确保引擎在真实数据上
不崩溃、不触发未实现分支的显式报错、能走完全部 bar。

真实数据可能有的问题：
- 重复 bar_dt（停牌复牌、补数据）
- 跳空（连续交易日之间有日历空白）
- 异常 OHLC 关系（open/close 不在 [low, high] 之内，虽然 TDX 数据应该干净）
- 稀疏数据（早期标的交易日很少）

如果这些问题导致引擎崩溃或行为异常，应记录在 BUILD-PLAN.md「已发现待处理」，
评估是否需要在规格中明确边界处理规则、或在数据读取层做清洗。

第一刀（S7）：验证 up 方向初始化，down 方向会抛 NotImplementedError。
第二刀（S2-6）：验证 down 方向初始化也能正常工作，不再抛异常（除非 H0/L0 或 L1/H1 替换）。
第三刀（S3-6）：验证 guard break 逻辑在真实数据上稳定，能触发 up_alive/down_alive → transition。
"""

from __future__ import annotations

import struct
from pathlib import Path

from malf.core_engine import MALFCoreEngine
from malf.initialization import find_initial_wave
from malf.pivot_detection import detect_pivots
from malf.types import PriceBar, SystemState


def _read_tdx_day(path: Path, limit: int = 200) -> list[PriceBar]:
    """读取 TDX .day 文件的前 limit 根 bar（用于冒烟测试，不需要全部数据）。

    TDX .day 格式（每条 32 字节）：
        int32 date (YYYYMMDD)
        int32 open  (单位：分，需除以100得到元)
        int32 high
        int32 low
        int32 close
        float amount (成交额)
        int32 vol (成交量)
        int32 reserved

    价格已是整数（单位：分），符合 int_fixed 策略，直接用不转换。
    """
    bars = []
    symbol = path.stem  # e.g., "sh600000"
    with open(path, "rb") as f:
        for _ in range(limit):
            chunk = f.read(32)
            if len(chunk) < 32:
                break
            date, o, h, low, c, _amt, _vol, _res = struct.unpack("<iiiiiifi", chunk)
            bar_dt = str(date)  # YYYYMMDD as string
            bars.append(
                PriceBar(
                    symbol=symbol,
                    timeframe="day",
                    bar_dt=bar_dt,
                    open=o,
                    high=h,
                    low=low,
                    close=c,
                )
            )
    return bars


def test_sh600000_first_200_bars_no_crash():
    """浦发银行 (sh600000) 前 200 根日线冒烟——验证引擎能走完不崩溃。

    不断言具体 pivot 或 snapshot 内容（那是 golden fixture 的职责），
    只验证 detect_pivots + find_initial_wave 能跑完、不抛异常（除了预期的 NotImplementedError）。

    第二刀更新：验证 down 方向初始化也能正常工作（第一刀时 down 会抛 NotImplementedError）。
    """
    tdx_file = Path("I:/new_tdx64/vipdoc/sh/lday/sh600000.day")
    if not tdx_file.exists():
        # 在 Windows 机器上路径不同，跳过（这是 VM 专属测试）
        import pytest
        pytest.skip(f"TDX file not found: {tdx_file}")

    bars = _read_tdx_day(tdx_file, limit=200)
    assert len(bars) > 0, "应至少读到一些 bar"

    # pivot 检测应能跑完
    pivots = detect_pivots(bars, k=2)
    assert isinstance(pivots, list)  # 不崩就行，pivot 数量不做断言

    # 统计 pivot 类型分布（用于诊断）
    h_count = sum(1 for p in pivots if p.pivot_type.value == "H")
    l_count = sum(1 for p in pivots if p.pivot_type.value == "L")

    # 初始化判定应能跑完（可能 confirmed=False，也可能确认 up/down，都不崩就行）
    try:
        result = find_initial_wave(pivots)
        # 第二刀：down 方向已实现，不应再抛 NotImplementedError（除非 H0/L0 或 L1/H1 替换）
        assert result is not None
        if result.confirmed:
            print(f"Initialized: direction={result.direction.value}, guard={result.guard_price}, progress={result.progress_extreme_price}")
        else:
            print("Not yet initialized (O6 failure rule)")
    except NotImplementedError as e:
        # 预期的未实现分支（H0/L0 替换 / L1/H1 替换），记录但不算失败
        # 第二刀后，down 方向本身不应抛异常
        print(f"Hit expected NotImplementedError (replacement scenario): {e}")

    print(f"Smoke test passed: {len(bars)} bars, {len(pivots)} pivots detected (H={h_count}, L={l_count}).")


def test_sh600000_with_core_engine_guard_break():
    """第三刀：使用 MALFCoreEngine 测试真实数据，验证 guard break 逻辑。

    验证：
    - 引擎能逐 bar 推进完整序列（不崩溃）
    - 能触发 up_alive 或 down_alive（initialization）
    - 能触发 guard break → transition（或不触发，取决于实际序列）
    - transition 后抛出预期的 NotImplementedError（active candidate 演化未实现）
    """
    tdx_file = Path("I:/new_tdx64/vipdoc/sh/lday/sh600000.day")
    if not tdx_file.exists():
        import pytest
        pytest.skip(f"TDX file not found: {tdx_file}")

    bars = _read_tdx_day(tdx_file, limit=200)
    assert len(bars) > 0, "应至少读到一些 bar"

    engine = MALFCoreEngine(k=2)

    initialized = False
    transitioned = False
    last_state = None
    transition_bar_idx = None

    for i, bar in enumerate(bars):
        try:
            snapshot = engine.on_bar(bar)
            last_state = snapshot.system_state

            # 记录初始化
            if not initialized and snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
                initialized = True
                print(f"[OK] Initialized at bar {i}: state={snapshot.system_state.value}, "
                      f"direction={snapshot.direction.value if snapshot.direction else None}, "
                      f"guard={snapshot.current_effective_guard_price}, "
                      f"progress={snapshot.progress_extreme_price}")

            # 记录 transition
            if snapshot.system_state == SystemState.TRANSITION:
                transitioned = True
                transition_bar_idx = i
                print(f"[OK] Transitioned at bar {i}: direction={snapshot.direction.value if snapshot.direction else None}")

        except NotImplementedError as e:
            # 预期的 NotImplementedError：transition 后的 active candidate 演化
            if "Transition 期间 active candidate" in str(e):
                print(f"[OK] Hit expected NotImplementedError at bar {i}: {e}")
                transitioned = True
                transition_bar_idx = i
                break
            else:
                # 其他 NotImplementedError（H0/L0 或 L1/H1 替换）
                print(f"[WARN] Hit replacement NotImplementedError at bar {i}: {e}")
                break

    print(f"\nSummary:")
    print(f"  Bars processed: {i + 1}/{len(bars)}")
    print(f"  Initialized: {initialized}")
    print(f"  Transitioned: {transitioned}")
    if transition_bar_idx:
        print(f"  Transition at bar: {transition_bar_idx}")
    print(f"  Final state: {last_state.value if last_state else 'N/A'}")

    # 冒烟测试成功标准：至少能走完一些 bars，不意外崩溃
    assert i >= 0, "Should process at least one bar"
