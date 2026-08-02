"""TDX 日线数据读取模块。

读取 TDX .day 二进制文件并转换为 MALF PriceBar 对象。

TDX .day 文件格式（32 字节/条）：
- Offset 0-3 (4 bytes): 日期（年月日编码）
- Offset 4-7 (4 bytes): Open（整数，已放大 100 倍）
- Offset 8-11 (4 bytes): High（整数，已放大 100 倍）
- Offset 12-15 (4 bytes): Low（整数，已放大 100 倍）
- Offset 16-19 (4 bytes): Close（整数，已放大 100 倍）
- Offset 20-23 (4 bytes): Amount（成交额）
- Offset 24-27 (4 bytes): Volume（成交量）
- Offset 28-31 (4 bytes): 保留字段

价格处理：
- TDX 存储价格已放大 100 倍（如 2.50 元 → 250）
- MALF 要求放大 1000 倍（int_fixed 策略）
- 因此需要再乘以 10
"""

import struct
from pathlib import Path
from typing import List
from datetime import datetime

# 导入 MALF 类型
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from malf.types import PriceBar


def decode_tdx_date(date_int: int) -> str:
    """解码 TDX 日期格式。

    TDX 日期编码：整数 YYYYMMDD 格式（如 20120528 表示 2012-05-28）

    实际格式：
    - 0x013303D0 = 20120528 → 2012-05-28
    - 0x013303D1 = 20120529 → 2012-05-29
    """
    # 直接解析为 YYYYMMDD
    year = date_int // 10000
    month = (date_int % 10000) // 100
    day = date_int % 100

    # 返回 ISO 8601 格式
    return f"{year:04d}-{month:02d}-{day:02d}"


def load_tdx_daily_bars(
    symbol: str,
    tdx_data_path: str = "/sessions/youthful-friendly-volta/mnt/new_tdx64",
    market: str = "sh"
) -> List[PriceBar]:
    """加载 TDX 日线数据。

    Args:
        symbol: 标的代码（如 "510300"）
        tdx_data_path: TDX 数据根目录
        market: 市场代码（"sh" 上海 / "sz" 深圳）

    Returns:
        PriceBar 对象列表，按时间顺序排列

    Raises:
        FileNotFoundError: 数据文件不存在
        ValueError: 数据解析错误
    """
    # 构建文件路径
    file_path = Path(tdx_data_path) / "vipdoc" / market / "lday" / f"{market}{symbol}.day"

    if not file_path.exists():
        raise FileNotFoundError(f"TDX data file not found: {file_path}")

    bars = []

    # 读取二进制数据
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(32)
            if len(chunk) < 32:
                break

            # 解析 32 字节数据（小端序）
            (
                date_int,
                open_price,
                high_price,
                low_price,
                close_price,
                amount,
                volume,
                reserved
            ) = struct.unpack("<IIIIIIII", chunk)

            # 解码日期
            bar_dt = decode_tdx_date(date_int)

            # 价格转换：TDX 已放大 100 倍，MALF 需要 1000 倍
            # 所以再乘以 10
            bar = PriceBar(
                symbol=symbol,
                timeframe="D",
                bar_dt=bar_dt,
                open=open_price * 10,
                high=high_price * 10,
                low=low_price * 10,
                close=close_price * 10,
            )

            bars.append(bar)

    return bars


def main():
    """测试读取前 10 条数据。"""
    print("Loading TDX data for 510300...")

    try:
        bars = load_tdx_daily_bars("510300", market="sh")

        print(f"\nTotal bars loaded: {len(bars)}")
        print("\nFirst 10 bars:")
        print("-" * 80)

        for i, bar in enumerate(bars[:10]):
            print(f"{i+1}. {bar.bar_dt}: O={bar.open/1000:.2f} H={bar.high/1000:.2f} "
                  f"L={bar.low/1000:.2f} C={bar.close/1000:.2f}")

        if len(bars) > 10:
            print("\nLast 3 bars:")
            print("-" * 80)
            for bar in bars[-3:]:
                print(f"   {bar.bar_dt}: O={bar.open/1000:.2f} H={bar.high/1000:.2f} "
                      f"L={bar.low/1000:.2f} C={bar.close/1000:.2f}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
