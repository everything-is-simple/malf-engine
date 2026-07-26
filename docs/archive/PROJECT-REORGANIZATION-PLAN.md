# malf-engine 项目重组方案

**问题诊断**: 2026-07-26

## 当前混乱状态

### 1. 根目录污染（9个临时脚本）
```
./analyze_c07_3.py
./analyze_range_stats.py
./debug_c07_3.py
./debug_guard_break.py
./debug_t2.py
./debug_t3_fixture.py
./test_offset_0_real_data.py
./verify_t3.py
./verify_t3_fixed.py
```
**问题**: 调试脚本、验证脚本散落在根目录，没有组织

### 2. 文档目录混乱（44个文档）
**分类混乱**:
- 规格/合同类：BUILD-CONTRACT.md, IMPLEMENTATION-CONTRACT-PATCH.md, MALF_V2_1_AUTHORITY_REFERENCE.md
- 计划/进度类：BUILD-PLAN.md, T*-PROGRESS-SUMMARY.md
- 完成报告类：T3-COMPLETION-SUMMARY.md, T4-DELIVERY-SUMMARY.md, FINAL-SUMMARY-20260726.md
- 日志类：DAILY-LOG-*.md
- 用户文档类：API.md, RANGE-LAYER-GUIDE.md
- 实现指南类：T6-RANGE-IMPLEMENTATION-GUIDE.md, C07-RULE-ANALYSIS.md
- 验证报告类：RANGE-REAL-DATA-REPORT.md, VALIDATION-FIXES.md
- 任务文档类：T*-START-PROMPT.md, T*-DAY-*-PROMPT.md

**问题**: 没有层级结构，所有文档平铺，难以导航

### 3. 核心问题
**缺少明确的"指导系统开发"的入口文档**

---

## 重组方案

### 原则
1. **清晰的层级结构**：按用途分目录
2. **明确的入口文档**：开发者/用户一眼知道看哪个
3. **历史归档**：完成的任务文档归档，不删除
4. **工具脚本集中**：调试/验证脚本统一管理

---

## 新目录结构

```
malf-engine/
├── README.md                          # 项目入口（保持）
├── CLAUDE.md                          # AI 助手指引（保持）
├── CHANGELOG.md                       # 版本变更记录（新增）
│
├── src/malf/                          # 源代码（保持）
│
├── tests/                             # 测试（保持）
│   ├── fixtures/
│   └── test_*.py
│
├── scripts/                           # 新增：工具脚本目录
│   ├── debug/                         # 调试脚本
│   │   ├── debug_c07_3.py
│   │   ├── debug_guard_break.py
│   │   ├── debug_t2.py
│   │   └── debug_t3_fixture.py
│   ├── verify/                        # 验证脚本
│   │   ├── verify_t3.py
│   │   ├── verify_t3_fixed.py
│   │   └── test_offset_0_real_data.py
│   └── analyze/                       # 分析脚本
│       ├── analyze_c07_3.py
│       └── analyze_range_stats.py
│
└── docs/                              # 文档目录（重组）
    │
    ├── 00-INDEX.md                    # 新增：文档导航入口 ⭐
    │
    ├── spec/                          # 规格与合同（权威）
    │   ├── MALF_V2_1_AUTHORITY_REFERENCE.md
    │   ├── BUILD-CONTRACT.md
    │   └── IMPLEMENTATION-CONTRACT-PATCH.md
    │
    ├── guide/                         # 用户指南（对外）
    │   ├── API.md
    │   ├── RANGE-LAYER-GUIDE.md
    │   └── QUICK-START.md             # 新增：快速开始
    │
    ├── dev/                           # 开发指南（当前工作）⭐
    │   ├── BUILD-PLAN.md              # 当前计划（活文档）
    │   ├── C07-RULE-ANALYSIS.md
    │   └── REVISION-CHECKLIST.md
    │
    ├── reports/                       # 验证与报告
    │   ├── range/
    │   │   ├── RANGE-REAL-DATA-REPORT.md
    │   │   ├── RANGE-REAL-DATA-VALIDATION-COMPLETE.md
    │   │   └── RANGE-REAL-DATA-VALIDATION-PLAN.md
    │   └── validation/
    │       └── VALIDATION-FIXES.md
    │
    └── archive/                       # 历史归档（已完成）
        ├── tasks/                     # 任务完成报告
        │   ├── T3/
        │   │   ├── T3-COMPLETION-SUMMARY.md
        │   │   ├── T3-FINAL-REPORT.md
        │   │   ├── T3-MEMORY-RECORDED.md
        │   │   └── T3-TEST-RESULTS.md
        │   ├── T4/
        │   │   ├── T4-COMPLETION-SUMMARY.md
        │   │   ├── T4-DELIVERY-SUMMARY.md
        │   │   ├── T4-IMPLEMENTATION-PLAN.md
        │   │   ├── T4-PROGRESS-SUMMARY.md
        │   │   └── T4-START-PROMPT.md
        │   ├── T5/
        │   │   ├── T5-COMPLETION-SUMMARY.md
        │   │   ├── T5-IMPLEMENTATION-PLAN.md
        │   │   ├── T5-PROPOSAL.md
        │   │   ├── T5-REVIEW-FIXES.md
        │   │   ├── t5_guard_update_derivation.md
        │   │   └── t5_replay_test_design.md
        │   ├── T6/
        │   │   ├── T6-DAY-MINUS-3-COMPLETION.md
        │   │   ├── T6-DAY-MINUS-2-COMPLETION.md
        │   │   ├── T6-DAY-MINUS-1-PROMPT.md
        │   │   ├── T6-DAY-MINUS-1-COMPLETION.md
        │   │   ├── T6-DAY-0-PROMPT.md
        │   │   ├── T6-DAY-0-COMPLETION.md
        │   │   ├── T6-DAY-1-REPORT.md
        │   │   ├── T6-DAY-2-PROMPT.md
        │   │   ├── T6-DAY-2-REPORT.md
        │   │   └── T6-RANGE-IMPLEMENTATION-GUIDE.md
        │   └── C07/
        │       ├── C07-IMPLEMENTATION.md
        │       └── DAILY-LOG-2026-07-26-C07.md
        │
        ├── logs/                      # 日志归档
        │   ├── DAILY-LOG-2026-07-26.md
        │   ├── DAILY-LOG-2026-07-27.md
        │   └── TASK-COMPLETION-REPORT-20260726.md
        │
        └── summaries/                 # 总结归档
            ├── FINAL-SUMMARY-20260726.md
            └── V2_1_ALIGNMENT_COMPLETION_REPORT.md
```

---

## 关键文档说明

### ⭐ `docs/00-INDEX.md` - 文档导航入口（新增）

这是**唯一的入口文档**，回答：
- 我是新手，从哪里开始？→ `guide/API.md`
- 我要继续开发，看哪个？→ `dev/BUILD-PLAN.md` ⭐
- 我要查规格，在哪里？→ `spec/MALF_V2_1_AUTHORITY_REFERENCE.md`
- 历史任务在哪里？→ `archive/tasks/T*/`

### ⭐ `dev/BUILD-PLAN.md` - 当前开发计划（活文档）

这是**指导系统开发的主文档**，包含：
- 当前刀的 step 清单
- 已完成的刀的状态
- 下一步做什么

### 用途分类

| 目录 | 用途 | 读者 | 更新频率 |
|------|------|------|---------|
| `spec/` | 规格与合同 | 开发者 | 几乎不变 |
| `guide/` | 用户文档 | 用户/开发者 | 功能更新时 |
| **`dev/`** | **开发指南** | **开发者** | **每天** ⭐ |
| `reports/` | 验证报告 | 质量团队 | 里程碑时 |
| `archive/` | 历史记录 | 参考 | 任务完成时 |

---

## 执行计划

### Phase 1: 创建新结构（不破坏现有）
1. 创建 `scripts/` 及子目录
2. 创建 `docs/` 新子目录
3. 创建 `docs/00-INDEX.md`

### Phase 2: 移动文件
1. 移动根目录脚本到 `scripts/`
2. 移动文档到新目录
3. 保留 `README.md`, `CLAUDE.md` 在根目录

### Phase 3: 更新引用
1. 更新 `README.md` 文档链接
2. 更新 `CLAUDE.md` 文档链接
3. 创建 `CHANGELOG.md`

### Phase 4: 验证
1. 运行测试确保无破坏
2. 检查所有链接有效
3. 提交一次性大重构

---

## 立即行动

**执行？** 
- [ ] 是，开始重组
- [ ] 否，我先看看方案

**预计时间**: 30-40 分钟

**风险**: 低（文件移动不影响代码运行）

**收益**: 
- ✅ 清晰的文档结构
- ✅ 明确的开发入口
- ✅ 历史可追溯
- ✅ 易于维护
