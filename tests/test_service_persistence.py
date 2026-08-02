"""
测试 Service 层序列化、持久化和中断恢复

测试场景：
1. 序列化/反序列化往返一致性
2. Lineage hash 确定性
3. 快照持久化
4. 中断恢复
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.malf.persistence import (
    serialize_snapshot,
    deserialize_snapshot,
    calculate_lineage_hash,
    ensure_var_directory,
    persist_snapshot,
    update_current_pointer,
    load_last_snapshot,
    should_resume_from,
)
from src.malf.types import WaveStructuralSnapshot


def test_serialization_roundtrip():
    """测试场景 1: 序列化/反序列化往返一致性"""

    # 创建测试快照
    snapshot = WaveStructuralSnapshot(
        symbol="TEST",
        timeframe="D1",
        bar_dt="2024-01-01",
        bar_index=0,
        system_state="UP_ALIVE",
        direction="UP",
        active_wave_id="wave_001",
        progress_extreme_price=115,
        progress_extreme_bar_dt="2024-01-01",
        guard_price=99,
        guard_bar_dt="2023-12-31",
        bar_count=5,
        break_bar_dt=None,
        break_price=None,
        transition_boundary_high=None,
        transition_boundary_low=None,
        candidate_pivot_type=None,
        candidate_pivot_price=None,
        range_boundary_high_now=None,
        range_boundary_low_now=None,
        range_evolution_count=None,
        range_candidate_replacement_count=None,
        range_type=None,
        wave_span_rank=0.65,
        wave_range_rank=0.72,
        wave_stagnation_rank=0.45,
        range_span_rank=None,
        range_evolution_rank=None,
        range_replacement_rank=None,
        range_resolution_distance_rank=None,
        p2_same_dir_span_momentum=0.15,
        p2_same_dir_range_momentum=0.20,
        p2_same_dir_label="accelerating",
        p3_cross_dir_span_momentum=0.25,
        p3_cross_dir_range_momentum=0.30,
        p3_cross_dir_label="self_dominant",
        p4_cross_span_momentum=0.10,
        p4_cross_range_momentum=0.12,
        p4_cross_alive_warning=True,
        rule_versions={
            "pivot_rule": "fractal_k2_v1.0",
            "core_version": "v2.1",
        },
        lineage_hash="abc123def456",
        reason_codes=["wave_alive", "operational_disabled"],
        usage="verification_only",
        freshness="current",
    )

    # 序列化
    json_str = serialize_snapshot(snapshot)

    # 验证是 JSON 格式
    assert isinstance(json_str, str)
    json_data = json.loads(json_str)
    assert json_data["symbol"] == "TEST"
    assert json_data["bar_dt"] == "2024-01-01"

    # 反序列化
    restored_snapshot = deserialize_snapshot(json_str)

    # 验证往返一致性
    assert restored_snapshot.symbol == snapshot.symbol
    assert restored_snapshot.bar_dt == snapshot.bar_dt
    assert restored_snapshot.bar_index == snapshot.bar_index
    assert restored_snapshot.system_state == snapshot.system_state
    assert restored_snapshot.usage == snapshot.usage
    assert restored_snapshot.reason_codes == snapshot.reason_codes
    assert restored_snapshot.wave_span_rank == snapshot.wave_span_rank


def test_lineage_hash_determinism():
    """测试场景 2: Lineage hash 确定性"""

    # 创建快照数据
    snapshot_data_1 = {
        "symbol": "TEST",
        "timeframe": "D1",
        "bar_dt": "2024-01-01",
        "bar_index": 0,
        "system_state": "UP_ALIVE",
        "direction": "UP",
        "current_effective_guard_price": 99,
        "progress_extreme_price": 115,
        "bar_count": 5,
        "wave_span_rank": 0.65,
        "wave_range_rank": 0.72,
        "p2_same_dir_label": "accelerating",
        "p3_cross_dir_label": "self_dominant",
        "rule_versions": {
            "pivot_rule": "fractal_k2_v1.0",
            "core_version": "v2.1",
        },
    }

    # 计算 hash 两次
    hash_1 = calculate_lineage_hash(snapshot_data_1)
    hash_2 = calculate_lineage_hash(snapshot_data_1)

    # 验证确定性（相同输入 → 相同 hash）
    assert hash_1 == hash_2

    # 验证 hash 格式（SHA256 hex = 64 字符）
    assert len(hash_1) == 64
    assert all(c in "0123456789abcdef" for c in hash_1)

    # 创建不同数据
    snapshot_data_2 = snapshot_data_1.copy()
    snapshot_data_2["bar_dt"] = "2024-01-02"  # 修改一个字段

    # 计算不同数据的 hash
    hash_3 = calculate_lineage_hash(snapshot_data_2)

    # 验证不同输入 → 不同 hash
    assert hash_1 != hash_3


def test_var_directory_creation():
    """测试 var/ 目录结构创建"""

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "var"

        # 确保目录创建
        ensure_var_directory(base_path)

        # 验证目录存在
        assert base_path.exists()
        assert (base_path / "staging").exists()
        assert (base_path / "published").exists()


def test_snapshot_persistence():
    """测试场景 3: 快照持久化"""

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "var"

        # 创建测试快照
        snapshot = WaveStructuralSnapshot(
            symbol="TEST",
            timeframe="D1",
            bar_dt="2024-01-01",
            bar_index=0,
            system_state="UP_ALIVE",
            direction="UP",
            active_wave_id="wave_001",
            progress_extreme_price=115,
            progress_extreme_bar_dt="2024-01-01",
            guard_price=99,
            guard_bar_dt="2023-12-31",
            bar_count=5,
            break_bar_dt=None,
            break_price=None,
            transition_boundary_high=None,
            transition_boundary_low=None,
            candidate_pivot_type=None,
            candidate_pivot_price=None,
            range_boundary_high_now=None,
            range_boundary_low_now=None,
            range_evolution_count=None,
            range_candidate_replacement_count=None,
            range_type=None,
            wave_span_rank=0.65,
            wave_range_rank=0.72,
            wave_stagnation_rank=0.45,
            range_span_rank=None,
            range_evolution_rank=None,
            range_replacement_rank=None,
            range_resolution_distance_rank=None,
            p2_same_dir_span_momentum=0.15,
            p2_same_dir_range_momentum=0.20,
            p2_same_dir_label="accelerating",
            p3_cross_dir_span_momentum=0.25,
            p3_cross_dir_range_momentum=0.30,
            p3_cross_dir_label="self_dominant",
            p4_cross_span_momentum=0.10,
            p4_cross_range_momentum=0.12,
            p4_cross_alive_warning=True,
            rule_versions={"pivot_rule": "fractal_k2_v1.0"},
            lineage_hash="abc123",
            reason_codes=["wave_alive"],
            usage="verification_only",
            freshness="current",
        )

        # 持久化快照
        filepath = persist_snapshot(snapshot, base_path)

        # 验证文件存在
        assert filepath.exists()
        assert filepath.name == "TEST_D1_2024-01-01.jsonl"

        # 验证文件内容
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert "TEST" in content
            assert "2024-01-01" in content

        # 更新 current.json
        update_current_pointer(snapshot, filepath, base_path)

        # 验证 current.json 存在
        current_json_path = base_path / "current.json"
        assert current_json_path.exists()

        # 验证 current.json 内容
        with open(current_json_path, "r", encoding="utf-8") as f:
            pointer_data = json.load(f)
            assert pointer_data["last_bar_dt"] == "2024-01-01"
            assert pointer_data["last_bar_index"] == 0


def test_interrupt_recovery():
    """测试场景 4: 中断恢复"""

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "var"

        # 创建初始快照
        snapshot_1 = WaveStructuralSnapshot(
            symbol="TEST",
            timeframe="D1",
            bar_dt="2024-01-01",
            bar_index=0,
            system_state="UP_ALIVE",
            direction="UP",
            active_wave_id="wave_001",
            progress_extreme_price=110,
            progress_extreme_bar_dt="2024-01-01",
            guard_price=95,
            guard_bar_dt="2023-12-31",
            bar_count=3,
            break_bar_dt=None,
            break_price=None,
            transition_boundary_high=None,
            transition_boundary_low=None,
            candidate_pivot_type=None,
            candidate_pivot_price=None,
            range_boundary_high_now=None,
            range_boundary_low_now=None,
            range_evolution_count=None,
            range_candidate_replacement_count=None,
            range_type=None,
            wave_span_rank=0.50,
            wave_range_rank=0.60,
            wave_stagnation_rank=0.40,
            range_span_rank=None,
            range_evolution_rank=None,
            range_replacement_rank=None,
            range_resolution_distance_rank=None,
            p2_same_dir_span_momentum=0.10,
            p2_same_dir_range_momentum=0.15,
            p2_same_dir_label="stable",
            p3_cross_dir_span_momentum=0.20,
            p3_cross_dir_range_momentum=0.25,
            p3_cross_dir_label="balanced",
            p4_cross_span_momentum=0.05,
            p4_cross_range_momentum=0.08,
            p4_cross_alive_warning=True,
            rule_versions={"core_version": "v2.1"},
            lineage_hash="hash001",
            reason_codes=["wave_alive"],
            usage="verification_only",
            freshness="current",
        )

        # 持久化初始快照
        filepath_1 = persist_snapshot(snapshot_1, base_path)
        update_current_pointer(snapshot_1, filepath_1, base_path)

        # 模拟中断...

        # 恢复：加载最后快照
        result = load_last_snapshot(base_path)
        assert result is not None

        restored_snapshot, last_bar_dt = result

        # 验证恢复的快照
        assert restored_snapshot.symbol == "TEST"
        assert restored_snapshot.bar_dt == "2024-01-01"
        assert last_bar_dt == "2024-01-01"

        # 测试 should_resume_from
        assert should_resume_from("2024-01-01", "2024-01-01") is True  # 已处理
        assert should_resume_from("2024-01-01", "2024-01-02") is False  # 需要处理
        assert should_resume_from("2024-01-01", "2023-12-31") is True  # 已处理（更早）


def test_load_last_snapshot_when_none_exists():
    """测试当没有快照时 load_last_snapshot 返回 None"""

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "var"

        # 目录不存在
        result = load_last_snapshot(base_path)
        assert result is None

        # 目录存在但没有 current.json
        ensure_var_directory(base_path)
        result = load_last_snapshot(base_path)
        assert result is None
