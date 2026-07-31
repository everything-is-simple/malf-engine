# malf-engine 文档导航

**版本**: 2026-07-31  
**目的**: 这是唯一的文档入口，告诉你应该看哪个文档

---

## 🏗️ 三层文档架构

malf-engine 采用三层分离的文档架构，避免设计、计划、记录混杂：

| 层级 | 目录 | 定位 | 时效性 | 可修改 |
|------|------|------|--------|--------|
| **规格层** | `spec/` | WHAT + HOW | 永久 | 极少改 |
| **计划层** | `.plan/` | WHEN + WHO + 详细步骤 | 活文档 | 天天改 |
| **记录层** | `.record/` | 实际发生了什么 | 归档 | 只增不改 |

---

## 🚀 快速导航

### 我是新手，想了解项目
👉 **项目概述**: [`../README.md`](../README.md)  
👉 **API 参考**: [`guide/API.md`](guide/API.md)  
👉 **开发指引**: [`../CLAUDE.md`](../CLAUDE.md)

### 我要继续开发 ⭐
👉 **当前状态**: [`.plan/00-当前状态.md`](.plan/00-当前状态.md) - 进度与下一步  
👉 **工作流程**: [`.plan/AI-TASK-WORKFLOW.md`](.plan/AI-TASK-WORKFLOW.md) - 任务执行 SOP  
👉 **规格查询**: [`spec/MALF_V2_1_AUTHORITY_REFERENCE.md`](spec/MALF_V2_1_AUTHORITY_REFERENCE.md)

### 我要查看规格
👉 **权威引用**: [`spec/MALF_V2_1_AUTHORITY_REFERENCE.md`](spec/MALF_V2_1_AUTHORITY_REFERENCE.md)  
👉 **建造合同**: [`spec/BUILD-CONTRACT.md`](spec/BUILD-CONTRACT.md) - 范围与验收线  
👉 **实现补丁**: [`spec/IMPLEMENTATION-CONTRACT-PATCH.md`](spec/IMPLEMENTATION-CONTRACT-PATCH.md)

### 我要查看实施记录
👉 **技术决策**: [`.record/decisions/`](.record/decisions/) - ADR 记录  
👉 **问题修复**: [`.record/issues/`](.record/issues/) - Bug 修复记录  
👉 **历史任务**: [`.record/archive/tasks/`](.record/archive/tasks/) - 按任务编号（T3/T4/T5/T6）  
👉 **验证报告**: [`.record/archive/reports/`](.record/archive/reports/)

---

## 📁 目录结构

```
docs/
├── 00-INDEX.md                  ⭐ 本文件：文档导航入口
│
├── spec/                        📘 规格层（永久，极少变动）
│   ├── MALF_V2_1_AUTHORITY_REFERENCE.md     # MALF v2.1 权威规格
│   ├── BUILD-CONTRACT.md                    # 建造合同（范围/验收线）
│   └── IMPLEMENTATION-CONTRACT-PATCH.md     # 实现合同补丁
│
├── guide/                       📖 用户指南（对外文档）
│   ├── API.md                               # WaveStructuralSnapshot 字段参考
│   └── RANGE-LAYER-GUIDE.md                 # Range 层使用指南
│
├── .plan/                       🔧 计划层（活文档）⭐
│   ├── 00-当前状态.md                        # 当前进度与下一步
│   └── AI-TASK-WORKFLOW.md                  # AI 助手任务执行 SOP
│
├── .record/                     📦 记录层（只增不改）
│   ├── README.md                            # 记录规范说明
│   ├── decisions/                           # 技术决策记录（ADR）
│   ├── issues/                              # 问题修复记录
│   ├── archive/                             # 历史任务归档
│   │   ├── tasks/                           # T3/T4/T5/T6/C07 任务记录
│   │   └── logs/                            # 日志归档
│   └── reports/                             # 验证报告归档
│       ├── range/                           # Range 层验证报告
│       ├── lifespan/                        # Lifespan 层验证报告
│       └── validation/                      # 修复验证记录
│
├── dev/                         ⚠️ 已废弃（内容已迁移到 .plan/）
└── prompts/                     💡 AI 提示词模板
```

---

## 📋 文档用途分类

| 目录 | 用途 | 目标读者 | 更新频率 | 示例 |
|------|------|----------|---------|------|
| **`spec/`** | 规格定义与合同 | 开发者 | 几乎不变 | 查 D18 定义 |
| **`guide/`** | 使用手册 | 用户/开发者 | 功能更新时 | 如何使用 API |
| **`.plan/`** ⭐ | 开发计划 | 开发者 | **每天** | 下一步做什么 |
| **`.record/`** | 实施记录 | 参考 | 完成时归档 | T3 如何实现的 |

---

## 🎯 常见问题

### Q: 我要开始新功能，从哪里开始？
**A**: 
1. 看 [`.plan/00-当前状态.md`](.plan/00-当前状态.md) 了解进度
2. 读 [`.plan/AI-TASK-WORKFLOW.md`](.plan/AI-TASK-WORKFLOW.md) 了解执行流程
3. 查 [`spec/BUILD-CONTRACT.md`](spec/BUILD-CONTRACT.md) 确认验收标准
4. 参考 [`.record/archive/tasks/`](.record/archive/tasks/) 相关任务的实现方式

### Q: 规格中的某个编号（如 D18）在哪里？
**A**: 查看 [`spec/MALF_V2_1_AUTHORITY_REFERENCE.md`](spec/MALF_V2_1_AUTHORITY_REFERENCE.md)

### Q: WaveStructuralSnapshot 的字段含义是什么？
**A**: 查看 [`guide/API.md`](guide/API.md)

### Q: 如何使用 Range 层功能？
**A**: 查看 [`guide/RANGE-LAYER-GUIDE.md`](guide/RANGE-LAYER-GUIDE.md)

### Q: 历史任务（如 T3、T4）的实现细节在哪里？
**A**: 查看 [`.record/archive/tasks/T*/`](.record/archive/tasks/)

### Q: 真实数据验证结果在哪里？
**A**: 查看 [`.record/archive/reports/range/RANGE-REAL-DATA-VALIDATION-COMPLETE.md`](.record/archive/reports/range/RANGE-REAL-DATA-VALIDATION-COMPLETE.md)

### Q: AI 助手接到任务后应该怎么做？
**A**: 查看 [`.plan/AI-TASK-WORKFLOW.md`](.plan/AI-TASK-WORKFLOW.md) - 按任务类型（写代码/修规格/调试/整理文档）有不同流程

### Q: 为什么某个技术决策是这样做的？
**A**: 查看 [`.record/decisions/`](.record/decisions/) - 技术决策记录（ADR）

### Q: 某个 bug 是怎么修复的？
**A**: 查看 [`.record/issues/`](.record/issues/) - 问题修复记录

---

## 🔄 文档更新原则

### 活文档（频繁更新）
- ⭐ **`.plan/00-当前状态.md`** - 每次完成一个 step 更新

### 稳定文档（极少更新）
- `spec/BUILD-CONTRACT.md` - 只在重大决策时更新
- `spec/MALF_V2_1_AUTHORITY_REFERENCE.md` - 只在规格变更时更新

### 归档文档（只增不改）
- `.record/decisions/` - 记录技术决策
- `.record/issues/` - 记录问题修复
- `.record/archive/` - 历史任务归档

---

## 📝 文档编写规范

### 标题规范
- 使用清晰的层级（h1/h2/h3）
- h1 只有一个（文档标题）
- 善用 emoji 提升可读性（但不过度）

### 链接规范
- 使用相对路径（如 `../README.md`）
- 文档间引用使用 markdown 链接
- 外部链接注明来源

### 归档规范
- 任务完成后关键决策移至 `.record/decisions/`
- 问题修复记录移至 `.record/issues/`
- 保留完整的历史记录，不删除

---

## 🛠️ 工具脚本

**位置**: `../scripts/`

- **`debug/`** - 调试脚本（debug_*.py）
- **`verify/`** - 验证脚本（verify_*.py, test_*.py）
- **`analyze/`** - 分析脚本（analyze_*.py）

**使用方式**: 
```bash
/d/miniconda/py310/python.exe scripts/verify/v1_full_integration_pipeline.py
```

---

## 📌 项目状态（2026-07-31）

**当前版本**: v2.1 with Structural Position  
**测试状态**: 89 passed, 2 skipped  
**规格合规度**: 95% (高度合规)  
**开发进度**: 20/20 刀（100%）

**完成里程碑**:
- ✅ Core 层（6 刀）
- ✅ Range 层（4 刀 + 真实数据验证）
- ✅ Lifespan 层（4 刀）
- ✅ Structural Position 层（4 刀）
- ✅ P0/P1 问题全部修复
- ⏸ Service 层待开发（2 刀）

**详细状态**: 查看 [`.plan/00-当前状态.md`](.plan/00-当前状态.md)

---

**文档维护**: 每次项目重大变更时更新本文件  
**最后更新**: 2026-07-31（文档架构重构为三层分离）
