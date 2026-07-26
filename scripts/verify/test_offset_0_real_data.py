"""Test that offset=0 real data now works with C-07 implementation."""

from pathlib import Path
import struct

from src.malf.core_engine import MALFCoreEngine
from src.malf.types import PriceBar


def _read_tdx_day(path: Path, offset: int = 0, limit: int = 200):
    """Read TDX day file format (32 bytes per record)."""
    bars = []
    with open(path, "rb") as f:
        f.seek(offset * 32)
        for _ in range(limit):
            data = f.read(32)
            if len(data) < 32:
                break
            # TDX format: date(4) + open(4) + high(4) + low(4) + close(4) + amount(4) + volume(4) + reserved(4)
            date_int, open_price, high, low, close, amount, volume, reserved = struct.unpack("<IIIIIIII", data)
            bar_dt = str(date_int)
            bars.append(
                PriceBar(
                    symbol="sh600000",
                    timeframe="1d",
                    bar_dt=bar_dt,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                )
            )
    return bars


def main():
    tdx_file = Path("I:/new_tdx64/vipdoc/sh/lday/sh600000.day")

    if not tdx_file.exists():
        print(f"TDX file not found: {tdx_file}")
        print("Skipping test (only works on systems with TDX data)")
        return

    print("Testing offset=0 (previously failed with NotImplementedError)")
    print("=" * 80)

    # This previously failed at bar 12 with:
    # "L0 之后、H1 确认前出现第二个 L（【填洞 C-07】替换场景）暂未实现"

    bars = _read_tdx_day(tdx_file, offset=0, limit=200)
    engine = MALFCoreEngine(k=2)

    success_count = 0
    error_bar = None

    try:
        for bar in bars:
            snapshot = engine.on_bar(bar)
            success_count += 1
    except NotImplementedError as e:
        error_bar = bar.bar_dt
        print(f"FAILED at bar {success_count + 1} ({error_bar}): {e}")
        return

    print(f"SUCCESS: Processed all {success_count} bars without NotImplementedError")
    print(f"Final state: {snapshot.system_state.value}")

    # Count state distribution
    bars = _read_tdx_day(tdx_file, offset=0, limit=200)
    engine = MALFCoreEngine(k=2)
    state_counts = {}

    for bar in bars:
        snapshot = engine.on_bar(bar)
        state = snapshot.system_state.value
        state_counts[state] = state_counts.get(state, 0) + 1

    print("\nState distribution:")
    for state, count in sorted(state_counts.items()):
        print(f"  {state}: {count} bars")

    print("\nC-07 implementation verified on real data from offset=0!")


if __name__ == "__main__":
    main()
