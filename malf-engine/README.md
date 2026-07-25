# malf-engine

MALF v2.0 结构计算核心。吃 OHLC，吐 `WaveProbabilitySnapshot`。确定性、单遍、零外部依赖。

实验目录 `RB-FX-008`，独立 venv，自跑 pytest。五层 trial-passed + replay 通过后搬主仓库。

## 文档（一个萝卜一个坑）

| 文档 | 是什么 | 何时看 |
|---|---|---|
| `../../asteria-riskbench/new-docs/MALF_v2.0_引擎规格_定稿.md` | **规范**（WHAT），唯一权威 | 查规则/公式/字段/编号 |
| `../../asteria-riskbench/new-docs/malf2.0-引擎.md` | 讲解（WHY） | 想懂设计理由 |
| `docs/BUILD-CONTRACT.md` | 建造合同：范围 / 非目标 / 验收线 | 稳定，极少改 |
| `docs/BUILD-PLAN.md` | 建造计划：当前这一刀的 step + 勾选 | 活的，每天看 |

> 本 README 与 BUILD-* 都**不复述规范**，只指向。行为的真正规格活在规格文档 + `tests/fixtures/` 的 golden fixture 里。

## 跑测试

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

现在只有空壳冒烟测试会 PASS，第一刀 fixture 测试标 skip（见 BUILD-PLAN.md S1）。
