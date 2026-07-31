#!/usr/bin/env python3
"""
快速验证单个标的的 lineage_hash 确定性
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
from v1_full_integration_pipeline import run_integrated_pipeline


def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "510300"

    print(f"\n{'=' * 60}")
    print(f"快速验证: {symbol}")
    print(f"{'=' * 60}\n")

    # Run 1
    print(f"Run 1...", flush=True)
    start = time.time()
    stats1 = run_integrated_pipeline(
        symbol=symbol,
        timeframe="D",
        tdx_data_path="/sessions/youthful-friendly-volta/mnt/new_tdx64",
        base_path=f".work/quick_test_{symbol}_run1",
        market="sh",
        enable_persistence=True,
    )
    elapsed1 = time.time() - start
    print(f"✓ Run 1 完成 ({elapsed1:.1f}s)")
    print(f"  Bars: {stats1.success_bars}")
    print(f"  Waves: {stats1.waves_terminated}")
    print(f"  Ranges: {stats1.ranges_resolved}")
    print(f"  Hashes: {len(stats1.lineage_hashes)}\n")

    # Run 2
    print(f"Run 2...", flush=True)
    start = time.time()
    stats2 = run_integrated_pipeline(
        symbol=symbol,
        timeframe="D",
        tdx_data_path="/sessions/youthful-friendly-volta/mnt/new_tdx64",
        base_path=f".work/quick_test_{symbol}_run2",
        market="sh",
        enable_persistence=True,
    )
    elapsed2 = time.time() - start
    print(f"✓ Run 2 完成 ({elapsed2:.1f}s)\n")

    # Compare
    hashes1 = stats1.lineage_hashes
    hashes2 = stats2.lineage_hashes

    if len(hashes1) != len(hashes2):
        print(f"❌ Hash count mismatch: {len(hashes1)} vs {len(hashes2)}")
        sys.exit(1)

    matches = sum(1 for h1, h2 in zip(hashes1, hashes2) if h1 == h2)
    total = len(hashes1)
    pct = (matches / total * 100) if total > 0 else 0

    print(f"{'=' * 60}")
    print(f"lineage_hash 确定性: {matches}/{total} ({pct:.1f}%)")

    if matches == total:
        print(f"✅ All hashes match!")
        sys.exit(0)
    else:
        print(f"❌ {total - matches} hashes differ")
        # 显示前几个不匹配的位置
        mismatches = [(i, h1, h2) for i, (h1, h2) in enumerate(zip(hashes1, hashes2)) if h1 != h2]
        print(f"\n前 5 个不匹配:")
        for i, h1, h2 in mismatches[:5]:
            print(f"  Bar {i}:")
            print(f"    Run1: {h1}")
            print(f"    Run2: {h2}")
        sys.exit(1)


if __name__ == "__main__":
    main()
