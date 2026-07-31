#!/usr/bin/env python3
"""
比较两次运行的 lineage_hash 确定性
从持久化的 JSON 文件中读取 hash 进行对比
"""
import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
from v1_full_integration_pipeline import run_integrated_pipeline


def load_hashes(jsonl_file: Path) -> list:
    """从 JSONL 文件中提取所有 lineage_hash"""
    hashes = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                snapshot = json.loads(line)
                hashes.append(snapshot.get('lineage_hash'))
    return hashes


def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "510300"

    print(f"\n{'=' * 60}")
    print(f"Hash 确定性验证: {symbol}")
    print(f"{'=' * 60}\n")

    # Run 1
    print(f"Run 1...", flush=True)
    base1 = f".work/hash_test_{symbol}_run1"
    start = time.time()
    stats1 = run_integrated_pipeline(
        symbol=symbol,
        timeframe="D",
        tdx_data_path="/sessions/youthful-friendly-volta/mnt/new_tdx64",
        base_path=base1,
        market="sh",
        enable_persistence=True,
    )
    elapsed1 = time.time() - start
    print(f"✓ ({elapsed1:.1f}s) Bars: {stats1.success_bars}, Waves: {stats1.waves_terminated}\n")

    # 找到输出文件
    published_dir = Path(base1) / "published" / symbol / "D"
    jsonl_files1 = sorted(published_dir.glob("snapshots_*.jsonl"))
    if not jsonl_files1:
        print(f"❌ 找不到 Run 1 输出文件")
        sys.exit(1)
    jsonl1 = jsonl_files1[-1]

    # Run 2
    print(f"Run 2...", flush=True)
    base2 = f".work/hash_test_{symbol}_run2"
    start = time.time()
    stats2 = run_integrated_pipeline(
        symbol=symbol,
        timeframe="D",
        tdx_data_path="/sessions/youthful-friendly-volta/mnt/new_tdx64",
        base_path=base2,
        market="sh",
        enable_persistence=True,
    )
    elapsed2 = time.time() - start
    print(f"✓ ({elapsed2:.1f}s)\n")

    # 找到输出文件
    published_dir = Path(base2) / "published" / symbol / "D"
    jsonl_files2 = sorted(published_dir.glob("snapshots_*.jsonl"))
    if not jsonl_files2:
        print(f"❌ 找不到 Run 2 输出文件")
        sys.exit(1)
    jsonl2 = jsonl_files2[-1]

    # 加载 hashes
    print(f"加载 hashes...")
    hashes1 = load_hashes(jsonl1)
    hashes2 = load_hashes(jsonl2)
    print(f"  Run 1: {len(hashes1)} hashes")
    print(f"  Run 2: {len(hashes2)} hashes\n")

    # 比较
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
            print(f"  Snapshot {i}:")
            print(f"    Run1: {h1}")
            print(f"    Run2: {h2}")
        sys.exit(1)


if __name__ == "__main__":
    main()
