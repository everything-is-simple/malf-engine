# 第六刀准备 Day -1 任务 - Prompt

你是量化专家，负责 malf-engine 项目的第六刀（Range 层）准备工作。这是一个独立的任务会话。

---

## 项目背景

### 项目信息
- **项目：** malf-engine - MALF（Market Action Logic Framework）量化引擎
- **工作目录：** `I:\asteria-riskbench-components\malf-engine`
- **Python 环境：** `/d/miniconda/py310/python.exe`

### MALF 是什么
MALF 是一个结构化的市场行为分析框架，通过 5 层架构（Core → Range → Lifespan → Structural Position → Service）将价格序列解析为波段（Wave）、震荡区间（Range）等结构对象，并提供统计排名，但永不输出概率或预测。

### 当前进度

**已完成：** 第一到第五刀（Core 层全部完成）
- ✅ 47 个测试通过，1 个跳过（真实数据在 Windows 上 SKIPPED）
- ✅ Core 层实现：Pivot 检测、初始化、Guard break、Transition 演化、Replay 确定性

**进行中：** 第六刀准备阶段（Range 层开工前准备）
- ✅ Day -3 完成：创建实施指南 `docs/T6-RANGE-IMPLEMENTATION-GUIDE.md`（34 KB）+ 更新 `docs/BUILD-PLAN.md`
- ✅ Day -2 完成：补充代码版本说明（4 个核心模块 docstring 已更新）
- ⏸ **Day -1（当前任务）：类型名重命名 + 数据结构补充**
- ⏸ Day 0：开始推 fixture

---

## 权威规格

### MALF v2.1 Definitive（2026-07-26 发布）
- **位置：** `I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`
- **核心文档：** `MALF_01_Core_v2_1-deepseek-20260726.md`（Core 层）
- **Range 文档：** `MALF_02_Range_v2_1-deepseek-20260726.md`（Range 层）
- **起草者：** DeepSeek，审核者：Claude (Anthropic)

### v2.1 与 v2.0 关系
- **语义完全等价**，v2.1 是"清晰表达版本"（不是新版本）
- **主要变更：** 补丁回写、歧义闭合、测试覆盖要求明确
- **命名修正：** Probability 层 → Structural Position 层（**本次 Day -1 需要重命名相关类型**）

---

## Day -1 任务：类型名重命名 + 数据结构补充

### 任务目标
- **P0-1：** 类型名重命名（WaveStructuralSnapshot → WaveStructuralSnapshot）
- **P1-2：** 补充 Range 数据结构到 types.py
- **P2-1：** 创建 version.py（版本常量文件）

### 优先级
- **P0：** 阻塞性，必须在 Day 0 前完成
- **P1：** 重要，建议完成
- **P2：** 可选，但推荐完成

### 预计工作量
- P0-1：15 分钟（全局搜索重命名 + 测试验证）
- P1-2：20 分钟（定义 Range/Oscillation 数据类）
- P2-1：10 分钟（创建版本常量文件）
- **总计：** 45 分钟

---

## 任务一：P0-1 类型名重命名

### 问题描述
MALF v2.1 将"Probability 层"重命名为"Structural Position 层"，以避免"概率"语义误导。当前代码中有一个快照类型名需要同步修正：

- **旧名：** `WaveStructuralSnapshot`（v2.0 遗留）
- **新名：** `WaveStructuralSnapshot`（v2.1 规范）

### 影响范围
虽然 Core 层代码已完成，但未来 Service 层会产出 `WaveStructuralSnapshot`（包含 Core + Range + Lifespan + Structural Position）。当前 `types.py` 的 docstring 已提到这个类型，需要预先重命名以避免混淆。

### 执行步骤

#### Step 1：全局搜索 "WaveProbability"
```bash
cd I:/asteria-riskbench-components/malf-engine
grep -r "WaveProbability" --include="*.py" --include="*.md"
```

#### Step 2：重命名所有出现位置
预期位置：
- `src/malf/types.py` - docstring 注释中
- 可能的其他文档文件

使用 Edit 工具批量替换：
- `WaveStructuralSnapshot` → `WaveStructuralSnapshot`
- `Probability` → `Structural Position`（上下文相关，需要判断）

#### Step 3：验证测试
```bash
cd I:/asteria-riskbench-components/malf-engine
/d/miniconda/py310/python.exe -m pytest -v
```

**预期结果：** 47 passed, 1 skipped（与修改前一致）

---

## 任务二：P1-2 补充 Range 数据结构

### 需要添加的数据类

#### 1. RangeSnapshot（Range 层核心快照）
基于 v2.1 Range §2-§5，包含以下字段：

```python
@dataclass(frozen=True)
class RangeSnapshot:
    """Range 层状态快照（v2.1 Range §2）。
    
    Range 是 transition 的升格版本，有自己的边界、生命周期、分类。
    
    两层边界模型（v2.1 Range §3）：
    - boundary_init: 冻结边界（Core 层使用，用于 resolution 判定）
    - boundary_now: 演化边界（Range 层使用，逐 pivot 扩展）
    
    使用场景对照表：
    - Resolution 判定（T6）：使用 boundary_init
    - Resolution distance 计算：使用 boundary_init
    - Range 统计（width, evolution_count）：使用 boundary_now
    - Range 分类（continuation/reversal）：基于 break_direction
    
    混用 init/now 会导致状态机不稳定或统计失真。
    """
    
    # identity
    symbol: str
    timeframe: str
    bar_dt: str
    range_id: str  # 格式："{symbol}_{timeframe}_R{序号}"
    
    # 生命周期
    range_state: RangeState  # alive / resolved
    birth_bar_dt: str  # Range 诞生时间（guard break 那根 bar）
    resolution_bar_dt: Optional[str] = None  # Resolution 确认时间
    
    # 两层边界（v2.1 Range §3 核心设计）
    boundary_init_high: int  # 初始上边界（冻结，用于 resolution 判定）
    boundary_init_low: int   # 初始下边界（冻结）
    boundary_now_high: int   # 当前上边界（演化，用于统计）
    boundary_now_low: int    # 当前下边界（演化）
    
    # 演化统计
    evolution_count: int = 0  # Boundary 演化次数（R2）
    
    # Break 方向（决定 continuation/reversal 分类）
    break_direction: Direction  # 从哪个方向 break 出来的（UP wave → 下 break，DOWN wave → 上 break）
    old_wave_direction: Direction  # 旧 wave 方向（用于命名陷阱警告）
    
    # Resolution 信息（resolved 时填充）
    resolution_type: Optional[RangeResolutionType] = None  # continuation / reversal
    resolution_distance: Optional[int] = None  # 突破距离（有符号整数，v2.1 Range §5）
    confirmation_pivot_extreme_price: Optional[int] = None  # 触发 resolution 的 pivot 极值价格
    confirmation_pivot_extreme_bar_dt: Optional[str] = None  # 极值时间
    confirmation_pivot_confirm_bar_dt: Optional[str] = None  # 确认时间
    new_wave_direction: Optional[Direction] = None  # 新 wave 方向
    
    # 版本信息
    range_rule_version: str = "v2.1.0"
    schema_version: str = "malf-range-snapshot-v0"
```

#### 2. RangeState（Range 生命周期状态）
```python
class RangeState(str, Enum):
    """Range 生命周期状态（v2.1 Range §4）。"""
    
    ALIVE = "alive"        # Range 活跃中（尚未 resolve）
    RESOLVED = "resolved"  # Range 已解决（new wave 确认）
```

#### 3. RangeResolutionType（Range 分类）
```python
class RangeResolutionType(str, Enum):
    """Range resolution 分类（v2.1 Range §6）。
    
    命名陷阱警告（v2.1 Range §6.2）：
    - continuation: 延续 **break 方向**（不是旧 wave 方向）
    - reversal: 反转 **break 方向**
    
    例子：
    - UP wave → 下 break（break_direction=DOWN）→ 下突破 → continuation
    - UP wave → 下 break（break_direction=DOWN）→ 上突破 → reversal
    - DOWN wave → 上 break（break_direction=UP）→ 上突破 → continuation
    - DOWN wave → 上 break（break_direction=UP）→ 下突破 → reversal
    """
    
    CONTINUATION = "continuation"  # 延续 break 方向
    REVERSAL = "reversal"          # 反转 break 方向
```

### 执行步骤

#### Step 1：读取现有 types.py
```bash
cd I:/asteria-riskbench-components/malf-engine
# 使用 Read 工具读取 src/malf/types.py
```

#### Step 2：在文件末尾添加 Range 数据结构
在 `CoreStateSnapshot` 定义之后，添加：
1. `RangeState` enum
2. `RangeResolutionType` enum
3. `RangeSnapshot` dataclass

**注意事项：**
- 保持与现有代码风格一致（frozen=True, Optional 类型标注）
- Docstring 需要包含 v2.1 规格章节引用
- 命名陷阱警告必须在 `RangeResolutionType` 的 docstring 中明确说明
- 两层边界模型的使用场景必须在 `RangeSnapshot` 的 docstring 中说明

#### Step 3：验证导入和语法
```bash
cd I:/asteria-riskbench-components/malf-engine
/d/miniconda/py310/python.exe -c "from malf.types import RangeSnapshot, RangeState, RangeResolutionType; print('导入成功')"
```

#### Step 4：运行测试
```bash
/d/miniconda/py310/python.exe -m pytest -v
```

**预期结果：** 47 passed, 1 skipped（新增的数据类暂时不会被使用，不影响现有测试）

---

## 任务三：P2-1 创建 version.py

### 目标
创建统一的版本常量文件，便于未来维护和版本追溯。

### 文件内容

创建 `src/malf/version.py`：

```python
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
```

### 执行步骤

#### Step 1：创建 version.py
使用 Write 工具创建文件。

#### Step 2：验证导入
```bash
cd I:/asteria-riskbench-components/malf-engine
/d/miniconda/py310/python.exe -c "from malf.version import CORE_RULE_VERSION, RANGE_RULE_VERSION; print(f'Core: {CORE_RULE_VERSION}, Range: {RANGE_RULE_VERSION}')"
```

#### Step 3（可选）：更新 types.py 使用 version.py 常量
在 `types.py` 的 `CoreStateSnapshot` 中，可以将硬编码版本字符串替换为：

```python
from malf.version import (
    CORE_RULE_VERSION,
    PIVOT_DETECTION_RULE_VERSION,
    PRICE_POLICY,
    CORE_SNAPSHOT_SCHEMA_VERSION,
)

@dataclass(frozen=True)
class CoreStateSnapshot:
    # ...
    core_rule_version: str = CORE_RULE_VERSION
    pivot_detection_rule_version: str = PIVOT_DETECTION_RULE_VERSION
    price_policy: str = PRICE_POLICY
    schema_version: str = CORE_SNAPSHOT_SCHEMA_VERSION
```

**注意：** 这一步是可选的，如果修改需要重新运行所有测试确保无回退。

---

## 完成标志

Day -1 完成 = 以下全部达标：

1. ✅ P0-1：所有 `WaveStructuralSnapshot` 已重命名为 `WaveStructuralSnapshot`
2. ✅ P1-2：`types.py` 已添加 `RangeSnapshot`, `RangeState`, `RangeResolutionType`
3. ✅ P2-1：已创建 `src/malf/version.py`
4. ✅ 测试仍然全绿（47 passed, 1 skipped）
5. ✅ 创建完成报告 `docs/T6-DAY-MINUS-1-COMPLETION.md`

---

## 完成报告模板

任务完成后，创建 `docs/T6-DAY-MINUS-1-COMPLETION.md`：

```markdown
# 第六刀 Day -1 准备工作完成报告

**日期：** 2026-07-26  
**任务：** P0-1 类型名重命名 + P1-2 数据结构补充 + P2-1 版本常量  
**状态：** ✅ 已完成

## 完成的任务

### ✅ P0-1：类型名重命名
- WaveStructuralSnapshot → WaveStructuralSnapshot
- 影响文件：[列出修改的文件]
- 测试验证：47 passed, 1 skipped ✅

### ✅ P1-2：Range 数据结构补充
- 新增：RangeState enum
- 新增：RangeResolutionType enum
- 新增：RangeSnapshot dataclass
- 位置：src/malf/types.py

### ✅ P2-1：版本常量文件
- 新增：src/malf/version.py
- 包含：CORE_RULE_VERSION, RANGE_RULE_VERSION 等常量

## 数据结构说明

### RangeSnapshot 关键设计
- **两层边界模型**（v2.1 Range §3）：
  - boundary_init: 冻结边界（Core 层使用）
  - boundary_now: 演化边界（Range 层使用）
- **命名陷阱**（v2.1 Range §6）：
  - continuation = 延续 break 方向（不是旧 wave 方向）
  - reversal = 反转 break 方向

## 验证结果

测试状态：47 passed, 1 skipped ✅（与修改前一致）

## 下一步

Day 0 任务：
- 开始推 6 个 Range fixture 预期输出
- 使用 debug_t6.py 工具辅助人肉推导
- 复核铁律：窗口填充 >= k、严格不等式

---

**Day -1 准备工作完成。准备进入 Day 0（推 fixture）。**
```

---

## 参考文档

### 项目文档
- **实施指南：** `docs/T6-RANGE-IMPLEMENTATION-GUIDE.md`（Day -3 创建，34 KB）
- **建造计划：** `docs/BUILD-PLAN.md`（第六刀章节）
- **Day -3 完成报告：** `docs/T6-DAY-MINUS-3-COMPLETION.md`
- **Day -2 完成报告：** `docs/T6-DAY-MINUS-2-COMPLETION.md`

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

执行 Day -1 准备工作，用 45 分钟完成：
1. 类型名重命名（P0-1）
2. Range 数据结构补充（P1-2）
3. 版本常量文件创建（P2-1）
4. 测试验证
5. 创建完成报告

**开始执行。**
