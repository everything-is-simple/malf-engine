#!/usr/bin/env python3
"""尝试从不同起始点加载数据，找到能成功初始化的区间"""

import struct
from pathlib import Path
from malf.core_engine import MALFCoreEngine
from malf.types import PriceBar, SystemState

def read_tdx_day(path: Path, offset: int = 0, limit: int = 200):
    """从 offset 开始读取 limit 根 bar"""
    bars = []
    symbol = path.stem
    with open(path, "rb") as f:
        # 跳过前 offset 条记录
        f.seek(offset * 32)
        for _ in range(limit):
            chunk = f.read(32)
            if len(chunk) < 32:
                break
            date, o, h, low, c, _amt, _vol, _res = struct.unpack("<iiiiiifi", chunk)
            bar_dt = str(date)
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

tdx_file = Path("I:/new_tdx64/vipdoc/sh/lday/sh600000.day")

# 尝试不同的起始点
for offset in [0, 50, 100, 200, 500, 1000]:
    print(f"\n{'='*60}")
    print(f"Trying offset={offset}")

    bars = read_tdx_day(tdx_file, offset=offset, limit=200)
    if len(bars) == 0:
        print(f"  No bars available at offset {offset}")
        continue

    print(f"  Loaded {len(bars)} bars starting from {bars[0].bar_dt}")

    engine = MALFCoreEngine(k=2)
    range_births = 0
    range_resolutions = 0
    bars_processed = 0

    try:
        for i, bar in enumerate(bars):
            snapshot = engine.on_bar(bar)
            bars_processed = i + 1

            if snapshot.range_birth_bar_dt == snapshot.bar_dt:
                range_births += 1
            if snapshot.range_resolution_bar_dt == snapshot.bar_dt:
                range_resolutions += 1

    except NotImplementedError as e:
        print(f"  Hit NotImplementedError at bar {bars_processed}: {str(e)[:80]}")

    print(f"  Bars processed: {bars_processed}/{len(bars)}")
    print(f"  Range births: {range_births}")
    print(f"  Range resolutions: {range_resolutions}")

    if bars_processed >= 100 and range_births > 0 and range_resolutions > 0:
        print(f"  [SUCCESS] Found good offset: {offset}")
        break
