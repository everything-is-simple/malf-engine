"""Debug script to check pivot detection for T2 down initialization."""
import json
from pathlib import Path
from malf.pivot_detection import detect_pivots
from malf.initialization import find_initial_wave
from malf.types import PriceBar

fixture_path = Path("tests/fixtures/t2_down_initialization.json")

with open(fixture_path, encoding='utf-8') as f:
    d = json.load(f)

bars = [
    PriceBar(
        symbol='EURUSD', timeframe='5min',
        bar_dt=b['bar_dt'], open=b['open'], high=b['high'], low=b['low'], close=b['close']
    )
    for b in d['input_bars']
]

print("=== Input Bars ===")
for i, b in enumerate(bars):
    print(f"Bar {i} ({b.bar_dt}): O={b.open} H={b.high} L={b.low} C={b.close}")

print("\n=== Detected Pivots ===")
all_pivots = detect_pivots(bars, k=2)
print(f"Total: {len(all_pivots)} pivots")
for p in all_pivots:
    print(f"  {p.pivot_type.value} @ {p.price}, extreme={p.extreme_bar_dt}, confirm={p.confirm_bar_dt}")

print("\n=== Expected Pivots ===")
for ep in d['expected_pivots']:
    print(f"  {ep['pivot_type']} @ {ep['price']}, extreme={ep['extreme_bar_dt']}, confirm={ep['confirm_bar_dt']}")

print("\n=== Initialization Test ===")
pivots_by_confirm_dt = {p.confirm_bar_dt: p for p in all_pivots}
confirmed_pivots = []

for i, bar in enumerate(bars):
    if bar.bar_dt in pivots_by_confirm_dt:
        p = pivots_by_confirm_dt[bar.bar_dt]
        confirmed_pivots.append(p)
        print(f"Bar {i}: Confirmed {p.pivot_type.value} @ {p.price}")

    result = find_initial_wave(confirmed_pivots)
    print(f"  After bar {i}: confirmed={result.confirmed}, direction={result.direction}")

    if result.confirmed:
        print(f"    → Initialization complete!")
        print(f"    → guard_price={result.guard_price}, progress={result.progress_extreme_price}")
        break
