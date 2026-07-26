# 第六刀 Day 0 任务 - 推 Range Fixture Prompt

你是量化专家，负责 malf-engine 项目的第六刀（Range 层）Day 0 工作。这是一个独立的任务会话。

---

## 项目背景

### 项目信息
- **项目：** malf-engine - MALF（Market Action Logic Framework）量化引擎
- **工作目录：** `I:\asteria-riskbench-components\malf-engine`
- **Python 环境：** `/d/miniconda/py310/python.exe`

### MALF 是什么
MALF 是一个结构化的市场行为分析框架，通过 5 层架构（Core → Range → Lifespan → Structural Position → Service）将价格序列解析为波段（Wave）、震荡区间（Range）等结构对象，并提供统计排名，但永不输出概率或预测。

### 当前进度

**已完成：** 第一到第五刀（Core 层全部完成）+ Day -3/-2/-1 准备工作
- ✅ Core 层：47 passed, 1 skipped（Pivot 检测、初始化、Guard break、Transition 演化、Replay 确定性）
- ✅ Day -3：创建实施指南 `docs/T6-RANGE-IMPLEMENTATION-GUIDE.md`（34 KB）
- ✅ Day -2：补充代码版本说明（4 个核心模块 docstring 已更新）
- ✅ Day -1：类型名重命名 + Range 数据结构补充 + version.py 创建

**进行中：** 第六刀 Day 0（Range 层 Fixture 推导）
- ⏸ **Day 0（当前任务）：人肉推导 6 个 Range fixture 预期输出**
- ⏸ Day 1-N：TDD 实现 Range 层

---

## 权威规格

### MALF v2.1 Definitive（2026-07-26 发布）
- **位置：** `I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`
- **核心文档：** `MALF_01_Core_v2_1-deepseek-20260726.md`（Core 层）
- **Range 文档：** `MALF_02_Range_v2_1-deepseek-20260726.md`（Range 层，**本次任务核心参考**）
- **起草者：** DeepSeek，审核者：Claude (Anthropic)

### v2.1 Range 层关键概念（必读）

#### 1. Range 是什么（§1-§2）
- **定义：** transition 的升格版本，是一等公民结构对象
- **诞生：** guard break 时诞生，同时 transition 消亡
- **边界：** 继承 transition 的 boundary_high/low 作为初始边界

#### 2. 两层边界模型（§3，核心设计）

**问题：** 为什么需要两层边界？
- **Core 层需要稳定边界** 进行 resolution 判定（T6 定理）
- **Range 层需要演化边界** 进行统计（R2 不变量）

**实现：**
```
boundary_init_high/low  # 从 transition 冻结，永不改变，Core 层专用
boundary_now_high/low   # 基于 init 演化，逐 pivot 扩展，Range 层专用
```

**使用场景对照表（§3）：**
| 使用场景 | 使用边界 | 理由 |
|---------|---------|------|
| T6 resolution 判定 | init | 状态机稳定性 |
| Resolution distance 计算 | init | 与判定一致 |
| Range 统计（width, evolution_count） | now | 反映真实震荡 |

**警告：** 混用 init/now 会导致状态机不稳定或统计失真。

#### 3. Resolution 判定（§4-§5，T6 定理）

**T6 定理（Range Resolution）：**
```
Range 在以下情况 resolve：
1. 出现新 pivot，其极值价格突破 boundary_init
2. 突破方向决定新 wave 方向和 resolution_type
```

**判定规则：**
```python
# 上突破（new UP wave）
if new_pivot.type == H and new_pivot.price > boundary_init_high:
    resolution_type = REVERSAL if break_direction == DOWN else CONTINUATION
    new_wave_direction = UP

# 下突破（new DOWN wave）
if new_pivot.type == L and new_pivot.price < boundary_init_low:
    resolution_type = REVERSAL if break_direction == UP else CONTINUATION
    new_wave_direction = DOWN
```

**resolution_distance 计算（§5）：**
```python
# 有符号整数，表示突破的距离和方向
if new_wave_direction == UP:
    resolution_distance = new_pivot.price - boundary_init_high  # 正数
elif new_wave_direction == DOWN:
    resolution_distance = new_pivot.price - boundary_init_low   # 负数
```

#### 4. Continuation vs Reversal 命名陷阱（§6，关键警告）

**错误理解：** 相对于**旧 wave 方向**
- UP wave → 下突破 = reversal ❌
- UP wave → 上突破 = continuation ❌

**正确理解：** 相对于 **break 方向**（与旧 wave 方向相反）

**例子：**
```
UP wave 向下 break（break_direction = DOWN）：
  → 下突破 = continuation（延续 break 的下行）
  → 上突破 = reversal（反转 break 的下行）

DOWN wave 向上 break（break_direction = UP）：
  → 上突破 = continuation（延续 break 的上行）
  → 下突破 = reversal（反转 break 的上行）
```

#### 5. Boundary 演化（§3，R2 不变量）

**R2 不变量：**
```
Range alive 期间，boundary_now 只能单调扩展：
- boundary_now_high 只能 ≥ 之前的值
- boundary_now_low 只能 ≤ 之前的值
- evolution_count 记录演化次数
```

**演化规则：**
```python
# Range alive 期间，每根 bar 的已确认 pivot 可能触发演化
if pivot.type == H and pivot.price > boundary_now_high:
    boundary_now_high = pivot.price
    evolution_count += 1

if pivot.type == L and pivot.price < boundary_now_low:
    boundary_now_low = pivot.price
    evolution_count += 1
```

---

## Day 0 任务：推 Range Fixture 预期输出

### 任务目标
人肉推导 6 个 Range fixture 的完整预期输出，为 TDD 实现提供 golden truth。

### 为什么需要人肉推导
- **TDD 精神：** fixture 必须独立于实现，不能用待测代码生成
- **复杂度：** Range 涉及 Core 状态机 + 两层边界 + resolution 判定，纯靠直觉易错
- **工具辅助：** 使用 debug 脚本验证 Core 层状态，但 Range 层输出仍需人工推导

### Fixture 覆盖场景

需要推导以下 6 个 fixture（按优先级排序）：

#### Fixture 1：R1 - Continuation Range（下 break → 下突破）
- **场景：** UP wave → 下 break → Range alive → 下突破
- **覆盖：** T6 resolution 判定、continuation 分类、负数 resolution_distance
- **优先级：** P0（最典型场景）

#### Fixture 2：R2 - Reversal Range（下 break → 上突破）
- **场景：** UP wave → 下 break → Range alive → 上突破
- **覆盖：** reversal 分类、正数 resolution_distance、命名陷阱
- **优先级：** P0（验证命名陷阱理解）

#### Fixture 3：R3 - Continuation Range（上 break → 上突破）
- **场景：** DOWN wave → 上 break → Range alive → 上突破
- **覆盖：** 对称性验证（与 R1 对称）
- **优先级：** P0（对称实现验证）

#### Fixture 4：R4 - Reversal Range（上 break → 下突破）
- **场景：** DOWN wave → 上 break → Range alive → 下突破
- **覆盖：** 对称性验证（与 R2 对称）
- **优先级：** P0（对称实现验证）

#### Fixture 5：R5 - Boundary Evolution（多次演化）
- **场景：** Range alive 期间，boundary_now 多次扩展
- **覆盖：** R2 不变量、evolution_count、boundary init/now 分离
- **优先级：** P1（验证演化逻辑）

#### Fixture 6：R6 - Long-lived Range（未 resolve）
- **场景：** Range 诞生后长期 alive，不触发 resolution
- **覆盖：** 边界情况、alive 状态持久性
- **优先级：** P2（边界验证）

### Fixture 设计铁律（来自前五刀经验）

#### 铁律 1：窗口填充必须充足
- **规则：** k=2 分形 pivot 需要左右各 k 根 bars
- **要求：** 序列开头必须有 >= k 根窗口填充 bars
- **检查：** 首个 pivot 的 extreme_bar 索引 >= k
- **陷阱：** 窗口填充 bars 不应触发意外 pivot（价格远离目标区间）

#### 铁律 2：Pivot 确认的严格不等式
- **规则（v2.1 Core §2.4）：**
  - L pivot: 右侧 k 根的 **low 严格 > pivot.low**（不是 `>=`）
  - H pivot: 右侧 k 根的 **high 严格 < pivot.high**（不是 `<=`）
- **陷阱：** 边界相等会导致 pivot 不确认，难以发现
- **检查：** 逐根验证严格不等式

#### 铁律 3：人肉推导必须工具辅助
- **禁止：** 仅凭直觉或手算推导 fixture
- **强制：** 使用 debug 脚本验证 Core 层状态（pivots、wave、transition）
- **流程：**
  1. 设计 bar 序列（Excel/手绘折线图）
  2. 标注每个候选 pivot 的左右 k 根窗口
  3. 逐一验证严格不等式
  4. 创建 debug 脚本，打印 Core 层状态
  5. 基于 Core 状态，人肉推导 Range 状态
  6. 对比人肉推导 vs 脚本输出（Core 部分）

---

## 执行步骤

### Step 1：创建 debug_t6.py 工具脚本

创建 `debug_t6.py`，用于验证 Core 层状态和辅助推导 Range 层状态。

**脚本功能：**
```python
# 1. 加载 bar 序列
# 2. 运行 Core 引擎，逐 bar 输出快照
# 3. 识别关键时刻：
#    - Pivot 确认时刻
#    - Wave 初始化时刻
#    - Guard break 时刻（Range 诞生）
#    - Transition boundary 演化时刻
# 4. 打印 Core 层完整状态供人工推导 Range 层状态
```

**输出格式示例：**
```
Bar 0: symbol=TEST, timeframe=1d, bar_dt=2020-01-01, OHLC=(100,105,95,102)
  Pivots detected: []
  System state: uninitialized

Bar 5: symbol=TEST, timeframe=1d, bar_dt=2020-01-06, OHLC=(...)
  Pivots detected: [L(price=90, extreme_bar_dt=2020-01-03, confirm_bar_dt=2020-01-06)]
  System state: uninitialized → up_alive (INITIALIZATION)
  Wave direction: UP
  Guard: price=95, extreme=2020-01-04, confirm=2020-01-06

Bar 12: symbol=TEST, timeframe=1d, bar_dt=2020-01-13, OHLC=(...)
  Pivots detected: [H(price=110, extreme_bar_dt=2020-01-11, confirm_bar_dt=2020-01-13)]
  System state: up_alive
  Guard updated: 110 (replaces 95)

Bar 18: symbol=TEST, timeframe=1d, bar_dt=2020-01-19, OHLC=(...)
  Pivots detected: []
  System state: up_alive → transition (GUARD BREAK)
  Break direction: DOWN (bar.low=105 < guard=110)
  Transition boundary: high=110, low=90
  >>> RANGE BORN HERE <<<
  Range birth_bar_dt: 2020-01-19
  boundary_init: (110, 90)
  boundary_now: (110, 90)
  break_direction: DOWN
  old_wave_direction: UP

Bar 25: symbol=TEST, timeframe=1d, bar_dt=2020-01-26, OHLC=(...)
  Pivots detected: [L(price=85, extreme_bar_dt=2020-01-24, confirm_bar_dt=2020-01-26)]
  System state: transition → down_alive (NEW WAVE CONFIRMED)
  New wave direction: DOWN
  >>> RANGE RESOLVED HERE <<<
  Resolution type: CONTINUATION (break_direction=DOWN, new_wave=DOWN)
  Resolution distance: 85 - 90 = -5
  Resolution bar_dt: 2020-01-26
```

**创建位置：** `debug_t6.py`（项目根目录）

### Step 2：设计 Fixture 1（R1 - Continuation Range）

**目标：** UP wave → 下 break → Range alive → 下突破

**设计要求：**
- 至少 2 根窗口填充 bars（bar 0-1）
- UP wave 初始化（需要 L0, H1, L2 三个 pivot，其中 L2 > L0）
- Guard break 向下（bar.low < current_guard）
- Range alive 期间至少 3-5 根 bars
- 下突破（L pivot.price < boundary_init_low）

**推导步骤：**
1. 画 bar 序列折线图（标注 high/low）
2. 标注每个 pivot 的窗口和确认时刻
3. 标注 guard break 时刻（Range 诞生）
4. 标注 resolution 时刻（Range resolve）
5. 运行 debug_t6.py，对比人肉推导 vs 脚本输出
6. 编写完整 fixture JSON

**预期输出结构：**
```json
{
  "fixture_id": "R1_continuation_down_break_down_resolve",
  "description": "UP wave → 下 break → Range alive → 下突破 (continuation)",
  "bars": [...],  // PriceBar 序列
  "expected_range_snapshots": [
    {
      "bar_dt": "2020-01-19",  // Range 诞生
      "range_state": "alive",
      "birth_bar_dt": "2020-01-19",
      "boundary_init_high": 110,
      "boundary_init_low": 90,
      "boundary_now_high": 110,
      "boundary_now_low": 90,
      "evolution_count": 0,
      "break_direction": "down",
      "old_wave_direction": "up",
      "resolution_bar_dt": null,
      "resolution_type": null,
      "resolution_distance": null
    },
    // ... Range alive 期间的快照 ...
    {
      "bar_dt": "2020-01-26",  // Range resolve
      "range_state": "resolved",
      "birth_bar_dt": "2020-01-19",
      "boundary_init_high": 110,
      "boundary_init_low": 90,
      "boundary_now_high": 115,  // 可能演化
      "boundary_now_low": 85,    // 突破触发点
      "evolution_count": 2,
      "break_direction": "down",
      "old_wave_direction": "up",
      "resolution_bar_dt": "2020-01-26",
      "resolution_type": "continuation",
      "resolution_distance": -5,  // 85 - 90 = -5
      "confirmation_pivot_extreme_price": 85,
      "confirmation_pivot_extreme_bar_dt": "2020-01-24",
      "confirmation_pivot_confirm_bar_dt": "2020-01-26",
      "new_wave_direction": "down"
    }
  ]
}
```

### Step 3：重复 Step 2，推导 Fixture 2-6

对每个 fixture：
1. 设计 bar 序列（覆盖目标场景）
2. 画折线图，标注关键时刻
3. 运行 debug_t6.py 验证 Core 层状态
4. 人肉推导 Range 层状态
5. 编写完整 fixture JSON
6. 自检 JSON 格式（使用 `python -m json.tool` 验证）

**优先级：**
- **P0：** R1, R2, R3, R4（4 个基础 resolution 场景）
- **P1：** R5（boundary 演化）
- **P2：** R6（long-lived alive）

### Step 4：创建 Fixture 文件

将所有 fixture 保存到：
```
tests/fixtures/range/
  R1_continuation_down_break_down_resolve.json
  R2_reversal_down_break_up_resolve.json
  R3_continuation_up_break_up_resolve.json
  R4_reversal_up_break_down_resolve.json
  R5_boundary_evolution.json
  R6_long_lived_alive.json
```

**JSON 格式要求：**
- 4 空格缩进
- 所有字符串使用双引号
- 价格为整数（int_fixed）
- 时间戳格式：`YYYY-MM-DD`（简化版）或 `YYYY-MM-DDTHH:MM:SS`

### Step 5：自检清单

推导完成后，检查以下内容：

**窗口与不等式：**
- [ ] 每个 fixture 开头至少有 k 根窗口填充 bars
- [ ] 首个 pivot 的 extreme_bar 索引 >= k
- [ ] 所有 L pivot 右侧 k 根：low 严格 > pivot.low
- [ ] 所有 H pivot 右侧 k 根：high 严格 < pivot.high
- [ ] 窗口填充 bars 不触发意外 pivot

**Range 语义：**
- [ ] boundary_init 从 transition boundary 继承，**永不改变**
- [ ] boundary_now 基于 init 初始化，单调扩展（R2 不变量）
- [ ] evolution_count 正确记录演化次数
- [ ] break_direction 与 old_wave_direction 正确对应（相反）
- [ ] resolution_type 基于 break_direction 判定（不是 old_wave_direction）
- [ ] resolution_distance 符号正确（上突破为正，下突破为负）
- [ ] resolution_distance 基于 boundary_init 计算（不是 boundary_now）

**对称性：**
- [ ] R1（down break → down resolve）vs R3（up break → up resolve）：完全对称
- [ ] R2（down break → up resolve）vs R4（up break → down resolve）：完全对称
- [ ] UP/DOWN、H/L、>/< 正确反向

**工具验证：**
- [ ] debug_t6.py 运行无崩溃
- [ ] Core 层状态与人肉推导一致（pivots、wave、transition）
- [ ] JSON 格式验证通过（`python -m json.tool fixture.json`）

---

## 完成标志

Day 0 完成 = 以下全部达标：

1. ✅ 创建 debug_t6.py 工具脚本
2. ✅ 推导 P0 fixture（R1-R4）完成，含完整预期输出
3. ✅ 推导 P1 fixture（R5）完成（可选：P2 R6）
4. ✅ 所有 fixture 通过自检清单
5. ✅ 创建完成报告 `docs/T6-DAY-0-COMPLETION.md`

---

## 完成报告模板

任务完成后，创建 `docs/T6-DAY-0-COMPLETION.md`：

```markdown
# 第六刀 Day 0 完成报告

**日期：** 2026-07-26  
**任务：** 推导 Range Fixture 预期输出  
**状态：** ✅ 已完成

## 完成的 Fixture

### ✅ P0 Fixture（4 个基础场景）

#### R1: Continuation Range（下 break → 下突破）
- 文件：`tests/fixtures/range/R1_continuation_down_break_down_resolve.json`
- Bar 数量：X 根（含 k 根窗口填充）
- 关键时刻：
  - Wave 初始化：bar Y
  - Guard break（Range 诞生）：bar Z
  - Range resolve：bar W
- Resolution type: continuation
- Resolution distance: -N（负数）

#### R2-R4：[类似格式]

### ✅ P1 Fixture（演化场景）

#### R5: Boundary Evolution
- [类似格式]

### ⏸ P2 Fixture（可选）

#### R6: Long-lived Range
- 状态：未推导 / 已推导

## 工具脚本

### debug_t6.py
- 功能：验证 Core 层状态，辅助推导 Range 层状态
- 输出：逐 bar 打印 pivots、system_state、transition、Range 关键时刻

## 自检结果

- [x] 窗口填充 >= k
- [x] 严格不等式验证通过
- [x] boundary_init 永不改变
- [x] boundary_now 单调扩展
- [x] resolution_type 基于 break_direction
- [x] resolution_distance 符号正确
- [x] 对称性验证通过
- [x] JSON 格式验证通过

## 遇到的问题与解决

### 问题 1：[描述]
- **解决：** [方案]

### 问题 2：[描述]
- **解决：** [方案]

## 下一步

Day 1 任务：
- S6-1：创建 Range 层测试骨架
- S6-2：实现 Range 诞生逻辑（guard break → Range）
- S6-3：实现 boundary 演化逻辑（R2 不变量）
- S6-4：实现 resolution 判定逻辑（T6 定理）
- S6-5：端到端测试（6 个 fixture 全过）

---

**Day 0 完成。准备进入 Day 1（TDD 实现）。**
```

---

## 参考文档

### 项目文档
- **实施指南：** `docs/T6-RANGE-IMPLEMENTATION-GUIDE.md`（Day -3 创建，34 KB）
- **建造计划：** `docs/BUILD-PLAN.md`（第六刀章节）
- **建造合同：** `docs/BUILD-CONTRACT.md`（Fixture 设计铁律）
- **Day -1 完成报告：** `docs/T6-DAY-MINUS-1-COMPLETION.md`

### 规格文档
- **v2.1 Core：** `I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\MALF_01_Core_v2_1-deepseek-20260726.md`
- **v2.1 Range：** `I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\MALF_02_Range_v2_1-deepseek-20260726.md`

### 编号体系
- **D1-D18：** 定义（Definitions）
- **T1-T10：** 定理（Theorems）
- **O1-O8：** 操作边界（Operational Boundaries）
- **R1-R5：** Range 不变量（Range Invariants）

---

## 你的任务

执行 Day 0 工作，推导 6 个 Range fixture 的完整预期输出：

1. 创建 debug_t6.py 工具脚本
2. 推导 P0 fixture（R1-R4）
3. 推导 P1 fixture（R5）
4. 自检所有 fixture
5. 创建完成报告

**预计工作量：** 2-3 小时（人肉推导 + 工具验证）

**开始执行。**
