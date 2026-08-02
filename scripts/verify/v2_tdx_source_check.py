"""V2 源数据核验：把 V2 材料包里嵌入的 OHLC 窗口与 TDX 原始 .day 文件逐 bar 对账。

TDX 日线 .day 记录格式（32 字节/条，小端）：
  u32 date  (YYYYMMDD)
  u32 open  (元 * 100)
  u32 high
  u32 low
  u32 close
  f32 amount
  u32 volume
  u32 reserved

引擎 int_fixed 价格 = 元 * 1000，而 TDX 存的是 元 * 100，因此 engine_price = tdx_price * 10。

零外部依赖，纯 stdlib。
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path


def load_tdx(day_file: Path) -> dict[str, dict]:
    """返回 {bar_dt 'YYYY-MM-DD': {open/high/low/close in engine int_fixed}}."""
    raw = day_file.read_bytes()
    out: dict[str, dict] = {}
    for off in range(0, len(raw), 32):
        rec = raw[off:off + 32]
        if len(rec) < 32:
            break
        date, o, h, l, c = struct.unpack_from("<IIIII", rec, 0)
        y, md = divmod(date, 10000)
        m, d = divmod(md, 100)
        dt = f"{y:04d}-{m:02d}-{d:02d}"
        # TDX 元*100 -> engine 元*1000
        out[dt] = {"open": o * 10, "high": h * 10, "low": l * 10, "close": c * 10}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", default=".work/V2-validation-package")
    ap.add_argument("--tdx", default="/sessions/trusting-pensive-edison/mnt/new_tdx64/vipdoc/sh/lday/sh510300.day")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    pkg = (root / args.package).resolve()
    data_file = pkg / "03-SNAPSHOTS-DATA.json"
    tdx_file = Path(args.tdx)
    if not tdx_file.exists():
        # 回退：相对挂载路径可能不同，尝试 I: 风格已由调用者传入
        print(f"找不到 TDX 文件 {tdx_file}", file=sys.stderr)
        return 2

    tdx = load_tdx(tdx_file)
    cases = json.loads(data_file.read_text(encoding="utf-8"))

    checked = 0
    mismatch = 0
    missing = 0
    fields = ("open", "high", "low", "close")

    for case in cases:
        for audit in case.get("pivot_audits", []):
            for bar in audit["ohlc_window"]:
                dt = bar["bar_dt"]
                checked += 1
                src = tdx.get(dt)
                if src is None:
                    missing += 1
                    print(f"  ⚠ TDX 缺少日期 {dt}")
                    continue
                for f in fields:
                    if bar[f] != src[f]:
                        mismatch += 1
                        print(f"  ✗ {dt} {f}: 包内 {bar[f]} != TDX {src[f]}")

    print(f"\n=== TDX 源数据对账 ===")
    print(f"对账 bar 字段组：{checked} 个 bar")
    print(f"缺失日期：{missing}")
    print(f"不一致字段：{mismatch}")
    if mismatch or missing:
        print("\n结果：❌ 源数据对账有差异")
        return 1
    print("\n结果：✅ 包内 OHLC 与 TDX 原始数据逐字节一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
