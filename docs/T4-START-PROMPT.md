# 第四刀启动 Prompt

## 背景

我正在开发 **malf-engine** 项目（MALF v2.0 结构计算引擎）。

**已完成**：
- ✅ 第一刀：uninitialized → up_alive（初始上涨波段）
- ✅ 第二刀：uninitialized → down_alive（初始下跌波段）
- ✅ 第三刀：up/down_alive → transition（guard break 检测）

**当前测试状态**：23 passed, 2 failed (fixture 设计问题，不影响核心逻辑)

## 第四刀目标

实现 **Transition 期间 Active Candidate 演化**，包括：

1. **Active Candidate 跟踪**
   - transition 状态下继续检测新的 pivots
   - 跟踪反向候选（up_alive → L candidates, down_alive → H candidates）

2. **L0/H0 替换逻辑**（C-07 消歧）
   - UP: transition 期间出现新的 L，低于当前 active candidate → 替换
   - DOWN: transition 期间出现新的 H，高于当前 active candidate → 替换

3. **L1/H1 替换逻辑**（C-08 消歧）
   - UP: L1 确认后，出现新的 H 高于 H0 → 替换 H1
   - DOWN: H1 确认后，出现新的 L 低于 L0 → 替换 L1

4. **New Wave 确认**（Opposite-direction Break）
   - UP→DOWN: transition 期间确认 L0，出现 H1，再出现 L2 < L0 → new down wave
   - DOWN→UP: transition 期间确认 H0，出现 L1，再出现 H2 > H0 → new up wave
   - 或者实现 same-direction recovery（回到 up/down_alive）

## 关键约束

1. **遵循 BUILD-CONTRACT.md §5 经验教训**（7 条铁律）
2. **TDD 方法**：先写 golden fixture，再写测试，最后实现
3. **对称实现**：UP 和 DOWN 方向必须对称
4. **零外部依赖**：纯 Python 标准库

## 环境信息

**工作目录**：`I:\asteria-riskbench-components\malf-engine`

**Python 路径**：`/d/miniconda/py310/python.exe`（系统 `python` 不可用）

**运行测试**：
```bash
cd /i/asteria-riskbench-components/malf-engine
/d/miniconda/py310/python.exe -m pytest
```

**TDX 数据**：`I:/new_tdx64/vipdoc/sh/lday/sh600000.day`

## 参考文档

- `docs/BUILD-PLAN.md` - 第四刀详细计划
- `docs/BUILD-CONTRACT.md` - 验收标准和经验教训
- `CLAUDE.md` - 项目概述和架构
- `src/malf/core_engine.py` - 当前状态机实现（第三刀）
- `../../asteria-riskbench/new-docs/MALF_v2.0_引擎规格_定稿.md` - 规格文档

## 真实数据发现

第三刀真实数据测试暴露了 **L0 替换场景**（bar 12 触发）：
```
[WARN] Hit replacement NotImplementedError at bar 12: 
L0 之后H1 确认前出现第二个 L（规则 C-07）
```

这是第四刀需要首先实现的场景。

## 任务

请按照 TDD 方法实现第四刀：

### Step 1: 阅读规格（15 分钟）
- 阅读 BUILD-PLAN.md 第四刀部分
- 理解 transition 状态下的 active candidate 演化规则
- 理解 L0/H0 替换（C-07）、L1/H1 替换（C-08）规则

### Step 2: Golden Fixture 人肉推导（30 分钟）
- 设计 L0 替换场景（UP 方向）
- 设计 H0 替换场景（DOWN 方向）
- 设计 new wave 确认场景
- 创建 debug 脚本验证 pivot 检测

### Step 3: 写测试（RED）
- 单元测试：`test_transition_active_candidate.py`
- 端到端测试：`test_t4_transition_evolution.py`
- 使用第三刀的模式（复用已验证序列 + 关键 bars）

### Step 4: 实现逻辑（GREEN）
- 更新 `src/malf/core_engine.py`
- 实现 transition 状态下的 pivot 跟踪
- 实现 L0/H0 替换逻辑
- 实现 new wave 确认或 same-direction recovery

### Step 5: 验证
- 单元测试全部通过
- 真实数据冒烟测试通过（应该能处理 bar 12 的 L0 替换）
- 与第一刀/第二刀/第三刀测试兼容

### Step 6: 文档回补
- 更新 BUILD-PLAN.md
- 更新 DAILY-LOG（创建新日期或继续 2026-07-26）
- 创建 T4-COMPLETION-SUMMARY.md

## 预期结果

- transition 状态下能正确跟踪 active candidate
- L0/H0 替换逻辑正确实现
- 真实数据测试能处理到 bar 12 之后
- 所有测试通过（目标：30+ passed）

## 开始

请从 **Step 1** 开始，阅读 BUILD-PLAN.md 第四刀部分，理解需求后告诉我你的理解和计划。
