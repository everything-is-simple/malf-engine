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

---

## 5. 经验教训（第一刀、第二刀累积）

### 5.1 Fixture 设计铁律

#### 铁律 1：窗口填充必须充足
**来源**：第二刀 S2-1，L0 检测失败（3 次调试才修正）

**问题**：k=2 分形 pivot 需要**左右各 k 根 bars**。将 pivot 放在序列开头（bar 0）会导致左侧窗口不足，无法确认为 pivot。

**解决**：
- **强制**在序列开头添加至少 k 根窗口填充 bars
- 首个有效 pivot 应从 bar k 开始（k=2 时，首个 pivot 在 bar 2 或之后）
- 窗口填充 bars 的 OHLC 设计应远离目标 pivot 价格区间，避免产生计划外 pivot

**检查清单（推 fixture 时必查）**：
- [ ] 首个 pivot 的 extreme_bar 索引 >= k
- [ ] 序列开头有 >= k 根窗口填充 bars
- [ ] 窗口填充 bars 不触发意外 pivot（用 debug 脚本验证）

#### 铁律 2：Pivot 确认的严格不等式
**来源**：第二刀调试，bar6.low=94 < L2=95 违反确认规则

**规则**（spec §2.4）：
- L pivot: 右侧 k 根的 **low 严格 > pivot.low**（不是 `>=`）
- H pivot: 右侧 k 根的 **high 严格 < pivot.high**（不是 `<=`）

**陷阱**：边界相等（price == pivot.price）会导致 pivot 不确认，但不报错，难以发现。

**检查清单（推 fixture 时必查）**：
- [ ] L pivot 右侧 k 根：所有 low 严格大于 pivot.low（逐根检查）
- [ ] H pivot 右侧 k 根：所有 high 严格小于 pivot.high（逐根检查）
- [ ] 不存在边界相等情况（用 debug 脚本验证）

#### 铁律 3：人肉推导必须工具辅助
**来源**：第二刀 3 次调试迭代

**禁止**：仅凭直觉或手算推导 fixture，不用工具验证。

**强制流程**：
1. 画 bar 序列的 high/low 折线图（Excel / Python 可视化）
2. 标注每个候选 pivot 的左右 k 根窗口
3. 逐一验证严格不等式（手算 + 脚本验证）
4. 创建 `debug_*.py` 脚本，打印 `detected_pivots` vs `expected_pivots`
5. 人肉推导与脚本结果**必须一致**才定稿

**工具模板**（见 `debug_t2.py`）：
```python
# 加载 fixture，喂给 detect_pivots，对比实际 vs 预期
pivots = detect_pivots(bars, k=2)
print("Detected:", pivots)
print("Expected:", fixture["expected_pivots"])
```

---

### 5.2 TDD 流程铁律

#### 铁律 4：先推 fixture，再写实现
**来源**：第一刀和第二刀的成功模式

**禁止**：
- 没有 golden fixture 就开始写实现
- 用待测代码生成预期输出（违背 TDD 精神）
- 边写实现边调整 fixture（fixture 必须独立于实现）

**强制流程**（每一刀）：
1. **S*-1**: 人肉推导 fixture 预期输出（含逐根 snapshot），工具辅助验证
2. **S*-2**: 定稿存 JSON，通过 JSON 格式自检
3. **S*-3**: 写测试加载 fixture，先 skip 或预期 RED
4. **S*-4**: 实现代码，追求 GREEN
5. **S*-5**: 端到端测试，全量回归（N passed, M skipped）

**检查清单（开工前必查）**：
- [ ] Fixture 先于实现（S*-1, S*-2 在 S*-4 之前）
- [ ] Fixture 独立于实现（人肉推导，不依赖代码）
- [ ] 测试先于实现（RED → GREEN → REFACTOR）

#### 铁律 5：对称实现优先
**来源**：第二刀 down 方向完全对称 up 方向，实现速度快、bug 少

**策略**：
- 识别对称性：up/down、H/L、>/< 、first/last
- 复用结构：相同的函数签名、相同的数据流、相同的 docstring 模板
- 测试对称：golden fixture 模式相同，只是数据反向

**反例（禁止）**：
- up 用一套函数，down 用另一套（代码重复）
- up 的测试覆盖 10 个场景，down 只覆盖 3 个（不对称）

**检查清单（实现时必查）**：
- [ ] 对称分支的代码结构一致（if/else 长度相近）
- [ ] 对称分支的测试覆盖相同（相同数量的单元测试）
- [ ] 不等号、pivot 类型、方向标记正确反向

---

### 5.3 真实数据验证铁律

#### 铁律 6：每刀必有真实数据冒烟
**来源**：第一刀 S7 暴露 down 方向未实现，第二刀 S2-6 验证 down 已实现

**目标**：暴露 golden fixture 没预料到的真实世界问题（边界情况、数据特性）

**要求**：
- 使用真实 A 股数据（浦发银行 sh600000 前 200 根日线，或等效标的）
- **不断言具体输出**（golden fixture 负责正确性）
- 只验证**不崩溃、不抛未预期异常**
- 记录 **pivot 分布**（H/L 数量）、**初始化结果**（up/down/未初始化）

**检查清单（每刀必做）**：
- [ ] 更新 `test_real_data_smoke.py`，添加本刀的验证点
- [ ] 记录可能触发的边界情况（注释说明）
- [ ] 区分不同刀的验证范围（docstring 更新）
- [ ] Windows 环境 SKIPPED 是正常的（TDX 路径不同）

---

### 5.4 文档回补铁律

#### 铁律 7：每刀结束必回补三份文档
**来源**：第二刀 S2-7

**三份文档**：
1. **BUILD-PLAN.md**：标记完成的 step，更新「已发现待处理」
2. **模块 docstring**：更新范围声明（已实现 vs 未实现 vs NotImplementedError）
3. **DAILY-LOG-YYYY-MM-DD.md**：完整记录调试过程、技术决策、遗留问题

**检查清单（每刀结束必查）**：
- [ ] BUILD-PLAN.md 当前这一刀的所有 step 勾选完成
- [ ] 「已发现待处理」移除已实现的项，添加新发现的问题
- [ ] 相关模块的 docstring 与实际代码状态一致
- [ ] DAILY-LOG 记录完整（问题描述+解决过程+经验教训+遗留问题）

---

### 5.5 行动计划模板（第三刀起强制遵循）

每一刀的标准流程（参考第一刀 S0-S8 和第二刀 S2-1~S2-7）：

```markdown
## 第 N 刀：<功能名称>

**目标**：<一句话描述目标状态转换或功能>
**覆盖**（规格 §X）：<涉及的规格章节、定义编号、不变量编号>

### Step 清单

- [ ] **S*-1 推 fixture 预期输出**：人肉推导，复核窗口/时序/不变量。
  工具辅助：画折线图、标窗口、debug 脚本验证 pivots
- [ ] S*-2 预期输出定稿存 JSON（X 根 bar，含 k 根窗口填充，JSON 自检通过）
- [ ] S*-3 写单元测试（验证关键逻辑点，先 RED）
- [ ] S*-4 实现功能（追求对称性、复用现有结构、显式 NotImplementedError）
- [ ] S*-5 端到端测试（逐 bar 喂入，全等比对，追求 GREEN）
- [ ] S*-6 真实数据冒烟（sh600000 前 200 根，记录 pivot 分布、状态转换）
- [ ] S*-7 回补文档（BUILD-PLAN.md + 模块 docstring + DAILY-LOG）

### 完成标志

第 N 刀 done = S*-5 绿 + S*-6 无意外崩溃 + S*-7 文档更新。达标后，才排第 N+1 刀。
```

**禁止跳步**：每个 step 必须按顺序完成，不得跳过 S*-6 或 S*-7。
