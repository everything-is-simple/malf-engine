# malf-engine 文档导航

**版本**: 2026-07-26  
**目的**: 这是唯一的文档入口，告诉你应该看哪个文档

---

## 🚀 快速导航

### 我是新手，想了解项目
👉 **先看**: [`../README.md`](../README.md) - 项目概述  
👉 **然后**: [`guide/API.md`](guide/API.md) - API 参考

### 我要继续开发 ⭐
👉 **主文档**: [`dev/BUILD-PLAN.md`](dev/BUILD-PLAN.md) - 当前开发计划（活文档）  
👉 **开发指引**: [`../CLAUDE.md`](../CLAUDE.md) - AI 助手工作指引  
👉 **规格查询**: [`spec/MALF_V2_1_AUTHORITY_REFERENCE.md`](spec/MALF_V2_1_AUTHORITY_REFERENCE.md)

### 我要查看验证报告
👉 **Range 层验证**: [`reports/range/RANGE-REAL-DATA-VALIDATION-COMPLETE.md`](reports/range/RANGE-REAL-DATA-VALIDATION-COMPLETE.md)  
👉 **修复记录**: [`reports/validation/VALIDATION-FIXES.md`](reports/validation/VALIDATION-FIXES.md)

### 我要查看历史任务
👉 **任务归档**: [`archive/tasks/`](archive/tasks/) - 按任务编号（T3/T4/T5/T6/C07）组织

---

## 📁 目录结构说明

```
docs/
├── 00-INDEX.md              ⭐ 本文件：文档导航入口
│
├── spec/                    📘 规格与合同（权威，极少变动）
│   ├── MALF_V2_1_AUTHORITY_REFERENCE.md     # MALF v2.1 权威规格
│   ├── BUILD-CONTRACT.md                    # 建造合同（范围/验收线）
│   └── IMPLEMENTATION-CONTRACT-PATCH.md     # 实现合同补丁
│
├── guide/                   📖 用户指南（对外文档）
│   ├── API.md                               # CoreStateSnapshot 字段参考
│   └── RANGE-LAYER-GUIDE.md                 # Range 层使用指南
│
├── dev/                     🔧 开发指南（当前工作）⭐
│   ├── BUILD-PLAN.md                        # 当前开发计划（活文档）
│   ├── C07-RULE-ANALYSIS.md                 # C-07 规则分析
│   └── REVISION-CHECKLIST.md                # 修订检查清单
│
├── reports/                 📊 验证与报告
│   ├── range/                               # Range 层验证报告
│   │   ├── RANGE-REAL-DATA-REPORT.md
│   │   ├── RANGE-REAL-DATA-VALIDATION-COMPLETE.md
│   │   └── RANGE-REAL-DATA-VALIDATION-PLAN.md
│   └── validation/                          # 验证修复记录
│       └── VALIDATION-FIXES.md
│
└── archive/                 📦 历史归档（已完成工作）
    ├── tasks/                               # 任务完成报告（按任务编号）
    │   ├── T3/                              # 第三刀：Same-direction Break
    │   ├── T4/                              # 第四刀：Transition Candidate
    │   ├── T5/                              # 第五刀：Guard/Progress Update
    │   ├── T6/                              # 第六刀：Range Layer
    │   └── C07/                             # C-07 补丁：Pivot 替换
    ├── logs/                                # 日志归档
    └── summaries/                           # 总结归档
```

---

## 📋 文档用途分类

| 目录 | 用途 | 目标读者 | 更新频率 | 示例 |
|------|------|----------|---------|------|
| **`spec/`** | 规格定义与合同 | 开发者 | 几乎不变 | 查 D18 定义 |
| **`guide/`** | 使用手册 | 用户/开发者 | 功能更新时 | 如何使用 API |
| **`dev/`** ⭐ | 开发指南 | 开发者 | **每天** | 下一步做什么 |
| **`reports/`** | 验证报告 | 质量团队 | 里程碑时 | Range 层验证结果 |
| **`archive/`** | 历史记录 | 参考 | 任务完成时 | T3 如何实现的 |

---

## 🎯 常见问题

### Q: 我要开始新功能，从哪里开始？
**A**: 
1. 阅读 [`dev/BUILD-PLAN.md`](dev/BUILD-PLAN.md) 了解当前进度
2. 查看 [`spec/BUILD-CONTRACT.md`](spec/BUILD-CONTRACT.md) 确认验收标准
3. 参考 [`archive/tasks/`](archive/tasks/) 中相关任务的实现方式

### Q: 规格中的某个编号（如 D18）在哪里？
**A**: 查看 [`spec/MALF_V2_1_AUTHORITY_REFERENCE.md`](spec/MALF_V2_1_AUTHORITY_REFERENCE.md)

### Q: CoreStateSnapshot 的字段含义是什么？
**A**: 查看 [`guide/API.md`](guide/API.md)

### Q: 如何使用 Range 层功能？
**A**: 查看 [`guide/RANGE-LAYER-GUIDE.md`](guide/RANGE-LAYER-GUIDE.md)

### Q: 历史任务（如 T3、T4）的实现细节在哪里？
**A**: 查看 [`archive/tasks/T*/`](archive/tasks/) 对应目录

### Q: 真实数据验证结果在哪里？
**A**: 查看 [`reports/range/RANGE-REAL-DATA-VALIDATION-COMPLETE.md`](reports/range/RANGE-REAL-DATA-VALIDATION-COMPLETE.md)

---

## 🔄 文档更新原则

### 活文档（频繁更新）
- ⭐ **`dev/BUILD-PLAN.md`** - 每次完成一个 step 勾一个

### 稳定文档（极少更新）
- `spec/BUILD-CONTRACT.md` - 只在重大决策时更新
- `spec/MALF_V2_1_AUTHORITY_REFERENCE.md` - 只在规格变更时更新

### 里程碑文档（任务完成时更新）
- `guide/*` - 功能完成后更新
- `reports/*` - 验证完成后记录
- `archive/tasks/*` - 任务完成时归档

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
- 任务完成后文档移至 `archive/tasks/{TASK}/`
- 保留完整的历史记录，不删除
- 按时间顺序组织（最新的在前）

---

## 🛠️ 工具脚本

**位置**: `../scripts/`

- **`debug/`** - 调试脚本（debug_*.py）
- **`verify/`** - 验证脚本（verify_*.py, test_*.py）
- **`analyze/`** - 分析脚本（analyze_*.py）

**使用方式**: 
```bash
/d/miniconda/py310/python.exe scripts/debug/debug_c07_3.py
```

---

## 📌 项目状态（2026-07-26）

**当前版本**: v2.1 with C-07  
**测试状态**: 58 passed, 1 skipped  
**开发重心**: 产品化增强（序列化、性能优化）

**完成里程碑**:
- ✅ Core 层（第一~五刀）
- ✅ C-07 补丁（Pivot 替换）
- ✅ Range 层（第六刀）
- ✅ 真实数据验证

**详细状态**: 查看 [`dev/BUILD-PLAN.md`](dev/BUILD-PLAN.md)

---

**文档维护**: 每次项目重大变更时更新本文件
**最后更新**: 2026-07-26（项目重组）
