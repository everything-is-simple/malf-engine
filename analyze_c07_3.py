"""Analyze C07-3 bars to understand why pivots are not detected."""

import json
from pathlib import Path


def main():
    fixture_path = Path("tests/fixtures/c07/C07_3_L1_replacement.json")
    with open(fixture_path, encoding="utf-8") as f:
        fixture = json.load(f)

    print("Bar sequence (k=2, need 2 bars on each side):")
    print("-" * 80)
    for i, bar in enumerate(fixture["bars"]):
        print(f"{bar['bar_dt']}: H={bar['high']:5d} L={bar['low']:5d}")

    print("\n" + "=" * 80)
    print("Checking H0 @ d01 (H=15000):")
    print("  Need: d02.H < 15000 and d03.H < 15000 (right side)")
    print("  Actual: d02.H=14000 OK, d03.H=13000 OK")
    print("  Need: 2 bars on left side -> NOT ENOUGH (d01 is first bar)")
    print("  Result: NOT a pivot (insufficient left context)")

    print("\nChecking L @ d05 (L=9000):")
    print("  Need: d03.L > 9000, d04.L > 9000 (left), d06.L > 9000, d07.L > 9000 (right)")
    print("  Actual: d03.L=9500 OK, d04.L=10000 OK, d06.L=9500 OK, d07.L=7000 FAIL")
    print("  Result: NOT a pivot (d07.L=7000 < 9000)")

    print("\nChecking L @ d07 (L=7000):")
    print("  Need: d05.L > 7000, d06.L > 7000 (left), d08.L > 7000, d09.L > 7000 (right)")
    print("  Actual: d05.L=9000 OK, d06.L=9500 OK, d08.L=7500 OK, d09.L=8500 OK")
    print("  Result: PIVOT confirmed at d09")

    print("\nConclusion: Fixture design needs adjustment")
    print("  - Add padding bars at start for H0 to have left context")
    print("  - Ensure L1_old is a valid pivot before L1_new appears")


if __name__ == "__main__":
    main()
