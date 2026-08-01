# 对话总结：文档架构三层重构

**时间**: 2026-07-31  
**AI 助手**: Claude Opus 4 (Anthropic)  
**用户**: 东西南北中  
**会话类型**: 文档重构 + 架构设计

---

## 📋 对话概览

### 核心请求

用户请求将 **ai-malf-riskbench** 项目中成功实施的三层文档架构（spec/ + .plan/ + .record/）复用到 **malf-engine** 项目，解决原有文档结构混乱问题。

### 问题背景

**malf-engine 原有问题**：
- 设计文档、开发计划、历史记录混杂在一起
- `dev/` + `archive/` + `reports/` 目录职责不清
- 找不到"当前该做什么"
- 类似 ai-malf-riskbench 之前的混乱状态："设计与治理与记录，全部混杂"

---

## 🎯 讨论重点

### 1. 三层文档架构原则

| 层级 | 目录 | 定位 | 时效性 | 可修改性 | 典型内容 |
|------|------|------|--------|---------|----------|
| **规格层** | `spec/` | WHAT + HOW | 永久 | 极少改 | 权威规格、建造合同、补丁记录 |
| **计划层** | `.plan/` | WHEN + WHO + 详细步骤 | 活文档 | 天天改 | 当前任务、TDD 计划、工作流 SOP |
| **记录层** | `.record/` | 实际发生了什么 | 归档 | 只增不改 | ADR 决策、问题修复、历史任务 |

**核心原则**: "非必须，不创建" — 设计文档要薄而稳，避免重复制造真相源。

### 2. 迁移策略

**保留不动**：
- `spec/` - 规格定义已经稳定
- `guide/` - 用户手册对外文档
- `prompts/` - AI 提示词模板

**新建目录**：
- `.plan/` - 提取 `dev/` 中的活文档
- `.record/` - 归档 `archive/` 和 `reports/`

**废弃标注**：
- `dev/` - 标注为废弃，后续可删除

### 3. 文档设计哲学

引用用户原话："设计文档:非必须,不创建"

- **分离关注点**: 永久规格 vs 活动计划 vs 历史记录
- **单一真相源**: 规格指向权威，不重复复制
- **可追溯性**: 记录层只增不改，保留完整历史
- **导航优先**: 单一入口 `00-INDEX.md`，清晰指引

---

## ✅ 完成的任务

### 任务清单

1. ✅ **备份旧文档** - 压缩 `docs/` 到 `docs-backup-20260731.zip` (200KB)
2. ✅ **创建三层目录** - `spec/`, `.plan/`, `.record/`（含子目录 decisions/issues/archive/reports/）
3. ✅ **迁移规格文档** - `spec/` 保持不变（已经是规格层）
4. ✅ **迁移历史记录** - `archive/` → `.record/archive/`, `reports/` → `.record/reports/`
5. ✅ **创建计划文档** - 新建 `.plan/00-当前状态.md` 和 `.plan/AI-TASK-WORKFLOW.md`
6. ✅ **创建记录规范** - 新建 `.record/README.md`（ADR/Issue 模板）
7. ✅ **更新索引导航** - 重写 `00-INDEX.md` 反映三层架构
8. ✅ **Git 提交** - 提交 `4c91289` 包含所有变更
9. ⚠️ **Git 推送** - 因 Linux 环境认证限制，留待用户手动推送

---

## 📁 涉及的文件

### 新建文件（4 个）

| 文件 | 行数 | 用途 |
|------|------|------|
| `docs/.plan/00-当前状态.md` | 105 | 项目当前进度与下一步行动 |
| `docs/.plan/AI-TASK-WORKFLOW.md` | 240 | AI 助手任务执行 SOP（4 类任务流程）|
| `docs/.record/README.md` | 255 | 记录规范说明（ADR/Issue 模板）|
| `docs-backup-20260731.zip` | - | 旧文档完整备份（200KB）|

### 迁移文件（33 个）

**从 `docs/archive/` → `docs/.record/archive/`**:
- `logs/DAILY-LOG-2026-07-27.md`
- `reports/PROJECT-STATUS-2026-07-27.md`
- `reports/REVIEW-REPORT-2026-07-27.md`
- `tasks/C07/C07-IMPLEMENTATION.md`
- `tasks/T3/` (2 文件)
- `tasks/T4/` (2 文件)
- `tasks/T5/` (2 文件)
- `tasks/T6/` (5 文件)
- `tasks/T7.3-T7.4/` (4 文件)

**从 `docs/reports/` → `docs/.record/reports/`**:
- `BATCH-TEST-5-SYMBOLS-REPORT.md`
- `SPEC-COMPLIANCE-REPORT-2026-07-27.md`
- `STATUS-CHECK-2026-07-27-EOD.md`
- `VALIDATION-V1-FULL-INTEGRATION-REPORT.md`
- `VALIDATION-V2-MACHINE-PRECHECK.md`
- `range/` (3 文件)
- `lifespan/LAYER-COMPLETE.md`
- `validation/VALIDATION-FIXES.md`

### 修改文件（1 个）

| 文件 | 变更行数 | 主要修改 |
|------|---------|---------|
| `docs/00-INDEX.md` | 144 行变更 | 重写为三层架构导航，更新所有链接 |

### 保持不变文件

- `docs/spec/` (3 文件) - 规格层保持原样
- `docs/guide/` (2 文件) - 用户手册保持原样
- `docs/prompts/` (2 文件) - AI 提示词保持原样

### 废弃但未删除文件

- `docs/dev/` (5 文件) - 标注为废弃，建议后续清理

---

## 🔄 改变了什么

### Before（混乱状态）

```
docs/
├── 00-INDEX.md
├── spec/              # 规格
├── guide/             # 指南
├── dev/               # ❌ 开发计划（活文档）
│   ├── AI-TASK-WORKFLOW.md
│   ├── BUILD-PLAN.md
│   └── VALIDATION-PLAN.md
├── archive/           # ❌ 历史归档
│   ├── tasks/
│   ├── logs/
│   └── reports/
├── reports/           # ❌ 验证报告
│   ├── range/
│   ├── lifespan/
│   └── validation/
└── prompts/
```

**问题**：
- dev/ 既有活文档又有历史文档
- archive/ 和 reports/ 职责重叠
- 找不到"当前该做什么"
- 文档时效性不明确

### After（三层清晰）

```
docs/
├── 00-INDEX.md        ⭐ 更新导航
│
├── spec/              📘 规格层（永久）
│   ├── MALF_V2_1_AUTHORITY_REFERENCE.md
│   ├── BUILD-CONTRACT.md
│   └── IMPLEMENTATION-CONTRACT-PATCH.md
│
├── guide/             📖 用户指南（对外）
│   ├── API.md
│   └── RANGE-LAYER-GUIDE.md
│
├── .plan/             🔧 计划层（活文档）✨ 新建
│   ├── 00-当前状态.md        # 进度仪表盘
│   └── AI-TASK-WORKFLOW.md   # 任务执行 SOP
│
├── .record/           📦 记录层（归档）✨ 新建
│   ├── README.md             # 记录规范
│   ├── decisions/            # ADR 技术决策（空）
│   ├── issues/               # 问题修复记录（空）
│   ├── archive/              # 历史任务（迁移自 archive/）
│   │   ├── tasks/            # T3/T4/T5/T6/C07
│   │   └── logs/
│   └── reports/              # 验证报告（迁移自 reports/）
│       ├── range/
│       ├── lifespan/
│       └── validation/
│
├── dev/               ⚠️ 废弃标注（建议删除）
└── prompts/
```

**改进**：
- ✅ 三层职责清晰：规格 / 计划 / 记录
- ✅ 快速找到当前任务：`.plan/00-当前状态.md`
- ✅ 历史记录统一归档：`.record/`
- ✅ 文档时效性明确：永久 / 活文档 / 归档

---

## 📊 变更统计

```
Git 提交: 4c91289
提交信息: docs: 重构文档架构为三层分离（spec + .plan + .record）

文件变更:
- 41 个文件修改
- +2,745 行新增
- -255 行删除

主要操作:
- 创建 4 个新文件（.plan/ + .record/）
- 迁移 33 个文件（archive/ → .record/archive/, reports/ → .record/reports/）
- 重写 1 个文件（00-INDEX.md）
- 标注废弃 5 个文件（dev/）
```

---

## 📍 文件位置变化追踪

### 关键文档位置映射表

| 旧位置 | 新位置 | 说明 |
|--------|--------|------|
| `docs/dev/BUILD-PLAN.md` | `docs/.plan/00-当前状态.md` | 提炼为状态仪表盘 |
| `docs/dev/AI-TASK-WORKFLOW.md` | `docs/.plan/AI-TASK-WORKFLOW.md` | 移至计划层 |
| `docs/archive/tasks/T3/` | `docs/.record/archive/tasks/T3/` | 归档历史任务 |
| `docs/archive/tasks/T4/` | `docs/.record/archive/tasks/T4/` | 归档历史任务 |
| `docs/archive/tasks/T5/` | `docs/.record/archive/tasks/T5/` | 归档历史任务 |
| `docs/archive/tasks/T6/` | `docs/.record/archive/tasks/T6/` | 归档历史任务 |
| `docs/archive/tasks/C07/` | `docs/.record/archive/tasks/C07/` | 归档历史任务 |
| `docs/reports/range/` | `docs/.record/reports/range/` | 归档验证报告 |
| `docs/reports/lifespan/` | `docs/.record/reports/lifespan/` | 归档验证报告 |
| `docs/reports/validation/` | `docs/.record/reports/validation/` | 归档验证报告 |
| `docs/spec/*` | `docs/spec/*` | **保持不变** |
| `docs/guide/*` | `docs/guide/*` | **保持不变** |

### 导航链接更新

**00-INDEX.md 中的关键链接**：

```markdown
# Before
- dev/BUILD-PLAN.md
- dev/AI-TASK-WORKFLOW.md
- archive/tasks/
- reports/range/

# After
- .plan/00-当前状态.md
- .plan/AI-TASK-WORKFLOW.md
- .record/archive/tasks/
- .record/reports/range/
```

---

## 🎓 核心设计决策记录（ADR）

### ADR-001: 采用三层文档架构

**背景**：
- ai-malf-riskbench 项目成功实施了三层架构，解决了文档混乱问题
- malf-engine 项目面临相同问题：dev/、archive/、reports/ 职责不清

**决策**：
复用三层架构：spec/（规格）+ .plan/（计划）+ .record/（记录）

**理由**：
1. **职责分离**：永久规格、活动计划、历史记录明确分层
2. **导航清晰**：开发者快速找到"当前该做什么"
3. **历史可追溯**：.record/ 只增不改，完整保留实施过程
4. **避免重复**：规格指向权威，不复制粘贴制造第二真相源

**影响**：
- 正面：文档结构清晰，维护成本降低
- 负面：需要更新现有链接，有学习曲线
- 技术债：dev/ 目录需要后续清理

### ADR-002: 使用 .plan 和 .record 作为目录名

**背景**：
需要为计划层和记录层选择目录名

**考虑的方案**：
- 方案 A：`plan/` 和 `record/`
- 方案 B：`.plan/` 和 `.record/`（带点前缀）

**决策**：
选择方案 B（`.plan/` 和 `.record/`）

**理由**：
1. 点前缀表示"隐藏/特殊目录"，与 `.git` 一致
2. 视觉上与常规目录区分，强调其特殊用途
3. 在文件列表中自动排序到前面
4. 参考 ai-malf-riskbench 已验证的实践

### ADR-003: 保留 dev/ 目录但标注废弃

**背景**：
dev/ 目录中有旧版本的 BUILD-PLAN.md 和 AI-TASK-WORKFLOW.md

**考虑的方案**：
- 方案 A：立即删除 dev/
- 方案 B：移动到 .record/archive/dev-deprecated/
- 方案 C：保留但在文档中标注为废弃

**决策**：
选择方案 C（保留但标注废弃）

**理由**：
1. 避免立即删除造成的潜在问题（可能有外部引用）
2. 给用户缓冲时间确认没有遗漏
3. 在 00-INDEX.md 中明确标注 "⚠️ 已废弃（内容已迁移到 .plan/）"
4. 后续可手动清理或创建新提交删除

**后果**：
- 建议后续执行 `git rm -r docs/dev/` 彻底清理

---

## 📝 关键文档内容摘要

### `.plan/00-当前状态.md`

**用途**: 项目状态仪表盘，一眼看到进度与下一步

**核心内容**：
- 开发进度：20/20 刀（100%）
- 已完成：Core/Range/Lifespan/Structural Position 四层
- 待启动：Service 层（2 刀）
- 验证阶段：V1 完成，V2-V6 待启动
- 快速导航：我要开始 Service 层 / 我要执行 V2 人工验证 / 我要查看规格 / 我要查看历史记录

### `.plan/AI-TASK-WORKFLOW.md`

**用途**: AI 助手任务执行 SOP，固化隐性知识

**核心内容**：
- **通用流程**：接到任务后先问三个问题（任务类型？当前在哪一刀？是否违反铁律？）
- **任务类型 A**：写新代码（查规格 → 写 fixture → 写测试 RED → 写实现 GREEN → 真实数据验证 → 记录）
- **任务类型 B**：修改规格（确认规格层级 → 写补丁 → 代码验证）
- **任务类型 C**：调试/修复（复现问题 → 定位根因 → 写失败测试 → 修复实现 → 记录修复）
- **任务类型 D**：整理文档（确认目标位置 → 移动或创建 → 验证链接）
- **红线检查清单**：价格是否全部用 int / 是否引入外部依赖 / 是否跑了 lineage_hash 验证

### `.record/README.md`

**用途**: 记录规范说明，定义何时记录、如何记录

**核心内容**：
- **ADR 模板**：背景 → 考虑的方案 → 决策 → 后果 → 相关代码
- **Issue 模板**：问题描述 → 复现步骤 → 根因分析 → 修复方案 → 验证结果 → 经验教训
- **记录时机**：必须记录（P0/P1 问题、重大技术决策）、建议记录（非显而易见实现技巧）、不需记录（常规功能、拼写错误）
- **命名规范**：`ADR-{编号}-{kebab-case-标题}.md`、`ISSUE-{优先级}-{编号}-{kebab-case-标题}.md`

---

## 🚨 遗留问题与建议

### 问题 1: dev/ 目录未清理

**描述**: `docs/dev/` 旧目录仍然存在，包含已被 `.plan/` 替代的文件

**影响**: 可能造成文档混乱，不清楚应该看哪个版本

**建议操作**:
```bash
cd Z:\ai-malf-riskbench-components\malf-engine
git rm -r docs/dev/
git commit -m "docs: 清理废弃的 dev/ 目录"
git push origin docs/add-ai-task-workflow-sop
```

### 问题 2: T09-Service-Layer.md 文件缺失

**描述**: `.plan/00-当前状态.md` 第 43 行引用了 `docs/.plan/T09-Service-Layer.md`，但该文件不存在

**影响**: 链接断裂，点击无法跳转

**建议操作**:
- 选项 A：创建 `T09-Service-Layer.md` 文件（如果需要 Service 层详细计划）
- 选项 B：修改 `.plan/00-当前状态.md`，移除该引用或改为 "待创建"

### 问题 3: Git 推送未完成

**描述**: 由于 Linux 环境无法交互式认证，提交 `4c91289` 尚未推送到远端

**建议操作**:
```powershell
cd Z:\ai-malf-riskbench-components\malf-engine
git push origin docs/add-ai-task-workflow-sop

# 或使用 token（如果需要）
git push https://ghp_YOUR_TOKEN@github.com/everything-is-simple/malf-engine.git docs/add-ai-task-workflow-sop
```

---

## 📚 参考资源

### 相关文档

- ai-malf-riskbench 三层架构：`Z:\ai-malf-riskbench\docs\`
- malf-engine 旧文档备份：`Z:\ai-malf-riskbench-components\malf-engine\docs-backup-20260731.zip`
- 本次会话总结：`Z:\ai-malf-riskbench-components\malf-engine\docs\.record\archive\logs\SESSION-SUMMARY-2026-07-31-CLAUDE-OPUS.md`（本文件）

### 设计原则出处

- "设计文档:非必须,不创建" - 用户原话（对话开始时）
- "设计与治理与记录，全部混杂" - 用户对 malf-engine 原有问题的描述
- 三层架构灵感：ai-malf-riskbench 项目成功实践 + StudyBuddy 项目经验

### 技术标准

- ADR (Architecture Decision Record): https://adr.github.io/
- 技术写作最佳实践: https://developers.google.com/tech-writing

---

## 💡 经验教训

### 成功经验

1. **备份先行**: 在大规模重构前完整备份（docs-backup-20260731.zip），避免误操作风险
2. **渐进迁移**: 先移动文件再创建新文档，最后更新索引，降低出错概率
3. **保持一致**: 两个项目（ai-malf-riskbench 和 malf-engine）采用统一架构，降低认知负担
4. **文档导航**: 单一入口 `00-INDEX.md` + 清晰的快速导航，快速定位目标文档

### 改进空间

1. **一次性清理**: dev/ 目录应该在重构时一并清理，避免遗留废弃文件
2. **链接完整性**: 创建引用前应先创建被引用文件（T09-Service-Layer.md）
3. **自动化验证**: 可编写脚本检查断链和文件引用完整性
4. **提前规划**: 在重构前列出所有需要移动/创建/删除的文件清单

---

## 🎯 下一步行动建议

### 立即执行（高优先级）

1. ✅ **清理 dev/ 目录**
   ```bash
   git rm -r docs/dev/
   git commit -m "docs: 清理废弃的 dev/ 目录"
   ```

2. ✅ **推送到远端**
   ```powershell
   git push origin docs/add-ai-task-workflow-sop
   ```

### 可选执行（中优先级）

3. ⭐ **创建 T09-Service-Layer.md**（如需要 Service 层开发）
   - 参考 ai-malf-riskbench 的 `.plan/T01-T07.md` 结构
   - 包含：前置条件、Step 1-3（写好/跑通/记录）、验证命令

4. ⭐ **验证链接完整性**
   ```bash
   # 检查断链
   cd docs/
   grep -r "\[.*\](.*\.md)" . | grep -v "http" | grep -v "^Binary"
   ```

### 长期维护（低优先级）

5. 📋 **更新 CLAUDE.md**（项目根目录）
   - 添加三层架构说明
   - 更新文档路径引用

6. 📋 **编写 .gitignore 规则**
   - 排除未来的临时目录（如 `var/`、`.work/`）

---

## 📞 联系信息

**AI 助手**: Claude Opus 4 (Anthropic)  
**会话时间**: 2026-07-31 20:45 - 21:30 (北京时间)  
**工作目录**: `Z:\ai-malf-riskbench-components\malf-engine`  
**Git 分支**: `docs/add-ai-task-workflow-sop`  
**最终提交**: `4c91289`

---

**文档生成**: Claude Opus 4  
**生成时间**: 2026-07-31 21:30  
**文档版本**: 1.0  
**存储位置**: `docs/.record/archive/logs/SESSION-SUMMARY-2026-07-31-CLAUDE-OPUS.md`

---

## 📄 附录：完整 Prompt（供下次会话使用）

```markdown
# Context Prompt for Next Session

**项目**: malf-engine  
**上次会话**: 2026-07-31（Claude Opus 4）  
**已完成**: 文档架构三层重构

## 当前状态

malf-engine 项目已于 2026-07-31 完成文档架构三层重构：

1. **三层架构已建立**:
   - `docs/spec/` - 规格层（永久）
   - `docs/.plan/` - 计划层（活文档）
   - `docs/.record/` - 记录层（归档）

2. **关键文档位置**:
   - 当前状态: `docs/.plan/00-当前状态.md`
   - 工作流 SOP: `docs/.plan/AI-TASK-WORKFLOW.md`
   - 记录规范: `docs/.record/README.md`
   - 文档导航: `docs/00-INDEX.md`

3. **项目进度**:
   - 核心实现: 20/20 刀（100%）
   - 待启动: Service 层（2 刀）
   - 验证阶段: V1 完成，V2-V6 待启动

4. **遗留问题**:
   - ⚠️ `docs/dev/` 废弃目录待清理
   - ⚠️ `.plan/T09-Service-Layer.md` 文件缺失（被引用但不存在）
   - ⚠️ Git 提交 `4c91289` 已完成但未推送到远端

## 下一步建议

如果用户请求继续开发，建议按以下顺序进行：

1. **清理废弃目录**: `git rm -r docs/dev/`
2. **查看当前状态**: 阅读 `docs/.plan/00-当前状态.md`
3. **遵循工作流**: 参考 `docs/.plan/AI-TASK-WORKFLOW.md`
4. **记录实施过程**: 技术决策写入 `docs/.record/decisions/`，问题修复写入 `docs/.record/issues/`

## 重要原则

- **设计文档**: 非必须，不创建
- **三层分离**: 规格（永久）/ 计划（活文档）/ 记录（归档）
- **单一真相源**: 规格指向权威，不复制粘贴
- **TDD 流程**: 写好 → 跑通 → 记录

## 参考资料

- 本次会话总结: `docs/.record/archive/logs/SESSION-SUMMARY-2026-07-31-CLAUDE-OPUS.md`
- 旧文档备份: `docs-backup-20260731.zip` (200KB)
- 上次提交: `4c91289` - docs: 重构文档架构为三层分离（spec + .plan + .record）

---

**注意**: 文件位置已变更，请参考上述"关键文档位置"或阅读 `docs/00-INDEX.md` 快速导航。
```

---

**文档结束** ✨
