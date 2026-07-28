"""V2 独立交叉核验脚本。

目的：不信任 V2 材料包里 engine 自带的 strict_fractal_check 布尔值，
而是直接用 pivot_audits 里的原始 OHLC 窗口重算 fractal k=2 规则、
确认延迟（extreme -> confirm 之间恰好 k=2 根）、以及 guard break 的不等式。

这是 V2 人工签字之前的机器预检，不替代肉眼对照 K 线。
零外部依赖，纯 stdlib。

用法：
    python3 scripts/verify/v2_independent_crosscheck.py
    python3 scripts/verify/v2_independent_crosscheck.py --package .work/V2-validation-package
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

K = 2  # fractal 窗口半径


def check_fractal(pivot_type: str, window: list[dict]) -> tuple[bool, str]:
    """在 5-bar 窗口里重算 fractal k=2：中心 bar 严格高/低于左右各 K 根。"""
    if len(window) != 2 * K + 1:
        return False, f"窗口长度 {len(window)} != {2*K+1}"
    center = window[K]
    if pivot_type == "H":
        c = center["high"]
        for i, b in enumerate(window):
            if i == K:
                continue
            if not (c > b["high"]):
                return False, f"center high {c} 未严格高于 bar#{b['bar_index']} high {b['high']}"
        return True, "OK"
    elif pivot_type == "L":
        c = center["low"]
        for i, b in enumerate(window):
            if i == K:
                continue
            if not (c < b["low"]):
                return False, f"center low {c} 未严格低于 bar#{b['bar_index']} low {b['low']}"
        return True, "OK"
    return False, f"未知 pivot_type {pivot_type}"


def check_pivot_price(pivot: dict, window: list[dict]) -> tuple[bool, str]:
    """确认 pivot.price 与中心 bar 的 high/low 一致，且 extreme_bar_dt 对得上。"""
    center = window[K]
    if center["bar_dt"] != pivot["extreme_bar_dt"]:
        return False, f"中心 bar 日期 {center['bar_dt']} != extreme_bar_dt {pivot['extreme_bar_dt']}"
    want = center["high"] if pivot["pivot_type"] == "H" else center["low"]
    if want != pivot["price"]:
        return False, f"pivot.price {pivot['price']} != 中心 bar 极值 {want}"
    return True, "OK"


def check_confirm_lag(pivot: dict, window: list[dict]) -> tuple[bool, str]:
    """确认延迟：窗口最后一根应为 confirm bar，且在 extreme 之后第 K 根。"""
    # 窗口是 [extreme-K .. extreme .. extreme+K]，最后一根 index 应等于 confirm
    last = window[-1]
    if last["bar_dt"] != pivot["confirm_bar_dt"]:
        return False, f"窗口末根 {last['bar_dt']} != confirm_bar_dt {pivot['confirm_bar_dt']}"
    center = window[K]
    gap = last["bar_index"] - center["bar_index"]
    if gap != K:
        return False, f"confirm 与 extreme 相隔 {gap} 根 != k={K}"
    return True, "OK"


def check_break(break_check: dict, event_bar: dict, prev_snap: dict, direction: str) -> tuple[bool, str]:
    """重算 guard break 不等式。UP: low < guard；DOWN: high > guard。"""
    guard = prev_snap["current_effective_guard_price"]
    if direction == "up":
        recomputed = event_bar["low"] < guard
        expr = f"low {event_bar['low']} < guard {guard}"
    elif direction == "down":
        recomputed = event_bar["high"] > guard
        expr = f"high {event_bar['high']} > guard {guard}"
    else:
        return False, f"未知方向 {direction}"
    if recomputed != break_check["passed"]:
        return False, f"重算 {recomputed} != 材料包 {break_check['passed']}"
    if expr.split(" ")[1] not in break_check["expression"]:
        # 宽松比对：仅提示，不算失败
        pass
    return True, f"{expr} -> {recomputed}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", default=".work/V2-validation-package")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    pkg = (root / args.package).resolve()
    data_file = pkg / "03-SNAPSHOTS-DATA.json"
    if not data_file.exists():
        print(f"找不到 {data_file}", file=sys.stderr)
        return 2

    cases = json.loads(data_file.read_text(encoding="utf-8"))
    total_pivots = 0
    fail_pivots = 0
    total_breaks = 0
    fail_breaks = 0
    mismatch_flag = 0  # engine 自带 flag 与重算不一致

    print(f"=== V2 独立交叉核验：{len(cases)} 个案例 ===\n")
    for idx, case in enumerate(cases, 1):
        eb = case["event_bar"]
        cat = case["selection_category"]
        header = f"[{idx:>2}] bar#{eb['bar_index']} {eb['bar_dt']} ({cat})"
        lines = []
        case_ok = True

        for audit in case.get("pivot_audits", []):
            piv = audit["pivot"]
            win = audit["ohlc_window"]
            role = audit["role"]
            total_pivots += 1

            ok_fr, msg_fr = check_fractal(piv["pivot_type"], win)
            ok_pr, msg_pr = check_pivot_price(piv, win)
            ok_lag, msg_lag = check_confirm_lag(piv, win)
            ok = ok_fr and ok_pr and ok_lag
            if not ok:
                fail_pivots += 1
                case_ok = False
                if not ok_fr:
                    lines.append(f"    ✗ {role} fractal: {msg_fr}")
                if not ok_pr:
                    lines.append(f"    ✗ {role} price: {msg_pr}")
                if not ok_lag:
                    lines.append(f"    ✗ {role} lag: {msg_lag}")
            # engine flag 与重算是否一致
            engine_flag = audit.get("strict_fractal_check")
            if engine_flag is not None and engine_flag != ok_fr:
                mismatch_flag += 1
                lines.append(f"    ⚠ {role} engine flag={engine_flag} 但重算={ok_fr}")

        bc = case.get("break_check")
        if bc:
            total_breaks += 1
            direction = case["core_snapshot"].get("direction")
            prev = case["previous_core_snapshot"]
            ok_bk, msg_bk = check_break(bc, eb, prev, direction)
            if not ok_bk:
                fail_breaks += 1
                case_ok = False
                lines.append(f"    ✗ break: {msg_bk}")

        status = "PASS" if case_ok else "FAIL"
        print(f"{header}  ->  {status}")
        for ln in lines:
            print(ln)

    print("\n=== 汇总 ===")
    print(f"Pivot 审计：{total_pivots - fail_pivots}/{total_pivots} 通过")
    print(f"Break 算式：{total_breaks - fail_breaks}/{total_breaks} 通过")
    print(f"engine flag 与重算不一致：{mismatch_flag} 处")

    if fail_pivots or fail_breaks:
        print("\n结果：❌ 有失败项，需检查")
        return 1
    print("\n结果：✅ 全部机器核验通过（仍需人工对照 K 线签字）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
