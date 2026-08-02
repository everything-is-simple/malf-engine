# malf-engine

MALF v2.1 结构计算核心。吃 OHLC，吐 `CoreStateSnapshot`（包含 Core + Range 层状态）。确定性、单遍、零外部依赖。

实验目录 `RB-FX-008`，独立 venv，自跑 pytest。五层 trial-passed + replay 通过后搬主仓库。

## 实现状态

### Core 层（✅ 已完成）
- Wave 方向追踪（UP/DOWN）
- Guard 机制与 break 检测
- Progress 追踪
- TRANSITION 期间 Candidate 机制
- **C-07 规则**：早期 pivot 替换（H0/L0/L1/H1）✅
- 测试：47 passed
- ⚠️ **已知问题**（2026-07-27）：2 个 P0 级缺陷待修复

### Range 层（✅ 已完成）
- Range 诞生（guard break 触发）
- Boundary 演化（R2 不变量）
- Resolution 判定（T6 定理）
- Continuation/Reversal 分类
- 测试：6 synthetic + 1 real data

### Lifespan 层（✅ 已完成）
- WaveLifespan 指标计算（7 个指标）
- RangeLifespan 指标计算（6 个指标）
- 双轨 peer_sample + percentile rank
- 测试：77 passed

### Structural Position 层（✅ 已完成）
- P1-P4 四个视图全部实现
- Momentum 计算 + 标签生成
- 测试：12 passed

**总计测试**：89 passed, 2 skipped

**规格合规度**（2026-07-27 检查）：**85%** (基本合规)
- 数据结构：92% ✅
- 算法逻辑：88% ⚠️（2 个 P0 缺陷待修复）
- 不变量覆盖：94% ✅

## 文档（一个萝卜一个坑）

**📍 入口**: [`docs/00-INDEX.md`](docs/00-INDEX.md) - 文档导航（从这里开始）

### 核心文档

| 文档 | 是什么 | 何时看 |
|---|---|---|
| [`docs/00-INDEX.md`](docs/00-INDEX.md) | **文档导航入口** | 不知道看哪个文档时 |
| [`docs/dev/AI-TASK-WORKFLOW.md`](docs/dev/AI-TASK-WORKFLOW.md) | **AI 助手任务执行 SOP**（HOW） | **接到任务第一个看** ⭐ |
| [`docs/dev/BUILD-PLAN.md`](docs/dev/BUILD-PLAN.md) | **建造计划**：当前这一刀的 step + 勾选 | **活的，每天看** |
| [`docs/spec/MALF_V2_1_AUTHORITY_REFERENCE.md`](docs/spec/MALF_V2_1_AUTHORITY_REFERENCE.md) | **v2.1 权威引用**（WHAT） | 查规则/公式/字段/编号 |
| [`docs/spec/BUILD-CONTRACT.md`](docs/spec/BUILD-CONTRACT.md) | 建造合同：范围 / 非目标 / 验收线 | 稳定，极少改 |
| [`docs/spec/IMPLEMENTATION-CONTRACT-PATCH.md`](docs/spec/IMPLEMENTATION-CONTRACT-PATCH.md) | 实现合同补丁：第 4A/4B 层立法参考 | TDD 前必读 |
| [`docs/guide/RANGE-LAYER-GUIDE.md`](docs/guide/RANGE-LAYER-GUIDE.md) | **Range 层使用指南** | 使用 Range 层功能 |
| [`docs/guide/API.md`](docs/guide/API.md) | **API 参考** | 查字段含义 |

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

**当前进度**：14/20 刀完成（70%）- Core + Range + Lifespan + Structural Position 层已完成

**⚠️ 重要提示**（2026-07-27）：规格对照检查发现 2 个 P0 级缺陷，需立即修复后再投入生产使用。详见 `docs/dev/BUILD-PLAN.md`。

| 层级 | 状态 | 测试 | 备注 |
|------|------|------|------|
| Core | ✅ 完成 | 47 passed | ⚠️ 2个P0缺陷待修复 |
| Range | ✅ 完成 | 6 + 1 real | ✅ 真实数据验证通过 |
| Lifespan | ✅ 完成 | 77 passed | ⚠️ 1个P1待核对 |
| Structural Position | ✅ 完成 | 12 passed | ✅ 合规 |
| Service | ⏸ 待做 | - | 预计3-5天 |

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