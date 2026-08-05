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

# RiskBench 对外 Service §5 版本合同。
# 注意：adapter/price_domain 使用主仓 AGENTS.md §6 已批准的 raw_none ETF 变体；
# 其余层版本使用 MALF v2.1 权威版本。内部实现版本和 schema 不属于该七键合同。
SERVICE_PIVOT_RULE_VERSION = "fractal_k2_v1.0"
SERVICE_PRICE_DOMAIN_VERSION = "source_integer_fixed_point-v0.1"
SERVICE_ADAPTER_VERSION = "malf-v2.0-etf-tick-v0.1"
SERVICE_CORE_VERSION = "v2.1"
SERVICE_RANGE_VERSION = "v2.1"
SERVICE_LIFESPAN_VERSION = "v2.1"
SERVICE_STRUCTURAL_POSITION_VERSION = "v2.1"


def service_rule_versions() -> dict[str, str]:
    """返回 RiskBench 发布快照使用的完整七键版本合同。"""
    return {
        "pivot_rule": SERVICE_PIVOT_RULE_VERSION,
        "price_domain": SERVICE_PRICE_DOMAIN_VERSION,
        "adapter": SERVICE_ADAPTER_VERSION,
        "core_version": SERVICE_CORE_VERSION,
        "range_version": SERVICE_RANGE_VERSION,
        "lifespan_version": SERVICE_LIFESPAN_VERSION,
        "structural_position_version": SERVICE_STRUCTURAL_POSITION_VERSION,
    }


# Schema 版本（快照数据结构版本）
CORE_SNAPSHOT_SCHEMA_VERSION = "malf-core-snapshot-v0"
RANGE_SNAPSHOT_SCHEMA_VERSION = "malf-range-snapshot-v0"
