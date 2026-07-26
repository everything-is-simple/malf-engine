# AI 助手任务工作流程 SOP

> 本文档固化 AI 助手（Claude）执行不同类型任务时的标准操作流程。
> 目的：把隐性知识显性化，确保任务执行的一致性与完整性。

**版本**: 2026-07-27  
**维护原则**: 每次发现流程不清晰或遗漏检查项时更新本文件

---

## 📋 通用流程（所有任务）

### 接到任务后，先问三个问题

1. **这是什么类型的任务？** → 见下面 A/B/C/D 分类
2. **当前在哪一刀？** → 看 `BUILD-PLAN.md` 顶部"当前进度"
3. **有没有违反七条铁律？** → 看 `BUILD-CONTRACT.md §5`

### 必查文档（按顺序）

| 顺序 | 文档 | 看什么 | 何时跳过 |
|------|------|--------|----------|
| 1️⃣ | `CLAUDE.md` | 约束、禁区、已知空白、当前实现状态 | 从不跳过 |
| 2️⃣ | `BUILD-PLAN.md` | 当前 step、下一步、勾选状态 | 纯文档任务可跳过 |
| 3️⃣ | `BUILD-CONTRACT.md §5` | 七条铁律 | 不涉及代码可跳过 |

---

## 🔧 任务类型 A：写新代码

**触发词**: "实现 XXX"、"写 XXX 功能"、"添加 XXX 层"

### 执行顺序（严格）

#### Step 1: 查规格与补丁

- **查规格** → `spec/MALF_V2_1_AUTHORITY_REFERENCE.md`
  - 找对应编号（如 D18、R1、T6）
  - 确认公式、字段定义、不变量
- **查补丁** → `spec/IMPLEMENTATION-CONTRACT-PATCH.md`
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
- 关键规则修复时（如 C-07）
- 状态机逻辑变更时

**执行方式**:
1. 写验证脚本 → `scripts/verify/verify_{feature}.py`
2. 使用真实市场数据（如 sh600000）
3. 验证不变量（如 R2、O3）
4. 记录结果 → `docs/reports/{layer}/{feature}-VALIDATION-COMPLETE.md`

#### Step 6: 更新文档

**必更新**:
- [ ] 勾选 `BUILD-PLAN.md` 对应 step
- [ ] 更新 `CLAUDE.md` "实现状态"与"当前进度"

**视情况更新**:
- [ ] 如果是新层，写 `guide/{LAYER}-GUIDE.md`
- [ ] 如果改了 API，更新 `guide/API.md`
- [ ] 如果完成任务，归档到 `archive/tasks/{TASK}/`

---

## 📝 任务类型 B：修规格 / 补丁

**触发词**: "合并 deepseek 补丁"、"修订规格"、"闭合缺口"

### 执行顺序

#### Step 1: 确认修订类型

从 `IMPLEMENTATION-CONTRACT-PATCH.md` 确认缺口属于哪一层：

| 层级 | 性质 | 操作方式 | 风险 |
|------|------|----------|------|
| **第 1 层：勘误** | 纯文档 bug | 直接改 | 零风险 |
| **第 2 层：还原** | 从 v1.4 考据 | 直接还原 | 低风险 |
| **第 3 层：消歧** | 影响状态机 | 需确认后改 | 中风险 |
| **第 4 层：立法** | 定新规则 | 需用户拍板 | 高风险 |

#### Step 2: 执行修订

**第 1、2 层（勘误 + 还原）**:
- 直接改 `spec/IMPLEMENTATION-CONTRACT-PATCH.md`
- 标注 `[已闭合 2026-MM-DD]`

**第 3、4 层（消歧 + 立法）**:
- **先询问用户确认**
- 确认后改 `spec/IMPLEMENTATION-CONTRACT-PATCH.md`
- 标注 `[已立法 2026-MM-DD]` 并注明"非历史还原"

#### Step 3: 禁止事项

- ❌ **不要直接改** `spec/MALF_V2_1_AUTHORITY_REFERENCE.md`
  - 那是已验证的权威版本
  - 修订走补丁，不污染权威版
- ❌ **不要猜测规格**
  - 模糊时记录"待确认"，询问用户

#### Step 4: 更新索引

- [ ] 如果加了新文档，更新 `00-INDEX.md`
- [ ] 如果改了关键规则，更新 `BUILD-PLAN.md` 加注释

---

## 🐛 任务类型 C：调试 / 修 Bug

**触发词**: "XXX 失败了"、"真实数据报错"、"测试不通过"

### 执行顺序

#### Step 1: 复现问题

- **写调试脚本** → `scripts/debug/debug_{issue}.py`
- **最小复现**：提取最小输入数据集
- **记录现象**：预期 vs 实际

#### Step 2: 定位根因

**两个方向**:

**A. 规格理解错了**:
- 回查 `spec/MALF_V2_1_AUTHORITY_REFERENCE.md`
- 检查 `spec/IMPLEMENTATION-CONTRACT-PATCH.md` 是否有闭合
- 如果规格确实模糊：
  - 记录到 `BUILD-PLAN.md` "已知空白"
  - 或记录到 `IMPLEMENTATION-CONTRACT-PATCH.md` 待闭合

**B. 实现有 bug**:
- 确认违反了哪条不变量（如 R2、O3）
- 确认是逻辑错误还是边界条件

#### Step 3: 修复

1. **写回归测试**（先 RED）
   - `tests/test_{module}.py` 加测试用例
   - 用触发 bug 的最小输入
2. **改实现**（GREEN）
3. **跑全量测试** → `pytest`
4. **真实数据重跑** → `scripts/verify/*.py`

#### Step 4: 记录

- **修复记录** → `docs/reports/validation/VALIDATION-FIXES.md`
  - 记录：触发条件、根因、修复方式、影响范围
- **更新 BUILD-PLAN.md**：勾选对应 step 或标注"已修复"

---

## 📚 任务类型 D：文档整理

**触发词**: "更新文档"、"整理归档"、"加导航"

### 执行顺序

#### Step 1: 确认文档分类

| 目录 | 放什么 | 更新频率 |
|------|--------|----------|
| `spec/` | 规格定义、合同、补丁 | 几乎不变 |
| `guide/` | 用户手册、API 参考 | 功能更新时 |
| `dev/` | 开发计划、工作流程 | **每天** |
| `reports/` | 验证报告、修复记录 | 里程碑时 |
| `archive/` | 历史任务、完成报告 | 任务完成时 |

#### Step 2: 执行整理

**原则**:
- 已完成任务 → 移到 `archive/tasks/{TASK}/`
- 新文档 → 按分类放到对应目录
- 不删除历史文档（只归档）

#### Step 3: 更新索引

**必更新**:
- [ ] `00-INDEX.md` 目录树
- [ ] `00-INDEX.md` "常见问题"（如果加了新文档类型）

**视情况更新**:
- [ ] `README.md`（如果影响用户）
- [ ] `CLAUDE.md`（如果影响开发流程）

---

## ⚠️ 禁止事项速查（从 CLAUDE.md 提取）

### 代码层面

- ❌ 领域核心（`src/malf/`）加外部依赖（numpy、pandas、pydantic）
- ❌ 价格用 `float`（必须用 `int`）
- ❌ 没有 golden fixture 就写实现
- ❌ 实现推测性功能（只做 fixture 驱动的部分）
- ❌ 对 pivot 排序/重排（调用方保证顺序）

### 文档层面

- ❌ 在文档里复述规格内容（只能指向规格）
- ❌ 规格模糊时猜测行为（应记录"待确认"）
- ❌ 直接改 `MALF_V2_1_AUTHORITY_REFERENCE.md`（修订走补丁）
- ❌ 删除历史文档（只归档，不删除）

### 规格层面

- ❌ 未确认就闭合第 3、4 层缺口（消歧 + 立法需拍板）
- ❌ 创建数据适配器、viewer、产品功能（属于 RiskBench，不属于引擎）

---

## ✅ 完成任务后的检查清单

### 通用检查（所有任务）

- [ ] `BUILD-PLAN.md` 对应 step 已勾选或标注
- [ ] 如果改了文档结构，`00-INDEX.md` 已更新

### 代码任务额外检查

- [ ] `pytest` 全绿（允许 1 skipped）
- [ ] Golden fixture 已提交（不是代码生成的）
- [ ] `CLAUDE.md` "实现状态"已更新
- [ ] 如果是关键功能，真实数据验证已完成

### 规格任务额外检查

- [ ] `IMPLEMENTATION-CONTRACT-PATCH.md` 已标注闭合状态
- [ ] 第 3、4 层缺口已获用户确认
- [ ] 未改动 `MALF_V2_1_AUTHORITY_REFERENCE.md`（修订走补丁）

### 调试任务额外检查

- [ ] 回归测试已添加（先 RED 后 GREEN）
- [ ] `VALIDATION-FIXES.md` 已记录修复
- [ ] 全量测试通过 + 真实数据重跑通过

---

## 🔄 文档维护

### 何时更新本文件

- 发现流程不清晰或步骤遗漏时
- 新增任务类型时
- 检查清单需要补充时
- 禁止事项有变化时

### 更新原则

- 保持"执行顺序"的顺序性（Step 1/2/3）
- 用表格 + 检查清单提升可读性
- 善用 emoji 提升导航性（但不过度）
- 每次更新后更新顶部"版本"日期

---

## 📞 常见问题

### Q: 规格模糊怎么办？
**A**: 
1. 先查 `IMPLEMENTATION-CONTRACT-PATCH.md` 看是否已闭合
2. 如果未闭合且属于第 3、4 层（消歧 + 立法），**停止**，询问用户
3. 不要猜测，记录"待确认"

### Q: 测试失败了但我觉得规格错了？
**A**: 
1. 回查规格原文（不是你的理解）
2. 查补丁是否有闭合
3. 如果确信规格有歧义，记录到 `BUILD-PLAN.md` 或 `IMPLEMENTATION-CONTRACT-PATCH.md`
4. 询问用户确认

### Q: 要不要写某个功能？
**A**: 
1. 查 `BUILD-PLAN.md` 是否在当前 step 清单里
2. 如果不在，查 `BUILD-CONTRACT.md §3 非目标` 是否明确排除
3. 如果模糊，询问用户

### Q: 文档该放哪个目录？
**A**: 
- 规格/合同 → `spec/`
- 用户手册 → `guide/`
- 开发指南 → `dev/`
- 验证报告 → `reports/`
- 已完成任务 → `archive/tasks/{TASK}/`

---

**最后更新**: 2026-07-27  
**维护者**: 每次流程不清晰时更新本文件
