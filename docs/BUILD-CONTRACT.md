# malf-engine 建造合同

> **薄而稳。** 本文只定「造什么范围、不造什么、什么算做完」。
> **规则、公式、字段、编号一律不复述——指向规格。** 复述就是制造第二个真相源（洞）。
>
> 规格权威：`../../../asteria-riskbench/new-docs/MALF_v2.0_引擎规格_定稿.md`（相对本仓库）
> 讲解（WHY）：同目录 `malf2.0-引擎.md`

## 1. 造什么（范围）

一个 Python 包，吃 OHLC（PriceBar 序列），吐 `WaveProbabilitySnapshot`。五层：
Core → Range → Lifespan → Probability → Service。全部行为定义在规格，本包只实现。

- 领域核心**零外部依赖**（Python 3.10+ 标准库）。理由见 pyproject.toml 注释与规格 §7.4。
- 实验目录 `RB-FX-008`，独立 venv，自跑 pytest，不污染主仓库。五层全部 trial-passed + replay 通过后，再搬主仓库 `src/riskbench/malf/`。

## 2. 不造什么（非目标）

- ❌ 不输出 `strength_score / setup / accept-reject / 仓位 / 盈亏`（规格 §8.1，MALF 永不输出）。
- ❌ 不做数据适配、Viewer、门禁、备份——那些是 RiskBench 产品层，不是引擎。
- ❌ 引擎内不引 Pydantic / FastAPI / numpy / pandas。
- ❌ 不预先把五层的详细 step 全排出来（见 BUILD-PLAN.md：计划是活的，一层通了再切下一层）。

## 3. 什么算做完（验收线）

引擎「做完」不靠"跑一遍看着对"，靠三条硬线**同时**绿：

1. **8 条 Core 不变量**全部有对应测试且通过（规格 §2.10）。
2. **golden fixture 全过**——每条转换路径一个 fixture，预期输出人肉推导（非待测代码生成）。
3. **replay 确定性通过**（规格 §7 / O8）：相同输入 + 相同版本 ⇒ 逐字节相同的 snapshot 与 lineage_hash。

> replay 不过，引擎不算写完。这是 O8 铁律。

## 4. 挂起项（~~等代码验证后再回补规格~~已闭合）

~~这两条是字段级契约改动，形态要等写 CoreStateSnapshot / state 存储时由代码验证，
**不在写第一行引擎代码前拍死**（否则又走"纸上立法"老路）：~~

- ~~**L4-6 runtime_fingerprint**：Python 版本 + 平台进快照 version 字段。
  待验证：是否进 lineage_hash 计算输入（当前倾向：**记录但不进 hash**，作审计元数据，replay 时单独比对）。~~
- ~~**L4-7 schema_version**：每条 revision / snapshot 带版本号（对应规格 S6 字段永不重命名）。
  待验证：全局一个 vs 每种记录各一个。~~

> ~~挂起 ≠ 遗忘。fixture 跑通、字段形态被代码验证过，回补进规格 §7 定稿。~~

**✅ 已闭合（2026-07-26）**：
- **L4-6** 定稿：`runtime_fingerprint` 记录但不进 lineage_hash（审计元数据），形如 `py3.10.19|win32|CPython`。代码实现见 `src/malf/fingerprint.py`，规格见 §7.6。
- **L4-7** 定稿：`schema_version` 每种 snapshot 类型独立版本号，首版 Core 为 `"malf-core-snapshot-v0"`。代码实现见 `src/malf/types.py::CoreStateSnapshot`，规格见 §7.6。
