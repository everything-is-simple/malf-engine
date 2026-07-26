# malf-engine

MALF v2.1 结构计算核心。吃 OHLC，吐 `WaveStructuralSnapshot`。确定性、单遍、零外部依赖。

实验目录 `RB-FX-008`，独立 venv，自跑 pytest。五层 trial-passed + replay 通过后搬主仓库。

## 文档（一个萝卜一个坑）

| 文档 | 是什么 | 何时看 |
|---|---|---|
| `docs/MALF_V2_1_AUTHORITY_REFERENCE.md` | **v2.1 权威引用**（WHAT），唯一规范入口 | 查规则/公式/字段/编号 |
| `docs/BUILD-CONTRACT.md` | 建造合同：范围 / 非目标 / 验收线 | 稳定，极少改 |
| `docs/BUILD-PLAN.md` | 建造计划：当前这一刀的 step + 勾选 | 活的，每天看 |
| `docs/IMPLEMENTATION-CONTRACT-PATCH.md` | 实现合同补丁：第 4A/4B 层立法参考（第 1-3 层已回写 v2.1） | TDD 前必读 |

> **v2.1 更新（2026-07-26）**：权威定义已从 v2.0 升级到 v2.1 Definitive（DeepSeek 起草/Claude 审核/东西南北中认定）。  
> v2.1 与 v2.0 语义等价，是"清晰表达版本"。核心变更：Probability 层 → Structural Position 层，WaveProbabilitySnapshot → WaveStructuralSnapshot。  
> **当前实现状态：** Core 层已完成（47 passed），基于 v2.0 命名。第六刀（Range 层）开工前将统一重命名为 v2.1 命名。

> 本 README 与 BUILD-* 都**不复述规范**，只指向。行为的真正规格活在规格文档 + `tests/fixtures/` 的 golden fixture 里。

## 跑测试

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

**当前进度**：Core 层五刀已完成 - **47 passed, 1 skipped**（skip 是真实数据冒烟，Windows 上无 TDX 路径）。

| 刀数 | 目标 | 状态 | 测试 |
|------|------|------|------|
| 第一~五刀 | Core 层完整状态机 | ✅ 完成 | 47 passed |
| **第六刀** | **Range 层** | **⏸ 待开始** | **-** |

详见 `docs/BUILD-PLAN.md`。