#!/usr/bin/env python3
"""调试 T3 fixture"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "malf-engine" / "src"))

from malf.pivot_detection import detect_pivots
from malf.types import PriceBar

bars = [
    PriceBar("TEST", "day", "d00", 100, 100, 95, 98),
    PriceBar("TEST", "day", "d01", 102, 102, 96, 99),
    PriceBar("TEST", "day", "d02", 99, 99, 94, 95),
    PriceBar("TEST", "day", "d03", 98, 98, 95, 97),
    PriceBar("TEST", "day", "d04", 104, 104, 96, 103),
    PriceBar("TEST", "day", "d05", 100, 100, 95, 98),
    PriceBar("TEST", "day", "d06", 99, 99, 94, 96),
]

pivots = detect_pivots(bars, k=2)
print(f"Detected {len(pivots)} pivots:")
for p in pivots:
    print(f"  {p.pivot_type.value} {p.price} @ {p.extreme_bar_dt}, confirmed @ {p.confirm_bar_dt}")

print("\nExpected 3 pivots:")
print("  H 102 @ d01, confirmed @ d03")
print("  L 94 @ d02, confirmed @ d04")
print("  H 104 @ d04, confirmed @ d06")
