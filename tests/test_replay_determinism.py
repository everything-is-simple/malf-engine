"""测试 O8 Replay 确定性（第五刀 Task 3）。

验证 MALF 引擎的确定性：相同输入 → 相同输出（除审计元数据）。

规格依据：
- 规格 §7 / O8 Replay 确定性
- 规格 §7.6 runtime_fingerprint
- 设计文档：docs/t5_replay_test_design.md
"""

import dataclasses
import json
from pathlib import Path

from malf.core_engine import MALFCoreEngine
from malf.types import CoreStateSnapshot, PriceBar


def load_golden_fixture():
    """加载 uninitialized_to_up_alive.json fixture。"""
    fixture_path = Path(__file__).parent / "fixtures" / "uninitialized_to_up_alive.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def bars_from_fixture(fixture):
    """从 fixture 构造 PriceBar 列表。"""
    return [
        PriceBar(
            symbol="TEST",
            timeframe="day",
            bar_dt=b["bar_dt"],
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"],
        )
        for b in fixture["input_bars"]
    ]


def snapshots_equal_except_fingerprint(s1: CoreStateSnapshot, s2: CoreStateSnapshot) -> bool:
    """比对两个 snapshot，忽略 runtime_fingerprint 和 note。

    根据规格 §7.6，runtime_fingerprint 是审计元数据，不参与 replay。
    note 字段也不参与相等比较（dataclass compare=False）。
    """
    s1_normalized = dataclasses.replace(s1, runtime_fingerprint="", note="")
    s2_normalized = dataclasses.replace(s2, runtime_fingerprint="", note="")
    return s1_normalized == s2_normalized


def test_replay_same_fixture_twice():
    """基础 Replay 测试：同一 fixture 跑两遍，结果必须完全一致。

    验证 O8 确定性：相同输入 → 相同 snapshots（除 runtime_fingerprint）。
    """
    fixture = load_golden_fixture()
    bars = bars_from_fixture(fixture)

    # Run 1
    engine1 = MALFCoreEngine(k=fixture["params"]["k"])
    run1_snapshots = []
    for bar in bars:
        snapshot = engine1.on_bar(bar)
        run1_snapshots.append(snapshot)

    # Run 2
    engine2 = MALFCoreEngine(k=fixture["params"]["k"])
    run2_snapshots = []
    for bar in bars:
        snapshot = engine2.on_bar(bar)
        run2_snapshots.append(snapshot)

    # 验证：两次运行的 snapshot 数量一致
    assert len(run1_snapshots) == len(run2_snapshots)
    assert len(run1_snapshots) == len(bars)

    # 验证：逐 snapshot 比对（除 runtime_fingerprint）
    for i, (s1, s2) in enumerate(zip(run1_snapshots, run2_snapshots)):
        assert snapshots_equal_except_fingerprint(s1, s2), (
            f"Snapshot {i} (bar_dt={s1.bar_dt}) differs between run1 and run2.\n"
            f"This indicates non-determinism in the engine.\n"
            f"Run1: {s1}\n"
            f"Run2: {s2}"
        )


def test_replay_cross_session():
    """跨 Session Replay 测试：重启 engine 不影响确定性。

    场景：
    1. 运行前 6 根 bars → partial_run
    2. 销毁 engine
    3. 重新运行全部 12 根 bars → full_run
    4. 验证前 6 个 snapshot 一致
    """
    fixture = load_golden_fixture()
    bars = bars_from_fixture(fixture)

    # Partial run (前 6 根 bars)
    engine_partial = MALFCoreEngine(k=fixture["params"]["k"])
    partial_snapshots = []
    for bar in bars[:6]:
        snapshot = engine_partial.on_bar(bar)
        partial_snapshots.append(snapshot)

    # Full run (全部 12 根 bars)
    engine_full = MALFCoreEngine(k=fixture["params"]["k"])
    full_snapshots = []
    for bar in bars:
        snapshot = engine_full.on_bar(bar)
        full_snapshots.append(snapshot)

    # 验证：前 6 个 snapshot 一致
    for i in range(6):
        assert snapshots_equal_except_fingerprint(partial_snapshots[i], full_snapshots[i]), (
            f"Snapshot {i} differs between partial and full run.\n"
            f"This indicates cross-session replay failure.\n"
            f"Partial: {partial_snapshots[i]}\n"
            f"Full: {full_snapshots[i]}"
        )


def test_runtime_fingerprint_isolation():
    """runtime_fingerprint 隔离测试：验证格式正确且不影响 replay。

    根据规格 §7.6：
    - runtime_fingerprint 格式：py{version}|{platform}|{implementation}
    - 例如：py3.10.19|win32|CPython
    - 该字段记录但不进 lineage_hash
    """
    fixture = load_golden_fixture()
    bars = bars_from_fixture(fixture)

    engine = MALFCoreEngine(k=fixture["params"]["k"])
    snapshots = []
    for bar in bars:
        snapshot = engine.on_bar(bar)
        snapshots.append(snapshot)

    # 验证所有 snapshot 的 runtime_fingerprint 格式正确
    for i, snapshot in enumerate(snapshots):
        fp = snapshot.runtime_fingerprint

        # 非空
        assert fp, f"Snapshot {i}: runtime_fingerprint is empty"

        # 格式：py{version}|{platform}|{implementation}
        parts = fp.split("|")
        assert len(parts) == 3, f"Snapshot {i}: runtime_fingerprint format wrong: {fp}"

        py_version, platform, implementation = parts

        # Python 版本以 "py" 开头
        assert py_version.startswith("py"), f"Snapshot {i}: py_version should start with 'py': {py_version}"

        # 平台非空
        assert platform, f"Snapshot {i}: platform is empty"

        # 实现非空
        assert implementation, f"Snapshot {i}: implementation is empty"


def test_version_fields_present():
    """版本字段验证：所有版本字段非空且格式正确。

    验证规格要求的版本标记：
    - core_rule_version
    - pivot_detection_rule_version
    - price_policy
    - schema_version
    """
    fixture = load_golden_fixture()
    bars = bars_from_fixture(fixture)

    engine = MALFCoreEngine(k=fixture["params"]["k"])

    # 取最后一个 snapshot（UP_ALIVE 状态，字段最全）
    snapshot = None
    for bar in bars:
        snapshot = engine.on_bar(bar)

    # 验证 core_rule_version
    assert snapshot.core_rule_version, "core_rule_version is empty"
    assert snapshot.core_rule_version.startswith("core-"), f"core_rule_version format wrong: {snapshot.core_rule_version}"

    # 验证 pivot_detection_rule_version
    assert snapshot.pivot_detection_rule_version, "pivot_detection_rule_version is empty"
    # 格式：fractal-k{k}-v{version}
    assert "fractal" in snapshot.pivot_detection_rule_version, f"pivot_detection_rule_version format wrong: {snapshot.pivot_detection_rule_version}"

    # 验证 price_policy
    assert snapshot.price_policy, "price_policy is empty"
    assert snapshot.price_policy in ["int_fixed", "round_2"], f"price_policy invalid: {snapshot.price_policy}"

    # 验证 schema_version
    assert snapshot.schema_version, "schema_version is empty"
    assert snapshot.schema_version.startswith("malf-"), f"schema_version format wrong: {snapshot.schema_version}"
