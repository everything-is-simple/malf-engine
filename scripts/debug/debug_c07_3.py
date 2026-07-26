"""Debug C07-3 fixture to understand pivot sequence."""

import json
from pathlib import Path

from src.malf.pivot_detection import detect_pivots
from src.malf.types import PriceBar


def main():
    # Load C07-3 fixture
    fixture_path = Path("tests/fixtures/c07/C07_3_L1_replacement.json")
    with open(fixture_path, encoding="utf-8") as f:
        fixture = json.load(f)

    # Create bars
    bars = []
    for bar_data in fixture["bars"]:
        bar = PriceBar(
            symbol=fixture["symbol"],
            timeframe=fixture["timeframe"],
            bar_dt=bar_data["bar_dt"],
            open=bar_data["open"],
            high=bar_data["high"],
            low=bar_data["low"],
            close=bar_data["close"],
        )
        bars.append(bar)

    # Detect pivots
    k = fixture.get("pivot_detection_k", 2)
    pivots = detect_pivots(bars, k=k)

    print(f"Total pivots detected: {len(pivots)}")
    print("\nPivot sequence (in confirm order):")
    for i, p in enumerate(pivots):
        print(f"  {i}: {p.pivot_type.value} @ {p.price:5d} "
              f"(extreme={p.extreme_bar_dt}, confirm={p.confirm_bar_dt})")

    print("\nExpected pivots from fixture:")
    for i, ep in enumerate(fixture["expected_pivots"]):
        print(f"  {i}: {ep['pivot_type']} @ {ep['price']:5d} "
              f"(extreme={ep['extreme_bar_dt']}, confirm={ep['confirm_bar_dt']}) - {ep['note']}")


if __name__ == "__main__":
    main()
