#!/usr/bin/env python3
"""Debug R5 fixture to understand pivot detection and evolution"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from malf.core_engine import MALFCoreEngine
from malf.types import PriceBar

# Load R5 fixture
fixture_path = Path(__file__).parent / "tests" / "fixtures" / "range" / "R5_multi_evolution.json"
with open(fixture_path, encoding='utf-8') as f:
    fixture = json.load(f)

# Create bars
bars = [
    PriceBar(
        symbol="TEST",
        timeframe="1d",
        bar_dt=b["bar_dt"],
        open=b["open"],
        high=b["high"],
        low=b["low"],
        close=b["close"]
    )
    for b in fixture["input_bars"]
]

# Run engine
engine = MALFCoreEngine(k=2)
print("Bar | State | Range Birth | Evo Count | Boundary Now | Boundary Init")
print("-" * 80)

for bar in bars:
    snapshot = engine.on_bar(bar)
    if snapshot.bar_dt in ["d14", "d15", "d16", "d17", "d18", "d19", "d20", "d21", "d22"]:
        print(f"{snapshot.bar_dt} | {snapshot.system_state.value:12s} | "
              f"{snapshot.range_birth_bar_dt or 'None':11s} | "
              f"{snapshot.range_evolution_count:9d} | "
              f"H:{snapshot.range_boundary_now_high or 0:3d} L:{snapshot.range_boundary_now_low or 0:3d} | "
              f"H:{snapshot.range_boundary_init_high or 0:3d} L:{snapshot.range_boundary_init_low or 0:3d}")
