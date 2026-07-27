# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指引。

## 项目概述

**malf-engine** 是 Asteria RiskBench 系统的 MALF v2.1 结构计算核心。吃 OHLC 价格数据，吐 `WaveStructuralSnapshot` 结构。引擎设计为确定性、单遍、**零外部依赖**（纯 Python 3.10+ 标准库）。

**关键约束**：领域核心零外部依赖，以保证 replay 确定性（spec §7.4, O8）。永远不要建议在核心引擎中添加 numpy、pandas 或任何外部库——不同版本/平台的 float 精度变化会破坏 `lineage_hash` 的 replay 校验。

## 架构

### 五层结构
引擎组织为五层（**全部完成**）：
- **L1 Core**：结构状态机（pivot 检测、初始化、guard/progress 跟踪）✅
- **L2 Range**：break 检测与 range 状态 ✅
- **L3 Lifespan**：波段生命周期管理 ✅
- **L4 Structural Position**：结构位置视图（4 视图）✅
- **L5 Service**：公共 API 层（usage 判定、持久化、中断恢复）✅

### 当前实现状态

🎊 **项目全部完成！20/20 刀（100%）** 🎊

**Core 层完成** ✅：完整状态机（UP/DOWN 双方向）
- Pivot 检测（k=2 延迟确认）
- 初始化判定（UP/DOWN 双方向）
- Guard break 检测（同向/反向突破）
- Progress 追踪
- TRANSITION 期间 Candidate 机制
- 测试：47 passed
- P0 级修复完成（2026-07-27 commit b4e1562）

**Range 层完成** ✅：震荡区间识别（2026-07-27）
- 两层边界模型（boundary_init + boundary_now）
- Range 生命周期（birth → resolution）
- Range 分类（continuation / reversal）
- Candidate replacement 计数
- 测试：18 passed

**C-07 补丁完成** ✅：早期 Pivot 替换
- H0/L0 替换：更高的 H 替换 H0，更低的 L 替换 L0
- L1/H1 替换：更低的 L 替换 L1，更高的 H 替换 H1
- 真实数据验证：offset=0 成功处理 200 bars
- 测试：4 个替换场景全部通过

**Lifespan 层完成** ✅：生命周期统计与排名（2026-07-27）
- WaveLifespan 指标计算（7 个指标）
- RangeLifespan 指标计算（6 个指标）
- 双轨 peer_sample（UP/DOWN 分池、continuation/reversal 分池）
- Percentile rank 计算（4 个 rank 字段）
- 测试：18 passed

**Structural Position 层完成** ✅：结构位置视图（4/4 完成，2026-07-27）
- P1 自身分位（Self Rank）：透传 rank 值
- P2 同向对照（Same Direction Momentum）：momentum 计算 + 标签
- P3 反向对照（Opposite Direction Momentum）：momentum 计算 + 标签
- P4 正反对照（Cross Compare）：momentum 计算 + alive warning
- 测试：12 passed

**Service 层完成** ✅：对外接口与持久化（2026-07-27）
- T9.1 Usage 判定 + 失败模式：
  - WaveStructuralSnapshot 数据结构（34 字段）
  - UsageType 枚举（4 个值）
  - ReasonCode 枚举（11 个常量）
  - Usage 判定逻辑（G0-G2 优先级）
  - 测试：5 passed
  - 提交：73eb90f
- T9.2 持久化 + 中断恢复：
  - JSON 序列化/反序列化
  - SHA256 lineage_hash 计算（确定性 replay）
  - var/ 目录结构管理
  - 快照持久化（JSON Lines 格式）
  - 原子 current.json 指针更新
  - 中断恢复机制
  - 测试：6 passed
  - 提交：e6bb6bc

**总计测试**：100 passed, 2 skipped ✅

**规格合规度**：~95%（2026-07-27 规格对照检查后修复）

**当前进度**：20/20 刀完成（100%）🎊

### 核心模块

**Core 层**:
- **`types.py`**：核心数据结构（stdlib dataclass）。价格为整数（`int_fixed`）以避免 float 精度问题。定义 `PriceBar`、`Pivot`（双时间戳）、`CoreStateSnapshot`、`RangeStateSnapshot`、`WaveLifespan`、`RangeLifespan`、`WaveStructuralSnapshot`（34 字段）。
- **`pivot_detection.py`**：分形 k=2 窗口检测。产出 pivot 列表，不含状态机逻辑。
- **`initialization.py`**：初始波段检测（UP/DOWN 双方向）。支持 C-07 早期 Pivot 替换规则。
- **`core_engine.py`**：完整状态机（UP_ALIVE/DOWN_ALIVE/TRANSITION/UNINITIALIZED）。Guard break 检测、progress 追踪、candidate 机制。
- **`fingerprint.py`**：运行时指纹生成（审计元数据）。

**Range 层**:
- **`range_engine.py`**：Range 生命周期管理。两层边界模型（boundary_init + boundary_now）、Range 分类（continuation/reversal）。

**Lifespan 层**:
- **`lifespan_engine.py`**：WaveLifespan 和 RangeLifespan 指标计算。双轨 peer_sample、percentile_rank 计算。

**Structural Position 层**:
- **`structural_position_engine.py`**：4 个结构位置视图（P1-P4）。Momentum 计算、标签生成。

**Service 层**:
- **`reason_codes.py`**：11 个 ReasonCode 常量（失败模式）。
- **`service_engine.py`**：Usage 判定逻辑、reason_codes 生成、WaveStructuralSnapshot 组装。
- **`persistence.py`**：JSON 序列化/反序列化、lineage_hash 计算、var/ 目录管理、中断恢复。

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

**入口**: [`docs/00-INDEX.md`](docs/00-INDEX.md) - 文档导航（告诉你看哪个）

**五个核心文档，各司其职**：

1. **AI-TASK-WORKFLOW.md**（HOW）：[`docs/dev/AI-TASK-WORKFLOW.md`](docs/dev/AI-TASK-WORKFLOW.md) ⭐ — **AI 助手任务执行 SOP**。接到任务先看这个，按任务类型（写代码/修规格/调试/整理文档）执行对应流程。固化了"先看哪个文档、做哪些检查、更新哪些文档"的标准操作。

2. **Spec**（WHAT）：[`docs/spec/MALF_V2_1_AUTHORITY_REFERENCE.md`](docs/spec/MALF_V2_1_AUTHORITY_REFERENCE.md) — 所有规则、公式、字段、编号的唯一真相源。永远不要在代码或文档中复述规格内容。

3. **BUILD-CONTRACT.md**（稳定）：[`docs/spec/BUILD-CONTRACT.md`](docs/spec/BUILD-CONTRACT.md) — 范围、非目标、验收标准。极少改动。**§5 经验教训**：第一刀、第二刀累积的 7 条铁律，第三刀起强制遵循。

4. **BUILD-PLAN.md**（活的）：[`docs/dev/BUILD-PLAN.md`](docs/dev/BUILD-PLAN.md) — 当前这一刀的 step 清单。每天更新。告诉你"下一步做什么"。

5. **IMPLEMENTATION-CONTRACT-PATCH.md**（实施）：[`docs/spec/IMPLEMENTATION-CONTRACT-PATCH.md`](docs/spec/IMPLEMENTATION-CONTRACT-PATCH.md) — deepseek 审计的 43 条缺口闭合。包含勘误、还原、消歧、立法四层。TDD 前必读。

6. **API.md**（用户）：[`docs/guide/API.md`](docs/guide/API.md) — CoreStateSnapshot 字段说明，用户手册。

**接到任务后的标准流程**：
1. 先看 **AI-TASK-WORKFLOW.md** 确认任务类型与执行流程
2. 再看 **BUILD-PLAN.md** 确认当前进度
3. 查 **BUILD-CONTRACT.md §5** 确认七条铁律
4. 如需规格，查 **MALF_V2_1_AUTHORITY_REFERENCE.md** 和 **IMPLEMENTATION-CONTRACT-PATCH.md**

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

## 已知空白

**P1-3: progress_pct 计算公式待核对**（低优先级）
- 位置: `lifespan_engine.py:79-82`
- 当前实现: `(wave_end - wave_start) / wave_start`
- 状态: 需与规格定义对照

其他所有功能均已实现并通过测试。

## 文件路径与上下文

这是一个**实验目录**（`RB-FX-008`），独立 venv。五层全部通过 trial + replay 验证后，代码会搬到主仓库 `src/riskbench/malf/`。

仓库结构：
- `src/malf/`：领域核心实现
- `tests/`：所有测试文件（pytest 发现 `test_*.py`）
- `tests/fixtures/`：人肉推导预期输出的 golden fixture JSON 文件
- `docs/`：文档（spec/, guide/, dev/, reports/, archive/）
- `scripts/`：工具脚本（verify/, debug/, tools/）
- `.work/`：临时工作区（gitignore）

**文件组织规范**：详见 `docs/dev/FILE-ORGANIZATION.md`

### 文件创建规则（重要！）

**根目录只允许 4 个文件**：
- ✅ `README.md`, `CLAUDE.md`, `pyproject.toml`, `.gitignore`

**禁止在根目录创建**：
- ❌ `verify_*.py`, `debug_*.py`, `run_*.py` → 应放在 `.work/debug/` 或 `scripts/`
- ❌ `TEST-*.ps1`, `run-*.ps1` → 临时脚本，任务完成后移到 `scripts/` 或删除
- ❌ `*-REPORT.md`, `*-COMPLETE.md` → 应归档到 `docs/archive/` 或 `docs/reports/`

**创建文件前问 3 个问题**：
1. 这是什么类型的文件？（源代码/测试/文档/脚本）
2. 是永久的还是临时的？
3. 任务完成后还需要吗？

**任务完成后的清理**：
- [ ] 删除 `.work/` 下的临时文件
- [ ] 删除根目录的临时脚本
- [ ] 归档报告到 `docs/archive/tasks/{TASK}/`
- [ ] 运行 `git status` 检查根目录是否干净

详见：`docs/dev/FILE-ORGANIZATION.md`

## 禁止事项

- ❌ 给领域核心添加外部依赖（numpy、pandas、pydantic 等）
- ❌ 价格值用 `float`
- ❌ 实现没有 golden fixture 驱动的功能
- ❌ 在 docstring 或文档中复述 spec 内容
- ❌ 规格模糊时猜测行为——应记录空白
- ❌ 创建数据适配器、viewer 或产品层功能（那些属于 RiskBench，不属于引擎）
- ❌ 在 `find_initial_wave()` 中对 pivot 排序/重排——调用方按 `confirm_bar_dt` 顺序提供
