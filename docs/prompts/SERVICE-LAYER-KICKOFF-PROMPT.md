# MALF Engine Service 层开发 Prompt

## 项目背景

你正在开发 **malf-engine**，这是 Asteria RiskBench 系统的 MALF v2.1 结构计算核心引擎。

**当前状态**：
- 项目进度：18/20 刀完成（90%）
- 已完成：Core、Range、Lifespan、Structural Position 四层
- **待完成**：Service 层（最后 2 刀）
- 测试状态：89 passed, 2 skipped ✅
- 规格合规度：95% ✅

**重要**：这是一个**零外部依赖**的纯 Python 3.10+ 标准库项目。永远不要建议添加 numpy、pandas 或任何外部库。

---

## 任务目标

完成 Service 层的 2 刀任务（T9.1 和 T9.2），实现对外接口层。

### T9.1: Usage 判定 + 失败模式（预计 1-2 天）
- 实现 usage 判定逻辑（normal/degraded/rejected）
- 实现 reason_codes 枚举和判定
- 实现失败模式处理
- 编写测试用例

### T9.2: 持久化 + 中断恢复（预计 2-3 天）
- 实现序列化支持（JSON）
- 实现 lineage_hash 计算
- 实现状态快照持久化
- 实现中断恢复机制
- 编写测试用例

---

## 关键文档路径

### 必读文档（按顺序）

1. **项目入口**：`I:\asteria-riskbench-components\malf-engine\CLAUDE.md`
   - 项目概述、架构、开发命令、禁止事项

2. **开发计划**：`I:\asteria-riskbench-components\malf-engine\docs\dev\BUILD-PLAN.md` ⭐
   - 当前进度、T9.1-T9.2 详细任务清单
   - 下一步行动、完成标志

3. **工作流 SOP**：`I:\asteria-riskbench-components\malf-engine\docs\dev\AI-TASK-WORKFLOW.md` ⭐⭐
   - **强制遵循**：接到任务后的标准操作流程
   - 任务类型判定、执行步骤、文档更新规则

4. **规格文档**：
   - **权威规格**：`I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\MALF_05_Service_v2_1-deepseek-20260726.md`
   - **实施补丁**：`I:\asteria-riskbench-components\malf-engine\docs\spec\IMPLEMENTATION-CONTRACT-PATCH.md`
   - **验收标准**：`I:\asteria-riskbench-components\malf-engine\docs\spec\BUILD-CONTRACT.md`（§5 经验教训 - 7 条铁律）

5. **文件组织规范**：`I:\asteria-riskbench-components\malf-engine\docs\dev\FILE-ORGANIZATION.md`
   - 文件创建前必读
   - 根目录只允许 4 个文件（README.md, CLAUDE.md, pyproject.toml, .gitignore）
   - 临时文件放 `.work/`，完成后归档到 `docs/reports/` 或 `docs/archive/`

---

## 工作流（强制遵循）

### 启动任务时

1. **阅读 AI-TASK-WORKFLOW.md**，确认任务类型（这是"写代码"任务）
2. **阅读 BUILD-PLAN.md § T9.1 或 T9.2**，了解详细 step 清单
3. **阅读规格文档 MALF_05_Service_v2_1**，理解业务逻辑
4. **查看 BUILD-CONTRACT.md §5**，确认 7 条铁律

### 执行任务时

#### 阶段 1：准备（RED）
1. 创建任务工作目录：`.work/T9.1/` 或 `.work/T9.2/`
2. 推导 Golden Fixture（人肉推导，存 `.work/T9.x/draft_fixture.json`）
3. 定稿 Fixture（移到 `tests/fixtures/t9_x_*.json`）

#### 阶段 2：实现（GREEN）
1. 补充数据结构（`src/malf/types.py`）
2. 实现核心逻辑（`src/malf/service_engine.py` 或新建）
3. 编写测试（`tests/test_service_*.py`）
4. 运行测试：`/d/miniconda/py310/python.exe -m pytest tests/test_service_*.py -v`

#### 阶段 3：验证（REFACTOR）
1. 运行完整回归测试：`/d/miniconda/py310/python.exe -m pytest`
2. 真实数据冒烟测试（如适用）
3. 更新 BUILD-PLAN.md（勾选完成的 step）

#### 阶段 4：提交
1. Git 提交：`git add -A && git commit -m "feat(service): 完成 T9.x [描述]"`
2. Git 推送：`git push origin docs/add-ai-task-workflow-sop`
3. 清理临时文件（`.work/` 下的草稿）

---

## 关键约束和原则

### 架构约束

1. **零外部依赖**：领域核心只用 Python 3.10+ 标准库（dataclass, typing, datetime, hashlib）
2. **整数价格**：所有价格用 `int`（int_fixed），永远不用 `float`
3. **不可变数据**：值对象用 `@dataclass(frozen=True)`
4. **确定性**：相同输入 + 相同版本 → 逐字节相同的输出和 lineage_hash

### TDD 原则

1. **Golden Fixture 先行**：在写实现前人肉推导预期输出
2. **显式 NotImplementedError**：对未实现分支（不要猜）
3. **测试覆盖**：所有不变量必须有对应测试
4. **不要提前实现**：没有 fixture 驱动时不实现

### 文件组织原则

1. **根目录清洁**：禁止创建 `verify_*.py`, `debug_*.py`, `TEST-*.ps1`
2. **临时文件**：放 `.work/debug/` 或 `.work/T9.x/`
3. **报告归档**：完成后移到 `docs/reports/` 或 `docs/archive/tasks/T9.x/`
4. **任务完成后清理**：删除 `.work/` 下的临时文件，运行 `git status` 检查根目录

### Git 提交原则

1. **提交前测试**：确保所有测试通过
2. **语义化提交**：`feat(service): ...` / `fix(service): ...` / `test(service): ...`
3. **推送前检查**：`git status` 确保无遗漏文件

---

## 数据结构参考

### 已有的核心数据结构（在 `src/malf/types.py`）

```python
@dataclass(frozen=True)
class PriceBar:
    symbol: str
    timeframe: str
    bar_dt: str
    open: int
    high: int
    low: int
    close: int

@dataclass(frozen=True)
class Pivot:
    pivot_type: PivotType
    price: int
    extreme_bar_dt: str
    confirm_bar_dt: str
    confirm_price: int
    pivot_id: Optional[str] = None

@dataclass(frozen=True)
class CoreStateSnapshot:
    bar_dt: str
    system_state: SystemState
    direction: Optional[Direction]
    guard_price: Optional[int]
    progress_price: Optional[int]
    # ... 其他字段
```

### 需要实现的 Service 层数据结构

参考规格 MALF_05_Service_v2_1 §2-§4：

```python
@dataclass(frozen=True)
class WaveStructuralSnapshot:
    """最终对外快照（Service 层输出）"""
    schema_version: str
    bar_dt: str
    usage: Literal["normal", "degraded", "rejected"]
    reason_codes: List[str]
    
    # Core 层
    core: CoreStateSnapshot
    
    # Range 层
    active_range: Optional[RangeSnapshot]
    
    # Lifespan 层
    current_wave_lifespan: Optional[WaveLifespan]
    current_range_lifespan: Optional[RangeLifespan]
    
    # Structural Position 层
    p1_self_rank: Optional[P1SelfRank]
    p2_same_dir_momentum: Optional[P2SameDirMomentum]
    p3_cross_dir_momentum: Optional[P3CrossDirMomentum]
    p4_cross_compare: Optional[P4CrossCompare]
    
    # 元数据
    lineage_hash: str
    runtime_fingerprint: str
```

---

## 测试策略

### T9.1 测试场景

1. **Normal Usage**：正常流程，所有层级数据完整
2. **Degraded Usage**：部分层级数据缺失（如 peer_sample 不足）
3. **Rejected Usage**：关键数据缺失（如初始化失败）
4. **Reason Codes**：验证各种失败原因码

### T9.2 测试场景

1. **Serialization**：快照序列化为 JSON
2. **Deserialization**：JSON 反序列化为快照
3. **Lineage Hash**：确定性验证（相同输入 → 相同 hash）
4. **State Persistence**：状态保存和加载
5. **Interruption Recovery**：中断后恢复

---

## 开发命令速查

```bash
# 进入项目目录
cd I:\asteria-riskbench-components\malf-engine

# 激活虚拟环境（如果需要）
.venv\Scripts\activate

# 运行测试（Windows 必须用完整路径）
/d/miniconda/py310/python.exe -m pytest

# 运行特定测试文件
/d/miniconda/py310/python.exe -m pytest tests/test_service_usage.py -v

# 运行单个测试函数
/d/miniconda/py310/python.exe -m pytest tests/test_service_usage.py::test_normal_usage -v

# 查看测试覆盖
/d/miniconda/py310/python.exe -m pytest --co

# Git 操作
git status
git add -A
git commit -m "feat(service): ..."
git push origin docs/add-ai-task-workflow-sop
```

---

## 常见陷阱（避免）

### ❌ 禁止做的事

1. **添加外部依赖**（numpy, pandas, pydantic 等）
2. **使用 float 做价格计算**
3. **在没有 fixture 驱动时实现功能**
4. **在 docstring 或文档中复述规格内容**（应引用规格编号）
5. **规格模糊时猜测行为**（应记录空白）
6. **在根目录创建临时脚本**
7. **提交前不运行测试**

### ✅ 应该做的事

1. **价格值用 `int`**
2. **数据对象用 `@dataclass(frozen=True)`**
3. **Golden Fixture 人肉推导**（不是代码生成）
4. **显式 `NotImplementedError`** 对未实现分支
5. **引用规格编号**（如"符合规格 §5.2, R3"）
6. **任务完成后清理** `.work/` 目录
7. **每完成一个 step 更新** BUILD-PLAN.md

---

## P1 待办提醒

在开始 Service 层前，有 2 个 P1 级问题可以选择先处理（不阻塞 Service 层开发）：

1. **P1-3: progress_pct 计算公式待核对**（1小时）
   - 位置：`src/malf/lifespan_engine.py:79-82`
   - 需要与规格 MALF_03_Lifespan_v2_1 对照

2. **P1-4: CoreStateSnapshot 添加 bar_index**（20分钟）
   - 位置：`src/malf/types.py:CoreStateSnapshot`
   - 添加 `bar_index: int` 字段用于追踪

---

## 启动任务的第一步

1. **阅读本 prompt** ✅（你已经在做）
2. **阅读 `docs/dev/AI-TASK-WORKFLOW.md`**（理解标准流程）
3. **阅读 `docs/dev/BUILD-PLAN.md § T9.1`**（了解第一刀详细任务）
4. **阅读规格 `MALF_05_Service_v2_1`**（理解 Service 层业务逻辑）
5. **开始执行 T9.1 的 step 清单**

---

## 成功标准

### T9.1 完成标志
- [ ] Usage 判定逻辑实现（normal/degraded/rejected）
- [ ] Reason codes 枚举定义
- [ ] 测试用例全部通过
- [ ] BUILD-PLAN.md 标记 T9.1 完成 ✅
- [ ] Git 提交推送

### T9.2 完成标志
- [ ] 序列化/反序列化实现
- [ ] Lineage hash 计算实现
- [ ] 中断恢复机制实现
- [ ] 测试用例全部通过
- [ ] 完整回归测试通过（所有 91+ 测试）
- [ ] BUILD-PLAN.md 标记 T9.2 完成 ✅
- [ ] Git 提交推送

### 项目完成标志
- [ ] 20/20 刀全部完成（100%）
- [ ] 所有测试通过（预计 95+ passed）
- [ ] 规格合规度维持 95%+
- [ ] 真实数据验证通过
- [ ] 文档更新完整
- [ ] `.work/` 目录清理干净

---

## 联系信息

**项目路径**：`I:\asteria-riskbench-components\malf-engine`  
**权威规格**：`I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`  
**当前分支**：`docs/add-ai-task-workflow-sop`  
**Python 路径**：`/d/miniconda/py310/python.exe`（Windows）

---

**准备好了吗？开始 Service 层开发，完成最后 2 刀任务！** 🚀

---

**版本**: v1.0  
**创建日期**: 2026-07-27  
**最后更新**: 2026-07-27 16:30
