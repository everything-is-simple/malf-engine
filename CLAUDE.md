# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指引。

## 项目概述

**malf-engine** 是 Asteria RiskBench 系统的 MALF v2.0 结构计算核心。吃 OHLC 价格数据，吐 `WaveProbabilitySnapshot` 结构。引擎设计为确定性、单遍、**零外部依赖**（纯 Python 3.10+ 标准库）。

**关键约束**：领域核心零外部依赖，以保证 replay 确定性（spec §7.4, O8）。永远不要建议在核心引擎中添加 numpy、pandas 或任何外部库——不同版本/平台的 float 精度变化会破坏 `lineage_hash` 的 replay 校验。

## 架构

### 五层结构
引擎组织为五层（当前正在实现第一层）：
- **L1 Core**：结构状态机（pivot 检测、初始化、guard/progress 跟踪）
- **L2 Range**：break 检测与 range 状态
- **L3 Lifespan**：波段生命周期管理
- **L4 Probability**：波段概率计算
- **L5 Service**：公共 API 层

### 当前实现状态
**第一刀完成**：`uninitialized → up_alive` 转换（spec §2, S1-S9 事件序列）。
- 16 个测试通过，1 个跳过（真实数据冒烟测试在 Windows 上需要 TDX 路径）
- 覆盖：pivot k=2 延迟确认、first guard = L1、initial wave 创建

### 核心模块

- **`types.py`**：使用 stdlib dataclass 的核心数据结构。价格为整数（`int_fixed`）以避免 float 精度问题。定义 `PriceBar`、`Pivot`（双时间戳：`extreme_bar_dt` + `confirm_bar_dt`）、`CoreStateSnapshot`，以及枚举（`SystemState`、`Direction`、`WaveCoreState`、`PivotType`）。

- **`pivot_detection.py`**：分形 k=2 窗口检测。产出 pivot 列表，不含状态机逻辑。窗口不足时返回空列表（不是错误）。

- **`initialization.py`**：初始波段检测（D18/O6）。当前只实现**上涨方向**干净序列（`H0 → L1 → H2, H2 > H0`）。下跌方向、H0 替换、L1 替换显式抛出 `NotImplementedError`——等待 golden fixture（见 BUILD-PLAN.md）。

- **`fingerprint.py`**：运行时指纹生成（`py3.10.19|win32|CPython`）。这是审计元数据，不进入 `lineage_hash` 计算。

- **`core.py`**：状态机骨架（当前是占位符，等待完整实现）。

## 开发命令

### Python 环境

**⚠️ 重要：Windows 环境下的 Python 路径**

系统 PATH 中的 `python` 命令指向 Windows Store 重定向器（返回 exit code 49）。
**必须使用实际安装的 Python**：

```bash
# Windows 上的实际 Python 路径
/d/miniconda/py310/python.exe

# 验证版本
/d/miniconda/py310/python.exe --version
# 输出: Python 3.10.19
```

### 环境搭建
```bash
cd malf-engine
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Unix:
. .venv/bin/activate

pip install -e ".[dev]"
```

### 测试
```bash
# ⚠️ Windows: 必须使用完整路径
/d/miniconda/py310/python.exe -m pytest

# 运行所有测试
/d/miniconda/py310/python.exe -m pytest

# 运行特定测试文件
/d/miniconda/py310/python.exe -m pytest tests/test_pivot_detection.py

# 详细输出
/d/miniconda/py310/python.exe -m pytest -v

# 运行单个测试函数
/d/miniconda/py310/python.exe -m pytest tests/test_initialization.py::test_up_direction_clean_sequence
```

### 验收机制
测试就是验收机制。没有单独的 build 或 lint 命令。项目使用：
- **Golden fixtures**：在 `tests/fixtures/*.json` 中人肉推导的预期输出（非被测代码生成）
- **TDD 方法**：RED → GREEN 循环，fixture 驱动实现
- **Replay 确定性**：相同输入 + 相同版本 → 逐字节相同的 snapshot 和 `lineage_hash`

## 文档层级

**四个文档，各司其职**（见 README.md）：

1. **Spec**（WHAT）：`../../asteria-riskbench/new-docs/MALF_v2.0_引擎规格_定稿.md` — 所有规则、公式、字段、编号的唯一真相源。永远不要在代码或文档中复述规格内容。

2. **BUILD-CONTRACT.md**（稳定）：范围、非目标、验收标准。极少改动。**§5 经验教训**：第一刀、第二刀累积的 7 条铁律，第三刀起强制遵循。

3. **BUILD-PLAN.md**（活的）：当前这一刀的 step 清单。每天更新。

4. **IMPLEMENTATION-CONTRACT-PATCH.md**（实施）：deepseek 审计的 43 条缺口闭合。包含勘误、还原、消歧、立法四层。TDD 前必读。

**实现时**：参考 spec 查行为规则。查 BUILD-PLAN.md 了解已知空白和 NotImplementedError 位置。查 IMPLEMENTATION-CONTRACT-PATCH.md 了解规格缺口的闭合决策。**查 BUILD-CONTRACT.md §5 了解必须遵循的铁律**（fixture 设计、TDD 流程、真实数据验证、文档回补）。不要实现推测性功能——只做 golden fixture 驱动的部分。

## 编码原则

### 数据完整性
- **只用整数价格**：所有价格为 `int`（int_fixed 策略，spec §7.1）。永远不要用 `float` 做价格计算。
- **Pivot 双时间戳**：`extreme_bar_dt`（pivot 实际发生时刻）+ `confirm_bar_dt`（k 根后确认时刻）。这反映了 spec §2.4 的时序不对称。
- **不可变数据**：值对象使用 `@dataclass(frozen=True)`。

### TDD 工作流
1. **Golden fixture 先行**：在写实现代码前先人肉推导预期输出
2. **显式 NotImplementedError**：对未实现分支（下跌方向、H0/L1 替换）。规格模糊时永远不要猜——在 BUILD-PLAN.md 中记录空白
3. **测试覆盖**：所有 8 条 Core 不变量（spec §2.10）必须有对应测试
4. **不要提前实现**：没有 golden fixture 驱动时不要实现下跌方向

### 状态机规则
- **逐 bar 推进**：状态机按顺序处理 bar。Pivot 在其 `confirm_bar_dt` 被看见，不是 `extreme_bar_dt`。
- **O6 失败规则**：结构不足时返回 `confirmed=False`（不是异常）。只有真正未实现的分支才抛 `NotImplementedError`。
- **状态不混用**：`SystemState` 和 `WaveCoreState` 永远不混用。系统可以是 `uninitialized/up_alive/down_alive/transition`；波段只有 `alive/terminated`。

### 版本控制
- **runtime_fingerprint**：记录 Python 版本、平台、实现供审计用。不进入 `lineage_hash`（spec §7.6, L4-6）。
- **schema_version**：每种 snapshot 类型独立版本号（如 `"malf-core-snapshot-v0"`）。Spec §7.6, L4-7。

## 已知空白（来自 BUILD-PLAN.md）

这些是显式记录的未实现功能：

1. **下跌方向初始化**：Spec §2.4 描述了 `L0 → H1 → L2, L2 < L0` 但还没有 golden fixture。`find_initial_wave()` 对 L 开头的序列抛 `NotImplementedError`。

2. **H0 替换（填洞 C-07）**：当 H0 确认后、L1 出现前又来一个更高的 H 时，spec 说"可以替换 H0"但没定义替换后 L1 候选范围。当前抛 `NotImplementedError`。

3. **L1 替换**：当 L1 确认后、H2 出现前又来一个更低的 L 时，spec 完全没提。当前抛 `NotImplementedError`。

没有对应的 golden fixture 和 spec 明确前，不要实现这些。

## 文件路径与上下文

这是一个**实验目录**（`RB-FX-008`），独立 venv。五层全部通过 trial + replay 验证后，代码会搬到主仓库 `src/riskbench/malf/`。

仓库结构：
- `src/malf/`：领域核心实现
- `tests/`：所有测试文件（pytest 发现 `test_*.py`）
- `tests/fixtures/`：人肉推导预期输出的 golden fixture JSON 文件
- `docs/`：BUILD-CONTRACT.md（稳定）和 BUILD-PLAN.md（活的清单）

## 禁止事项

- ❌ 给领域核心添加外部依赖（numpy、pandas、pydantic 等）
- ❌ 价格值用 `float`
- ❌ 实现没有 golden fixture 驱动的功能
- ❌ 在 docstring 或文档中复述 spec 内容
- ❌ 规格模糊时猜测行为——应记录空白
- ❌ 创建数据适配器、viewer 或产品层功能（那些属于 RiskBench，不属于引擎）
- ❌ 在 `find_initial_wave()` 中对 pivot 排序/重排——调用方按 `confirm_bar_dt` 顺序提供
