# AI 助手任务工作流程 SOP

> 本文档固化 AI 助手（Claude）执行不同类型任务时的标准操作流程。
> 目的：把隐性知识显性化，确保任务执行的一致性与完整性。

**版本**: 2026-07-31  
**维护原则**: 每次发现流程不清晰或遗漏检查项时更新本文件

---

## 📋 通用流程（所有任务）

### 接到任务后，先问三个问题

1. **这是什么类型的任务？** → 见下面 A/B/C/D 分类
2. **当前在哪一刀？** → 看 `docs/.plan/00-当前状态.md`
3. **有没有违反七条铁律？** → 看 `docs/spec/BUILD-CONTRACT.md` §5

### 必查文档（按顺序）

| 顺序 | 文档 | 看什么 | 何时跳过 |
|------|------|--------|----------|
| 1️⃣ | `CLAUDE.md` | 约束、禁区、已知空白、当前实现状态 | 从不跳过 |
| 2️⃣ | `.plan/00-当前状态.md` | 当前进度、下一步、待做工作 | 纯文档任务可跳过 |
| 3️⃣ | `spec/BUILD-CONTRACT.md` §5 | 七条铁律 | 不涉及代码可跳过 |

---

## 🔧 任务类型 A：写新代码

**触发词**: "实现 XXX"、"写 XXX 功能"、"添加 XXX 层"

### 执行顺序（严格）

#### Step 1: 查规格与补丁

- **查规格** → `docs/spec/MALF_V2_1_AUTHORITY_REFERENCE.md`
  - 找对应编号（如 D18、R1、T6）
  - 确认公式、字段定义、不变量
- **查补丁** → `docs/spec/IMPLEMENTATION-CONTRACT-PATCH.md`
  - 检查对应缺口是否已闭合
  - 如果缺口状态是"待确认"，**停止**，询问用户

#### Step 2: 写 Golden Fixture（铁律 1）

- **位置**: `tests/fixtures/{module}_*.json`
- **内容**: 人肉推导的预期输出（**不是**被测代码生成）
- **命名**: 
  - 场景描述性命名（如 `initialization_up_clean_sequence.json`）
  - 不用 `test1/test2` 这种无意义名字
- **结构**: 
  ```json
  {
    "description": "人类可读的场景描述",
    "input": { ... },
    "expected_output": { ... }
  }
  ```

#### Step 3: 写测试（RED）

- **位置**: `tests/test_{module}.py`
- **原则**:
  - 测试名描述场景（如 `test_up_direction_clean_sequence`）
  - 先运行，确认 **RED**（失败）
  - 不要写"总会通过"的测试

#### Step 4: 写实现（GREEN）

- **位置**: `src/malf/{module}.py`
- **原则**:
  - 只实现 fixture 驱动的部分
  - 未实现分支显式抛 `NotImplementedError`（带说明）
  - 价格一律用 `int`，禁止 `float`
  - 不可变对象用 `@dataclass(frozen=True)`

#### Step 5: 真实数据验证（关键功能）

**何时需要**:
- 新层完成时（如 Core 层、Range 层）
- 修复 P0/P1 问题后
- 涉及公式变更时

**验证方式**:
```bash
# 运行流水线
python scripts/verify/v1_full_integration_pipeline.py

# 检查 lineage_hash 确定性
python scripts/verify/verify_lineage_determinism.py
```

#### Step 6: 记录实施过程

- **位置**: `docs/.record/decisions/` 或 `docs/.record/issues/`
- **何时记录**:
  - 做了非显而易见的技术决策（ADR）
  - 发现并修复了 bug（Issue）
  - 规格与实现有争议点需要记录

---

## 📝 任务类型 B：修改规格

**触发词**: "更新规格"、"补丁 XXX"、"规格缺口"

### 执行顺序

#### Step 1: 确认规格层级

| 规格类型 | 文件 | 修改难度 |
|---------|------|---------|
| **权威引用** | `spec/MALF_V2_1_AUTHORITY_REFERENCE.md` | 🔴 极少改（仅引用） |
| **建造合同** | `spec/BUILD-CONTRACT.md` | 🟡 重大决策时 |
| **实现补丁** | `spec/IMPLEMENTATION-CONTRACT-PATCH.md` | 🟢 发现缺口即补 |

#### Step 2: 写补丁（如需要）

- **格式**: 见 `IMPLEMENTATION-CONTRACT-PATCH.md` 现有条目
- **必含字段**:
  - 缺口编号（如 L4-6）
  - 问题描述
  - 解决方案
  - 状态（待确认 / 已闭合）

#### Step 3: 代码验证（如有代码影响）

- 补丁闭合前，必须有代码验证
- 不允许"纸上立法"

---

## 🐛 任务类型 C：调试/修复

**触发词**: "修复 XXX bug"、"为什么 XXX 不对"

### 执行顺序

#### Step 1: 复现问题

- **最小可复现脚本**: `scripts/debug/debug_{issue}.py`
- **记录输入输出**: 预期 vs 实际

#### Step 2: 定位根因

- 查看相关不变量（Core 8条，Range 3条）
- 检查 fixture 是否覆盖此场景
- 对照规格公式

#### Step 3: 写失败测试（RED）

- 先写能暴露 bug 的测试
- 确认测试失败

#### Step 4: 修复实现（GREEN）

- 最小改动原则
- 修复后运行全量测试

#### Step 5: 记录修复

- **位置**: `docs/.record/issues/{issue-id}.md`
- **内容**:
  - 问题描述
  - 根因分析
  - 修复方案
  - 影响范围

---

## 📚 任务类型 D：整理文档

**触发词**: "更新文档"、"归档 XXX"

### 执行顺序

#### Step 1: 确认目标位置

| 文档类型 | 目录 | 说明 |
|---------|------|------|
| **规格** | `spec/` | WHAT + HOW（永久） |
| **计划** | `.plan/` | WHEN + WHO（活文档） |
| **记录** | `.record/` | 实际发生了什么（归档） |

#### Step 2: 移动或创建文档

- 遵循三层架构原则
- 更新索引文件（`00-INDEX.md`）
- 更新相互引用链接

#### Step 3: 验证链接完整性

```bash
# 检查断链
grep -r "\[.*\](.*\.md)" docs/ | grep -v "http"
```

---

## 🎯 快速决策树

```
收到任务
│
├─ 涉及代码？
│  ├─ 是 → 任务类型 A（写代码）或 C（修复）
│  └─ 否 → 任务类型 B（改规格）或 D（整理文档）
│
├─ 有规格依据？
│  ├─ 有 → 查 MALF_V2_1_AUTHORITY_REFERENCE.md
│  └─ 无 → 检查 IMPLEMENTATION-CONTRACT-PATCH.md 是否有缺口
│
└─ 需要验证？
   ├─ 关键功能 → 真实数据验证（V1 流水线）
   └─ 修复/变更 → 全量测试 + lineage_hash 确定性检查
```

---

## 🚨 红线检查清单

### 每次提交前必查

- [ ] 价格是否全部用 `int`？（禁止 `float`）
- [ ] 是否引入了外部依赖？（Core/Range/Lifespan 禁止）
- [ ] 修改了算法是否跑了 lineage_hash 验证？
- [ ] 新功能是否有 golden fixture？
- [ ] 文档引用是否更新？

### 每个新层完成后

- [ ] 不变量测试全部通过
- [ ] Golden fixture 覆盖主要路径
- [ ] 真实数据验证通过（V1 流水线）
- [ ] 更新 `.plan/00-当前状态.md` 进度

---

**文档维护**: 发现流程不清晰时立即更新  
**最后更新**: 2026-07-31（文档架构重构）
