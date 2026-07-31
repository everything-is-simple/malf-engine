#!/usr/bin/env python3
"""Prepare a deterministic V2 manual-validation package from raw TDX bars.

Unlike the original draft, this script replays the Core engine directly, keeps
raw OHLC context for every audited pivot, and selects enough cases to satisfy
the V2 acceptance threshold.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (SRC_ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from malf.core_engine import MALFCoreEngine
from malf.pivot_detection import detect_pivots
from malf.types import CoreStateSnapshot, Pivot, PriceBar
from tdx_reader import load_tdx_daily_bars

ALIVE_STATES = {"up_alive", "down_alive"}


def enum_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: enum_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [enum_value(item) for item in value]
    return value


def snapshot_dict(snapshot: CoreStateSnapshot) -> dict[str, Any]:
    return enum_value(asdict(snapshot))


def bar_dict(bar: PriceBar, bar_index: int) -> dict[str, Any]:
    return {
        "bar_index": bar_index,
        "bar_dt": bar.bar_dt,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
    }


def pivot_dict(pivot: Pivot | None) -> dict[str, Any] | None:
    if pivot is None:
        return None
    return enum_value(asdict(pivot))


def discover_tdx_root(explicit: str | None = None) -> Path:
    candidates = [
        explicit,
        os.environ.get("TDX_DATA_ROOT"),
        r"I:\new_tdx64",
        "/sessions/youthful-friendly-volta/mnt/new_tdx64",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    rendered = ", ".join(str(item) for item in candidates if item)
    raise FileNotFoundError(
        "TDX data root not found. Pass --tdx-root or set TDX_DATA_ROOT. "
        f"Checked: {rendered}"
    )


def _state(snapshot: CoreStateSnapshot | None) -> str | None:
    return snapshot.system_state.value if snapshot is not None else None


def _direction(snapshot: CoreStateSnapshot | None) -> str | None:
    if snapshot is None or snapshot.direction is None:
        return None
    return snapshot.direction.value


def classify_events(
    previous: CoreStateSnapshot | None,
    current: CoreStateSnapshot,
    confirmed_pivot: Pivot | None,
) -> list[str]:
    """Return all material events at the current bar, ordered by importance."""
    events: list[str] = []
    prev_state = _state(previous)
    curr_state = _state(current)
    prev_direction = _direction(previous)
    curr_direction = _direction(current)

    if previous is None:
        events.append("series_start")
    elif prev_state == "uninitialized" and curr_state in ALIVE_STATES:
        events.append(f"initialization_{curr_direction}")
    elif prev_state in ALIVE_STATES and curr_state == "transition":
        events.append(f"guard_break_{prev_direction}")
    elif prev_state == "transition" and curr_state in ALIVE_STATES:
        events.append(f"new_wave_{curr_direction}")

    if previous is not None:
        if previous.current_effective_guard_price != current.current_effective_guard_price:
            events.append("guard_update")
        if previous.progress_extreme_price != current.progress_extreme_price:
            events.append("progress_update")
        if (
            previous.active_candidate_guard_price is None
            and current.active_candidate_guard_price is not None
        ):
            events.append("candidate_start")
        if current.candidate_replacement_count > previous.candidate_replacement_count:
            events.append("candidate_replacement")
        if current.range_evolution_count > previous.range_evolution_count:
            events.append("range_evolution")

    if confirmed_pivot is not None:
        events.append(f"pivot_confirm_{confirmed_pivot.pivot_type.value.lower()}")

    if not events:
        if curr_state in ALIVE_STATES:
            events.append("alive_observation")
        elif curr_state == "transition":
            events.append("transition_observation")
        else:
            events.append("uninitialized_observation")
    return events


def build_trace(bars: Sequence[PriceBar], k: int = 2) -> tuple[list[dict[str, Any]], list[Pivot]]:
    """Replay Core and retain one deterministic record per input bar."""
    pivots = detect_pivots(bars, k=k)
    # This mirrors MALFCoreEngine's current one-pivot-per-confirm-bar behavior.
    pivot_by_confirm_dt = {pivot.confirm_bar_dt: pivot for pivot in pivots}
    engine = MALFCoreEngine(k=k)
    trace: list[dict[str, Any]] = []
    previous: CoreStateSnapshot | None = None

    for index, bar in enumerate(bars):
        current = engine.on_bar(bar)
        confirmed_pivot = pivot_by_confirm_dt.get(bar.bar_dt)
        events = classify_events(previous, current, confirmed_pivot)
        trace.append(
            {
                "bar_index": index,
                "bar_dt": bar.bar_dt,
                "bar": bar,
                "previous_snapshot": previous,
                "snapshot": current,
                "confirmed_pivot": confirmed_pivot,
                "events": events,
            }
        )
        previous = current
    return trace, pivots


def _spread(items: Sequence[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if count <= 0 or not items:
        return []
    if len(items) <= count:
        return list(items)
    if count == 1:
        return [items[len(items) // 2]]
    positions = [round(i * (len(items) - 1) / (count - 1)) for i in range(count)]
    return [items[position] for position in positions]


def select_validation_cases(trace: Sequence[dict[str, Any]], count: int = 15) -> list[dict[str, Any]]:
    """Select broad, deterministic V2 coverage across the entire history."""
    if count < 10:
        raise ValueError("V2 acceptance requires at least 10 validation cases")

    categories: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [
        ("initialization", lambda row: any(e.startswith("initialization_") for e in row["events"])),
        ("guard_break_up", lambda row: "guard_break_up" in row["events"]),
        ("guard_break_down", lambda row: "guard_break_down" in row["events"]),
        ("new_wave_up", lambda row: "new_wave_up" in row["events"]),
        ("new_wave_down", lambda row: "new_wave_down" in row["events"]),
        ("guard_update", lambda row: "guard_update" in row["events"]),
        ("progress_update", lambda row: "progress_update" in row["events"]),
        ("candidate_start", lambda row: "candidate_start" in row["events"]),
        ("candidate_replacement", lambda row: "candidate_replacement" in row["events"]),
        ("range_evolution", lambda row: "range_evolution" in row["events"]),
        ("pivot_high", lambda row: "pivot_confirm_h" in row["events"]),
        ("pivot_low", lambda row: "pivot_confirm_l" in row["events"]),
        ("alive", lambda row: _state(row["snapshot"]) in ALIVE_STATES),
        ("transition", lambda row: _state(row["snapshot"]) == "transition"),
    ]

    buckets = [(name, [row for row in trace if predicate(row)]) for name, predicate in categories]
    selected: list[dict[str, Any]] = []
    used: set[int] = set()

    # Round-robin through early/middle/late representatives so one scenario cannot dominate.
    for pass_number in range(3):
        for category, rows in buckets:
            if len(selected) >= count or not rows:
                break
            candidates = _spread(rows, 3)
            candidate = candidates[min(pass_number, len(candidates) - 1)]
            index = candidate["bar_index"]
            if index in used:
                continue
            copied = dict(candidate)
            copied["selection_category"] = category
            selected.append(copied)
            used.add(index)
        if len(selected) >= count:
            break

    if len(selected) < count:
        eventful = [
            row
            for row in trace
            if row["events"] != ["uninitialized_observation"] and row["bar_index"] not in used
        ]
        for row in _spread(eventful, count - len(selected)):
            copied = dict(row)
            copied["selection_category"] = "coverage_fill"
            selected.append(copied)
            used.add(row["bar_index"])

    if len(selected) < count:
        raise RuntimeError(f"Only {len(selected)} eligible V2 cases found; requested {count}")
    return sorted(selected[:count], key=lambda row: row["bar_index"])


def _bar_index_by_dt(bars: Sequence[PriceBar]) -> dict[str, int]:
    return {bar.bar_dt: index for index, bar in enumerate(bars)}


def context_window(bars: Sequence[PriceBar], center_dt: str, radius: int = 2) -> list[dict[str, Any]]:
    index_by_dt = _bar_index_by_dt(bars)
    center = index_by_dt.get(center_dt)
    if center is None:
        return []
    start = max(0, center - radius)
    end = min(len(bars), center + radius + 1)
    return [bar_dict(bars[index], index) for index in range(start, end)]


def _find_pivot(
    pivots: Sequence[Pivot],
    extreme_dt: str | None,
    price: int | None,
    pivot_type: str | None = None,
) -> Pivot | None:
    if extreme_dt is None or price is None:
        return None
    for pivot in pivots:
        if pivot.extreme_bar_dt != extreme_dt or pivot.price != price:
            continue
        if pivot_type is None or pivot.pivot_type.value == pivot_type:
            return pivot
    return None


def _audit_pivot(
    role: str,
    pivot: Pivot | None,
    bars: Sequence[PriceBar],
    k: int,
) -> dict[str, Any] | None:
    if pivot is None:
        return None
    window = context_window(bars, pivot.extreme_bar_dt, radius=k)
    center = next((bar for bar in window if bar["bar_dt"] == pivot.extreme_bar_dt), None)
    neighbors = [bar for bar in window if bar["bar_dt"] != pivot.extreme_bar_dt]
    strict = False
    if center is not None and len(neighbors) == 2 * k:
        if pivot.pivot_type.value == "H":
            strict = all(center["high"] > bar["high"] for bar in neighbors)
        else:
            strict = all(center["low"] < bar["low"] for bar in neighbors)
    return {
        "role": role,
        "pivot": pivot_dict(pivot),
        "strict_fractal_check": strict,
        "ohlc_window": window,
    }


def enrich_case(
    row: dict[str, Any],
    bars: Sequence[PriceBar],
    pivots: Sequence[Pivot],
    k: int,
) -> dict[str, Any]:
    current: CoreStateSnapshot = row["snapshot"]
    previous: CoreStateSnapshot | None = row["previous_snapshot"]
    direction = _direction(current)
    guard_type = "L" if direction == "up" else "H" if direction == "down" else None
    progress_type = "H" if direction == "up" else "L" if direction == "down" else None
    candidate_direction = (
        current.active_candidate_direction.value if current.active_candidate_direction is not None else None
    )
    candidate_type = "L" if candidate_direction == "up" else "H" if candidate_direction == "down" else None

    audits: list[dict[str, Any]] = []
    candidates = [
        ("confirmed_on_case_bar", row["confirmed_pivot"]),
        (
            "effective_guard",
            _find_pivot(
                pivots,
                current.current_effective_guard_extreme_bar_dt,
                current.current_effective_guard_price,
                guard_type,
            ),
        ),
        (
            "progress_extreme",
            _find_pivot(
                pivots,
                current.progress_extreme_bar_dt,
                current.progress_extreme_price,
                progress_type,
            ),
        ),
        (
            "active_candidate_guard",
            _find_pivot(
                pivots,
                current.active_candidate_guard_extreme_bar_dt,
                current.active_candidate_guard_price,
                candidate_type,
            ),
        ),
    ]
    seen: set[tuple[str, str, int]] = set()
    for role, pivot in candidates:
        if pivot is None:
            continue
        key = (role, pivot.extreme_bar_dt, pivot.price)
        if key in seen:
            continue
        audit = _audit_pivot(role, pivot, bars, k)
        if audit is not None:
            audits.append(audit)
            seen.add(key)

    break_check = None
    if previous is not None and _state(previous) in ALIVE_STATES and _state(current) == "transition":
        guard = previous.current_effective_guard_price
        if _direction(previous) == "up":
            actual = row["bar"].low
            passed = guard is not None and actual < guard
            expression = f"low {actual} < guard {guard}"
        else:
            actual = row["bar"].high
            passed = guard is not None and actual > guard
            expression = f"high {actual} > guard {guard}"
        break_check = {"expression": expression, "passed": passed}

    return {
        "selection_category": row["selection_category"],
        "events": row["events"],
        "event_bar": bar_dict(row["bar"], row["bar_index"]),
        "previous_core_snapshot": snapshot_dict(previous) if previous is not None else None,
        "core_snapshot": snapshot_dict(current),
        "confirmed_pivot": pivot_dict(row["confirmed_pivot"]),
        "break_check": break_check,
        "pivot_audits": audits,
    }


def _price(value: int | None) -> str:
    return "—" if value is None else f"{value} ({value / 1000:.3f})"


def generate_transition_markdown(
    trace: Sequence[dict[str, Any]], output_file: Path, symbol: str
) -> None:
    transitions = []
    for row in trace:
        previous = row["previous_snapshot"]
        current = row["snapshot"]
        if previous is not None and _state(previous) != _state(current):
            transitions.append(row)
    lines = [
        f"# {symbol} Core 状态转换时间线",
        "",
        f"- 输入 bar 数: {len(trace)}",
        f"- 状态转换数: {len(transitions)}",
        "- 数据来源: 本地 TDX `.day` 原始记录",
        "",
        "| Bar | 日期 | 前状态 | 后状态 | 方向 | Guard | Progress | 事件 |",
        "|---:|---|---|---|---|---:|---:|---|",
    ]
    for row in transitions:
        previous = row["previous_snapshot"]
        current = row["snapshot"]
        lines.append(
            f"| {row['bar_index']} | {row['bar_dt']} | {_state(previous)} | {_state(current)} | "
            f"{_direction(current) or '—'} | {current.current_effective_guard_price or '—'} | "
            f"{current.progress_extreme_price or '—'} | {', '.join(row['events'])} |"
        )
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _render_window(window: Sequence[dict[str, Any]], extreme_dt: str) -> list[str]:
    lines = [
        "| Bar | 日期 | O | H | L | C | 位置 |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for bar in window:
        marker = "**extreme**" if bar["bar_dt"] == extreme_dt else ""
        lines.append(
            f"| {bar['bar_index']} | {bar['bar_dt']} | {_price(bar['open'])} | {_price(bar['high'])} | "
            f"{_price(bar['low'])} | {_price(bar['close'])} | {marker} |"
        )
    return lines


def generate_checklist(cases: Sequence[dict[str, Any]], output_file: Path, symbol: str, k: int) -> None:
    lines = [
        f"# V2 人工结构验证清单 - {symbol}",
        "",
        f"**验证案例数**: {len(cases)}（验收门槛 ≥ 10）  ",
        "**生成日期**: 2026-07-27  ",
        f"**Pivot 参数**: fractal k={k}",
        "",
        "> 以本文件内嵌的 TDX 原始 OHLC 为审计基准。外部行情软件若启用了前/后复权，价格可能不同。",
        "",
        "## 判定规则",
        "",
        f"- High Pivot: 中心 high 严格高于左右各 {k} 根 high。",
        f"- Low Pivot: 中心 low 严格低于左右各 {k} 根 low。",
        f"- Pivot 在 extreme bar 发生，在第 {k} 根后续 bar 确认。",
        "- UP guard break: 当前 bar.low < 旧 guard。",
        "- DOWN guard break: 当前 bar.high > 旧 guard。",
        "",
        "---",
    ]

    for number, case in enumerate(cases, 1):
        snap = case["core_snapshot"]
        event_bar = case["event_bar"]
        lines.extend(
            [
                "",
                f"## {number}. Bar #{event_bar['bar_index']} — {event_bar['bar_dt']}",
                "",
                f"- 选样类别: `{case['selection_category']}`",
                f"- 事件: `{', '.join(case['events'])}`",
                f"- 状态: `{snap['system_state']}` / 方向: `{snap['direction']}`",
                f"- Event OHLC: O={_price(event_bar['open'])}, H={_price(event_bar['high'])}, "
                f"L={_price(event_bar['low'])}, C={_price(event_bar['close'])}",
                f"- Guard: {_price(snap['current_effective_guard_price'])} "
                f"@ {snap['current_effective_guard_extreme_bar_dt'] or '—'} "
                f"(confirm {snap['current_effective_guard_confirm_bar_dt'] or '—'})",
                f"- Progress: {_price(snap['progress_extreme_price'])} "
                f"@ {snap['progress_extreme_bar_dt'] or '—'}",
            ]
        )
        if case["break_check"] is not None:
            lines.append(
                f"- 自动 break 算式: `{case['break_check']['expression']}` → "
                f"`{case['break_check']['passed']}`"
            )

        lines.extend(["", "### Pivot 审计窗口", ""])
        if not case["pivot_audits"]:
            lines.append("本案例没有可引用的已确认 pivot（仅做状态/边界观察）。")
        for audit in case["pivot_audits"]:
            pivot = audit["pivot"]
            lines.extend(
                [
                    f"#### {audit['role']}: {pivot['pivot_type']} {pivot['extreme_bar_dt']} "
                    f"@ {_price(pivot['price'])}",
                    "",
                    f"- 引擎确认日: `{pivot['confirm_bar_dt']}`",
                    f"- 自动严格分形检查: `{audit['strict_fractal_check']}`",
                    "",
                    *_render_window(audit["ohlc_window"], pivot["extreme_bar_dt"]),
                    "",
                ]
            )

        lines.extend(
            [
                "### 人工结论",
                "",
                "- [ ] Pivot 识别与确认延迟正确",
                "- [ ] Guard 引用与方向规则正确",
                "- [ ] Progress 引用与方向规则正确",
                "- [ ] 状态转换 / break / candidate 行为正确",
                "- 结论: ☐ 通过 / ☐ 不通过 / ☐ 待确认",
                "- 备注:",
                "",
                "```text",
                "",
                "```",
                "",
                "---",
            ]
        )

    lines.extend(
        [
            "",
            "## 汇总",
            "",
            f"- 已核验案例: _____ / {len(cases)}",
            f"- Pivot 正确: _____ / {len(cases)}",
            f"- Guard/Progress 正确: _____ / {len(cases)}",
            f"- 状态转换正确: _____ / {len(cases)}",
            "- V2 结论: ☐ 通过 / ☐ 不通过 / ☐ 需修复后重验",
            "",
            "### 验收标准",
            "",
            "- 至少人工核验 10 个案例",
            "- 覆盖 initialization、alive、transition、guard break、new wave",
            "- Pivot 准确率 > 95%",
            "- Guard/Progress 准确率 > 90%",
        ]
    )
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_readme(
    output_file: Path,
    symbol: str,
    bar_count: int,
    case_count: int,
    source_file: Path,
) -> None:
    content = f"""# V2 验证材料包

**生成日期**: 2026-07-27  
**标的**: {symbol}  
**输入 bar 数**: {bar_count}  
**人工验证案例数**: {case_count}  
**源文件**: `{source_file}`

## 文件

1. `01-STATE-TRANSITIONS.md`：完整 Core 状态转换时间线。
2. `02-VALIDATION-CHECKLIST.md`：15 个案例及其原始 OHLC / Pivot 窗口。
3. `03-SNAPSHOTS-DATA.json`：相同案例的机器可读审计数据。
4. `MALF_V2_1_AUTHORITY_REFERENCE.md`：规格权威摘录。

## 使用方法

1. 打开 `02-VALIDATION-CHECKLIST.md`。
2. 按内嵌的 5-bar OHLC 窗口手工判断 High/Low Pivot。
3. 核对 extreme 日期、confirm 日期、Guard、Progress 与 break 算式。
4. 每个案例填写通过/不通过和备注，最后完成汇总。

## 重要说明

- 本包不再读取 Service 快照中不存在的 H0/L0/H1/L1 字段。
- 所有 Pivot 审计都追溯到本地 TDX 原始 OHLC。
- 自动 `strict_fractal_check` 只是预检查，不能替代 V2 人工签字。
- 公开行情若启用复权，价格可能与本包不同；V2 应以同一原始数据源为准。
"""
    output_file.write_text(content, encoding="utf-8")


def prepare_package(
    symbol: str,
    market: str,
    tdx_root: Path,
    output_dir: Path,
    count: int = 15,
    k: int = 2,
    max_bars: int | None = None,
) -> list[dict[str, Any]]:
    bars = load_tdx_daily_bars(symbol, tdx_data_path=str(tdx_root), market=market)
    if max_bars is not None:
        bars = bars[:max_bars]
    if not bars:
        raise ValueError(f"No bars loaded for {market}{symbol}")

    trace, pivots = build_trace(bars, k=k)
    selected = select_validation_cases(trace, count=count)
    cases = [enrich_case(row, bars, pivots, k=k) for row in selected]

    output_dir.mkdir(parents=True, exist_ok=True)
    generate_transition_markdown(trace, output_dir / "01-STATE-TRANSITIONS.md", symbol)
    generate_checklist(cases, output_dir / "02-VALIDATION-CHECKLIST.md", symbol, k)
    (output_dir / "03-SNAPSHOTS-DATA.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    spec_source = PROJECT_ROOT / "docs" / "spec" / "MALF_V2_1_AUTHORITY_REFERENCE.md"
    if spec_source.exists():
        shutil.copy2(spec_source, output_dir / spec_source.name)
    source_file = tdx_root / "vipdoc" / market / "lday" / f"{market}{symbol}.day"
    generate_readme(output_dir / "README.md", symbol, len(bars), len(cases), source_file)
    return cases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a V2 manual-validation package")
    parser.add_argument("--symbol", default="510300")
    parser.add_argument("--market", choices=("sh", "sz"), default="sh")
    parser.add_argument("--tdx-root", default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / ".work" / "V2-validation-package",
    )
    parser.add_argument("--count", type=int, default=15)
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--max-bars", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tdx_root = discover_tdx_root(args.tdx_root)
    print(f"Loading {args.market}{args.symbol} from {tdx_root} ...")
    cases = prepare_package(
        symbol=args.symbol,
        market=args.market,
        tdx_root=tdx_root,
        output_dir=args.output_dir,
        count=args.count,
        k=args.k,
        max_bars=args.max_bars,
    )
    print(f"Generated {len(cases)} V2 cases in {args.output_dir}")
    for case in cases:
        event = case["event_bar"]
        print(
            f"  #{event['bar_index']:4d} {event['bar_dt']} "
            f"[{case['selection_category']}] {', '.join(case['events'])}"
        )


if __name__ == "__main__":
    main()
