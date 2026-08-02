#!/usr/bin/env python3
"""
V1 批量测试脚本 - 验证 5 只标的的 lineage_hash 确定性

运行所有标的两次，验证 lineage_hash 100% 匹配
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
from typing import Dict, List, Tuple
from v1_full_integration_pipeline import run_integrated_pipeline


# 5 只测试标的
SYMBOLS = [
    "510300",  # 沪深300ETF
    "510500",  # 中证500ETF
    "159915",  # 创业板ETF
    "512880",  # 证券ETF
    "513100",  # 纳指ETF
]

TDX_DATA_PATH = "/sessions/youthful-friendly-volta/mnt/new_tdx64"


def run_single_test(symbol: str, run_id: int) -> Tuple[bool, Dict]:
    """运行单个标的测试，返回 (success, stats)"""
    # 使用独立的 var 目录避免冲突
    base_path = f".work/batch_test_{symbol}_run{run_id}"

    try:
        stats = run_integrated_pipeline(
            symbol=symbol,
            timeframe="D",
            tdx_data_path=TDX_DATA_PATH,
            base_path=base_path,
            market="sh",
            enable_persistence=True,
        )

        # 提取结果
        result = {
            "bars_processed": stats.success_bars,
            "total_waves": stats.waves_terminated,
            "total_ranges": stats.ranges_resolved,
            "lineage_hashes": stats.lineage_hashes,
        }
        return True, result
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def compare_hashes(run1_hashes: List[str], run2_hashes: List[str]) -> Tuple[int, int]:
    """比较两次运行的 hash，返回 (matches, total)"""
    if len(run1_hashes) != len(run2_hashes):
        return 0, max(len(run1_hashes), len(run2_hashes))

    matches = sum(1 for h1, h2 in zip(run1_hashes, run2_hashes) if h1 == h2)
    return matches, len(run1_hashes)


def main():
    print("=" * 80)
    print("V1 批量测试 - lineage_hash 确定性验证")
    print("=" * 80)
    print(f"\n测试标的: {len(SYMBOLS)} 个")
    print(f"每个标的运行 2 次")
    print(f"预计时间: ~{len(SYMBOLS) * 40} 秒\n")

    all_results = {}
    total_start = time.time()

    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"\n[{i}/{len(SYMBOLS)}] {symbol}")
        print("-" * 40)

        # Run 1
        print("  Run 1...", end=" ", flush=True)
        start = time.time()
        success1, stats1 = run_single_test(symbol, run_id=1)
        elapsed1 = time.time() - start

        if not success1:
            all_results[symbol] = {"success": False}
            continue

        print(f"✓ ({elapsed1:.1f}s)")
        print(f"    Bars: {stats1['bars_processed']}")
        print(f"    Waves: {stats1['total_waves']}")
        print(f"    Ranges: {stats1['total_ranges']}")

        # Run 2
        print("  Run 2...", end=" ", flush=True)
        start = time.time()
        success2, stats2 = run_single_test(symbol, run_id=2)
        elapsed2 = time.time() - start

        if not success2:
            all_results[symbol] = {"success": False}
            continue

        print(f"✓ ({elapsed2:.1f}s)")

        # Compare hashes
        hashes1 = stats1.get("lineage_hashes", [])
        hashes2 = stats2.get("lineage_hashes", [])
        matches, total = compare_hashes(hashes1, hashes2)

        match_pct = (matches / total * 100) if total > 0 else 0

        if matches == total:
            print(f"  ✅ Hash match: {matches}/{total} (100.0%)")
        else:
            print(f"  ❌ Hash mismatch: {matches}/{total} ({match_pct:.1f}%)")

        all_results[symbol] = {
            "success": True,
            "bars": stats1["bars_processed"],
            "waves": stats1["total_waves"],
            "ranges": stats1["total_ranges"],
            "hash_matches": matches,
            "hash_total": total,
            "time_avg": (elapsed1 + elapsed2) / 2
        }

    total_elapsed = time.time() - total_start

    # Summary
    print("\n" + "=" * 80)
    print("批量测试总结")
    print("=" * 80)

    success_count = sum(1 for r in all_results.values() if r.get("success"))
    total_bars = sum(r.get("bars", 0) for r in all_results.values())
    total_waves = sum(r.get("waves", 0) for r in all_results.values())
    total_ranges = sum(r.get("ranges", 0) for r in all_results.values())
    total_hash_matches = sum(r.get("hash_matches", 0) for r in all_results.values())
    total_hash_total = sum(r.get("hash_total", 0) for r in all_results.values())

    print(f"\n成功标的: {success_count}/{len(SYMBOLS)}")
    print(f"总 bars: {total_bars}")
    print(f"总 waves: {total_waves}")
    print(f"总 ranges: {total_ranges}")
    print(f"总时间: {total_elapsed:.1f}s")

    if total_hash_total > 0:
        match_pct = total_hash_matches / total_hash_total * 100
        print(f"\nlineage_hash 确定性:")
        print(f"  {total_hash_matches}/{total_hash_total} ({match_pct:.1f}%)")

        if total_hash_matches == total_hash_total:
            print("\n  ✅ All hashes match! 100% determinism confirmed.")
        else:
            print("\n  ❌ Hash mismatch detected!")
            print("\n详细结果:")
            for symbol, result in all_results.items():
                if result.get("success"):
                    m = result["hash_matches"]
                    t = result["hash_total"]
                    pct = (m / t * 100) if t > 0 else 0
                    status = "✅" if m == t else "❌"
                    print(f"  {status} {symbol}: {m}/{t} ({pct:.1f}%)")

    print("\n" + "=" * 80)

    # Exit code
    if success_count == len(SYMBOLS) and total_hash_matches == total_hash_total:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
