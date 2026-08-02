"""
MALF v2.1 Service 层 - 序列化与持久化

规格权威：MALF_05_Service_v2_1-deepseek-20260726.md §4

职责：
- 实现 WaveStructuralSnapshot 序列化/反序列化（JSON）
- 实现 lineage_hash 计算
- 实现快照持久化（var/ 目录）
- 实现中断恢复机制
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Any
from dataclasses import asdict
from datetime import datetime

from .types import WaveStructuralSnapshot


# ============================================================================
# 序列化/反序列化（规格 §4）
# ============================================================================


def serialize_snapshot(snapshot: WaveStructuralSnapshot) -> str:
    """
    序列化 WaveStructuralSnapshot 为 JSON 字符串（规格 §4）。

    使用 JSON Lines 格式，每个快照一行。

    Args:
        snapshot: WaveStructuralSnapshot 对象

    Returns:
        JSON 字符串（单行，无换行符）
    """
    # 转换为字典
    data = asdict(snapshot)

    # 序列化为 JSON（紧凑格式，排序键确保一致性）
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)

    return json_str


def deserialize_snapshot(json_str: str) -> WaveStructuralSnapshot:
    """
    反序列化 JSON 字符串为 WaveStructuralSnapshot（规格 §4）。

    Args:
        json_str: JSON 字符串

    Returns:
        WaveStructuralSnapshot 对象
    """
    # 解析 JSON
    data = json.loads(json_str)

    # 重建对象
    snapshot = WaveStructuralSnapshot(**data)

    return snapshot


# ============================================================================
# Lineage Hash 计算（规格 §5）
# ============================================================================


def calculate_lineage_hash(snapshot_data: dict[str, Any]) -> str:
    """
    计算 lineage_hash（计算链路哈希，规格 §5）。

    从输入数据到最终快照的完整计算路径的哈希值。
    用于审计和 replay 验证。

    相同输入 + 相同版本 → 相同 lineage_hash（确定性）

    Args:
        snapshot_data: 快照数据字典（包含所有字段）

    Returns:
        SHA256 哈希字符串（16进制，64字符）
    """
    # 提取参与 hash 计算的字段（排除 lineage_hash 自身和 reason_codes）
    hash_input = {
        "symbol": snapshot_data["symbol"],
        "timeframe": snapshot_data["timeframe"],
        "bar_dt": snapshot_data["bar_dt"],
        "bar_index": snapshot_data["bar_index"],
        "system_state": snapshot_data["system_state"],
        "direction": snapshot_data["direction"],
        "rule_versions": snapshot_data["rule_versions"],
        # 添加所有核心计算字段
        "core_fields": {
            "guard_price": snapshot_data.get("current_effective_guard_price"),
            "progress_price": snapshot_data.get("progress_extreme_price"),
            "bar_count": snapshot_data.get("bar_count"),
        },
        # 添加 Lifespan 字段
        "lifespan_fields": {
            "wave_span_rank": snapshot_data.get("wave_span_rank"),
            "wave_range_rank": snapshot_data.get("wave_range_rank"),
        },
        # 添加 Position 字段
        "position_fields": {
            "p2_label": snapshot_data.get("p2_same_dir_label"),
            "p3_label": snapshot_data.get("p3_cross_dir_label"),
        },
    }

    # 序列化为 JSON（排序键确保一致性）
    json_str = json.dumps(hash_input, sort_keys=True)

    # 计算 SHA256
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))

    return hash_obj.hexdigest()


# ============================================================================
# 持久化（规格 §4 var/ 目录）
# ============================================================================


def ensure_var_directory(base_path: Path = Path("var")) -> None:
    """
    确保 var/ 目录结构存在（规格 §4）。

    创建目录结构：
    var/
    ├── staging/
    ├── published/
    └── current.json（文件，不是目录）

    Args:
        base_path: var/ 目录的根路径
    """
    # 创建主目录
    base_path.mkdir(parents=True, exist_ok=True)

    # 创建子目录
    (base_path / "staging").mkdir(exist_ok=True)
    (base_path / "published").mkdir(exist_ok=True)


def persist_snapshot(
    snapshot: WaveStructuralSnapshot,
    base_path: Path = Path("var")
) -> Path:
    """
    持久化快照到 var/published/（规格 §4）。

    路径格式：var/published/{symbol}/{timeframe}/{symbol}_{timeframe}_{bar_dt}.jsonl

    Args:
        snapshot: WaveStructuralSnapshot 对象
        base_path: var/ 目录的根路径

    Returns:
        写入的文件路径
    """
    # 确保目录存在
    ensure_var_directory(base_path)

    # 构造文件路径
    published_dir = base_path / "published" / snapshot.symbol / snapshot.timeframe
    published_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{snapshot.symbol}_{snapshot.timeframe}_{snapshot.bar_dt}.jsonl"
    filepath = published_dir / filename

    # 序列化快照
    json_str = serialize_snapshot(snapshot)

    # 写入文件（追加模式，每个快照一行）
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json_str + "\n")

    return filepath


def update_current_pointer(
    snapshot: WaveStructuralSnapshot,
    snapshot_path: Path,
    base_path: Path = Path("var")
) -> None:
    """
    更新 current.json 原子指针（规格 §4）。

    指向最新成功发布的快照。

    Args:
        snapshot: 最新的 WaveStructuralSnapshot 对象
        snapshot_path: 快照文件路径
        base_path: var/ 目录的根路径
    """
    current_json_path = base_path / "current.json"

    # 构造指针数据
    pointer_data = {
        "last_snapshot_path": str(snapshot_path),
        "last_bar_dt": snapshot.bar_dt,
        "last_bar_index": snapshot.bar_index,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }

    # 原子写入（先写临时文件，再重命名）
    temp_path = current_json_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(pointer_data, f, indent=2)

    # 原子重命名
    temp_path.replace(current_json_path)


# ============================================================================
# 中断恢复（规格 §4 中断恢复策略）
# ============================================================================


def load_last_snapshot(base_path: Path = Path("var")) -> Optional[tuple[WaveStructuralSnapshot, str]]:
    """
    从 current.json 加载最后一个成功发布的快照（规格 §4）。

    用于中断恢复。

    Args:
        base_path: var/ 目录的根路径

    Returns:
        (WaveStructuralSnapshot, last_bar_dt) 或 None（如果没有快照）
    """
    current_json_path = base_path / "current.json"

    # 检查 current.json 是否存在
    if not current_json_path.exists():
        return None

    # 读取指针
    with open(current_json_path, "r", encoding="utf-8") as f:
        pointer_data = json.load(f)

    snapshot_path = Path(pointer_data["last_snapshot_path"])
    last_bar_dt = pointer_data["last_bar_dt"]

    # 检查快照文件是否存在
    if not snapshot_path.exists():
        return None

    # 读取最后一行（最新快照）
    with open(snapshot_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return None
        last_line = lines[-1].strip()

    # 反序列化
    snapshot = deserialize_snapshot(last_line)

    return (snapshot, last_bar_dt)


def should_resume_from(last_bar_dt: str, new_bar_dt: str) -> bool:
    """
    判断是否应该从上次中断处恢复（规格 §4）。

    Args:
        last_bar_dt: 上次快照的 bar_dt
        new_bar_dt: 当前要处理的 bar_dt

    Returns:
        True 表示应该跳过（已处理），False 表示需要处理
    """
    # 简单字符串比较（假设 bar_dt 格式一致，如 "2024-01-01"）
    return new_bar_dt <= last_bar_dt
