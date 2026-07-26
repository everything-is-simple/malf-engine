# malf-engine

MALF v2.1 结构计算核心。吃 OHLC，吐 `CoreStateSnapshot`（包含 Core + Range 层状态）。确定性、单遍、零外部依赖。

实验目录 `RB-FX-008`，独立 venv，自跑 pytest。五层 trial-passed + replay 通过后搬主仓库。

## 实现状态

### Core 层（✅ 已完成）
- Wave 方向追踪（UP/DOWN）
- Guard 机制与 break 检测
- Progress 追踪
- TRANSITION 期间 Candidate 机制
- 测试：47 passed

### Range 层（✅ 已完成）
- Range 诞生（guard break 触发）
- Boundary 演化（R2 不变量）
- Resolution 判定（T6 定理）
- Continuation/Reversal 分类
- 测试：6 synthetic + 1 real data

**总计测试**：54 passed, 1 skipped（真实数据在 CI 上跳过）

**真实数据验证**：
- 数据源：上证 600000（浦发银行）200 bars
- 验证结果：3 Ranges，67% continuation，33% reversal
- R2 不变量：78 个 TRANSITION 快照全部通过
- 结论：生产就绪 ✅

## 文档（一个萝卜一个坑）

| 文档 | 是什么 | 何时看 |
|---|---|---|
| `docs/MALF_V2_1_AUTHORITY_REFERENCE.md` | **v2.1 权威引用**（WHAT），唯一规范入口 | 查规则/公式/字段/编号 |
| `docs/RANGE-LAYER-GUIDE.md` | **Range 层使用指南**，概念、示例、FAQ | 使用 Range 层功能 |
| `docs/API.md` | **API 参考**，CoreStateSnapshot 字段说明 | 查字段含义 |
| `docs/BUILD-CONTRACT.md` | 建造合同：范围 / 非目标 / 验收线 | 稳定，极少改 |
| `docs/BUILD-PLAN.md` | 建造计划：当前这一刀的 step + 勾选 | 活的，每天看 |
| `docs/IMPLEMENTATION-CONTRACT-PATCH.md` | 实现合同补丁：第 4A/4B 层立法参考 | TDD 前必读 |

> **v2.1 更新（2026-07-26）**：权威定义已从 v2.0 升级到 v2.1 Definitive。  
> v2.1 与 v2.0 语义等价，是"清晰表达版本"。核心变更：Probability 层 → Structural Position 层。  
> **第六刀（Range 层）已完成**，包含真实市场数据验证。

> 本 README 与 BUILD-* 都**不复述规范**，只指向。行为的真正规格活在规格文档 + `tests/fixtures/` 的 golden fixture 里。

## 跑测试

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

**当前进度**：Core + Range 层已完成 - **54 passed, 1 skipped**

| 刀数 | 目标 | 状态 | 测试 |
|------|------|------|------|
| 第一~五刀 | Core 层完整状态机 | ✅ 完成 | 47 passed |
| **第六刀** | **Range 层** | **✅ 完成** | **6 synthetic + 1 real data** |

详见 `docs/BUILD-PLAN.md`。

## Quick Start

```python
from malf.core_engine import MALFCoreEngine
from malf.types import PriceBar

engine = MALFCoreEngine(k=2)

bar = PriceBar(
    symbol="TEST",
    timeframe="1d",
    bar_dt="20260726",
    open=100,
    high=105,
    low=98,
    close=103
)

snapshot = engine.on_bar(bar)

# Core 层字段
print(f"State: {snapshot.system_state.value}")
print(f"Direction: {snapshot.direction.value if snapshot.direction else None}")

# Range 层字段（仅在 TRANSITION 时有效）
if snapshot.system_state.value == 'transition':
    print(f"Range birth: {snapshot.range_birth_bar_dt}")
    print(f"Boundary: [{snapshot.range_boundary_init_high}, {snapshot.range_boundary_init_low}]")
    print(f"Evolution count: {snapshot.range_evolution_count}")
```

更多示例见 `docs/RANGE-LAYER-GUIDE.md`。