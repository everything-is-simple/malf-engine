"""MALF 版本常量定义。

本文件集中管理所有层的规则版本号，便于追溯和维护。

版本号格式：
- Core 层：core-v{major}.{minor}.{patch}
- Range 层：v{major}.{minor}.{patch}（对齐 MALF 规格版本）
- Pivot 检测：{algorithm}-k{k}-v{version}

规格对照：
- MALF v2.1 Definitive (deepseek-20260726)
- 位置：I:\\asteria-riskbench-Definitive-validated\\MALF_Definitive_v2_1-deepseek-20260726\\
"""

# Core 层版本（对应 v2.1 Core）
CORE_RULE_VERSION = "core-v0.0.1"
PIVOT_DETECTION_RULE_VERSION = "fractal-k2-v1"
PRICE_POLICY = "int_fixed"

# Range 层版本（对应 v2.1 Range）
RANGE_RULE_VERSION = "v2.1.0"

# Lifespan 层版本（未来第七刀）
# LIFESPAN_RULE_VERSION = "v2.1.0"

# Structural Position 层版本（未来第八刀）
# STRUCTURAL_POSITION_RULE_VERSION = "v2.1.0"

# Schema 版本（快照数据结构版本）
CORE_SNAPSHOT_SCHEMA_VERSION = "malf-core-snapshot-v0"
RANGE_SNAPSHOT_SCHEMA_VERSION = "malf-range-snapshot-v0"
