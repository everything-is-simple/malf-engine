# malf-engine 项目清理报告

**生成日期**: 2026-07-27  
**目的**: 诊断文档和脚本混乱问题，提供清理行动方案

---

## 📊 当前状态诊断

### 文件统计
- **总 Markdown 文件**: 49 个
- **docs/ 目录**: 44 个（含 33 个归档文件）
- **根目录**: 3 个 (.md)
- **scripts/ 目录**: 9 个 (.py)
- **其他**: 1 个 shell 脚本

### 问题识别

#### 🔴 严重问题
1. **根目录遗留**: `TASK-SUMMARY.md` 和 `commit_t4.sh` 是 T4/T6 任务的临时产物，未归档
2. **docs/archive/ 过载**: 33 个归档文件（占总文档 67%），结构臃肿
3. **重复内容**: 多个日志、总结、报告描述相同任务（如 T6 有 10 个文档）

#### 🟡 次要问题
1. **scripts/ 命名不统一**: `debug_*.py` vs `verify_*.py` vs `analyze_*.py`
2. **部分脚本过时**: `debug_t2.py`、`debug_t3_fixture.py`、`verify_t3.py` 针对早期任务
3. **00-INDEX.md 未同步**: 最后更新 2026-07-26，但 07-27 有新日志产生

---

## 📋 清理方案

### 阶段 1: 根目录清理（立即执行）

#### 动作 1.1: 归档任务遗留文件
```bash
# TASK-SUMMARY.md → docs/archive/tasks/T6/
mv TASK-SUMMARY.md docs/archive/tasks/T6/T6-TASK-SUMMARY.md

# commit_t4.sh → 删除（过时的提交脚本）
rm commit_t4.sh
```

**理由**:
- `TASK-SUMMARY.md` 是 T6 Day 0 任务总结，应归档到 T6 目录
- `commit_t4.sh` 是 T4 临时提交脚本，T4 已完成且提交，无保留价值

---

### 阶段 2: docs/archive/ 精简（重要但不紧急）

#### 问题分析
当前 `docs/archive/` 包含 33 个文件，分为：
- **logs/** (3 个): 日志文件
- **summaries/** (2 个): 总结文件
- **tasks/** (27 个): 按任务组织
- **根目录** (1 个): `PROJECT-REORGANIZATION-PLAN.md`

#### 动作 2.1: 合并重复文档

**T6 目录（10 个文档 → 4 个）**:
```
保留：
✅ T6-DAY-0-COMPLETION.md          # Day 0 fixture 推导完成报告
✅ T6-DAY-1-REPORT.md              # Day 1 TDD 实现报告
✅ T6-DAY-2-REPORT.md              # Day 2 测试扩展报告
✅ T6-RANGE-IMPLEMENTATION-GUIDE.md # 实施指南（922 行，最详细）

删除（内容已被后续报告覆盖）:
❌ T6-DAY-0-PROMPT.md              # 被 DAY-0-COMPLETION 覆盖
❌ T6-DAY-2-PROMPT.md              # 被 DAY-2-REPORT 覆盖
❌ T6-DAY-MINUS-1-COMPLETION.md    # 准备工作，价值较低
❌ T6-DAY-MINUS-1-PROMPT.md        # 准备工作，价值较低
❌ T6-DAY-MINUS-2-COMPLETION.md    # 准备工作，价值较低
❌ T6-DAY-MINUS-3-COMPLETION.md    # 准备工作，价值较低
```

**T5 目录（5 个文档 → 2 个）**:
```
保留：
✅ T5-COMPLETION-SUMMARY.md        # 完成总结（最终版本）
✅ T5-IMPLEMENTATION-PLAN.md       # 实施计划（有参考价值）

删除：
❌ T5-PROPOSAL.md                  # 被 IMPLEMENTATION-PLAN 覆盖
❌ T5-REVIEW-FIXES.md              # 修复记录，已整合到 COMPLETION-SUMMARY
❌ t5_guard_update_derivation.md  # 推导细节，已整合到代码注释
❌ t5_replay_test_design.md       # 测试设计，已实现
```

**T4 目录（5 个文档 → 2 个）**:
```
保留：
✅ T4-COMPLETION-SUMMARY.md        # 完成总结（295 行，最详细）
✅ T4-IMPLEMENTATION-PLAN.md       # 实施计划（有参考价值）

删除：
❌ T4-DELIVERY-SUMMARY.md          # 简化版总结（118 行），被 COMPLETION 覆盖
❌ T4-PROGRESS-SUMMARY.md          # 中间进度，已过时
❌ T4-START-PROMPT.md              # 启动 prompt，价值较低
```

**T3 目录（4 个文档 → 2 个）**:
```
保留：
✅ T3-FINAL-REPORT.md              # 最终报告（254 行，最详细）
✅ T3-COMPLETION-SUMMARY.md        # 完成总结（简洁版）

删除：
❌ T3-TEST-RESULTS.md              # 测试结果，已整合到 FINAL-REPORT
❌ T3-MEMORY-RECORDED.md           # 记忆确认（79 行，价值较低）
```

**C07 目录（2 个文档 → 1 个）**:
```
保留：
✅ C07-IMPLEMENTATION.md           # 完整实现报告

删除：
❌ DAILY-LOG-2026-07-26-C07.md    # 日志，已整合到 IMPLEMENTATION
```

**logs/ 目录（3 个 → 1 个）**:
```
保留：
✅ DAILY-LOG-2026-07-27.md         # 最新日志

删除：
❌ DAILY-LOG-2026-07-26.md         # 旧日志，价值较低
❌ TASK-COMPLETION-REPORT-20260726.md # 任务报告，被各任务目录覆盖
```

**summaries/ 目录（2 个 → 0 个，全部删除）**:
```
删除：
❌ FINAL-SUMMARY-20260726.md       # 与 TASK-COMPLETION-REPORT 重复
❌ V2_1_ALIGNMENT_COMPLETION_REPORT.md # 对齐报告，已完成
```

**根目录清理**:
```
删除：
❌ PROJECT-REORGANIZATION-PLAN.md  # 重组计划，已执行完毕
```

#### 精简后结构
```
docs/archive/
├── logs/
│   └── DAILY-LOG-2026-07-27.md           # 保留最新日志
├── tasks/
│   ├── C07/
│   │   └── C07-IMPLEMENTATION.md          # 1 个
│   ├── T3/
│   │   ├── T3-FINAL-REPORT.md             # 2 个
│   │   └── T3-COMPLETION-SUMMARY.md
│   ├── T4/
│   │   ├── T4-COMPLETION-SUMMARY.md       # 2 个
│   │   └── T4-IMPLEMENTATION-PLAN.md
│   ├── T5/
│   │   ├── T5-COMPLETION-SUMMARY.md       # 2 个
│   │   └── T5-IMPLEMENTATION-PLAN.md
│   └── T6/
│       ├── T6-DAY-0-COMPLETION.md         # 4 个
│       ├── T6-DAY-1-REPORT.md
│       ├── T6-DAY-2-REPORT.md
│       └── T6-RANGE-IMPLEMENTATION-GUIDE.md
└── (summaries/ 删除)
```

**统计**: 33 个文件 → 12 个文件（减少 64%）

---

### 阶段 3: scripts/ 目录优化（可选）

#### 当前状态
```
scripts/
├── analyze/
│   ├── analyze_c07_3.py          # C07 分析（40 行）
│   └── analyze_range_stats.py    # Range 统计（303 行）✅ 保留
├── debug/
│   ├── debug_c07_3.py            # C07 调试（47 行）
│   ├── debug_guard_break.py      # Guard break 调试（50 行）
│   ├── debug_t2.py               # T2 调试（51 行）❌ 过时
│   └── debug_t3_fixture.py       # T3 调试（28 行）❌ 过时
└── verify/
    ├── test_offset_0_real_data.py # 真实数据测试（86 行）✅ 保留
    ├── verify_t3.py               # T3 验证（129 行）❌ 过时
    └── verify_t3_fixed.py         # T3 修复验证（103 行）❌ 过时
```

#### 动作 3.1: 删除过时脚本
```bash
# 过时调试/验证脚本（T2/T3 已完成且测试通过）
rm scripts/debug/debug_t2.py
rm scripts/debug/debug_t3_fixture.py
rm scripts/verify/verify_t3.py
rm scripts/verify/verify_t3_fixed.py
```

#### 动作 3.2: 整理 C07 脚本（可选）
```bash
# C07 已完成，调试脚本可归档或删除
# 如果未来不需要调试 C07，可删除：
rm scripts/analyze/analyze_c07_3.py
rm scripts/debug/debug_c07_3.py
rm scripts/debug/debug_guard_break.py
```

#### 精简后结构（激进方案）
```
scripts/
├── analyze/
│   └── analyze_range_stats.py    # Range 统计（唯一有持续价值的脚本）
└── verify/
    └── test_offset_0_real_data.py # 真实数据测试
```

**统计**: 9 个文件 → 2 个文件（减少 78%）

#### 保守方案（如果担心需要参考）
保留所有 C07 相关脚本，仅删除 T2/T3 脚本：
```
scripts/
├── analyze/
│   ├── analyze_c07_3.py          # 保留
│   └── analyze_range_stats.py    # 保留
├── debug/
│   ├── debug_c07_3.py            # 保留
│   └── debug_guard_break.py      # 保留
└── verify/
    └── test_offset_0_real_data.py # 保留
```

**统计**: 9 个文件 → 5 个文件（减少 44%）

---

### 阶段 4: 更新 00-INDEX.md（清理后执行）

#### 需要更新的内容
1. **文档数量**: 更新统计（49 → 约 23）
2. **归档目录**: 反映新的精简结构
3. **最后更新日期**: 改为 2026-07-27
4. **项目状态**: 更新为"待启动 T6.1"

---

## 🎯 执行建议

### 推荐执行顺序

#### Step 1: 快速清理（10 分钟）⭐ **优先**
```bash
# 1.1 根目录清理
mv TASK-SUMMARY.md docs/archive/tasks/T6/T6-TASK-SUMMARY.md
rm commit_t4.sh

# 1.2 删除过时脚本
rm scripts/debug/debug_t2.py
rm scripts/debug/debug_t3_fixture.py
rm scripts/verify/verify_t3.py
rm scripts/verify/verify_t3_fixed.py
```

**效果**: 清理 5 个遗留文件，立即见效

---

#### Step 2: 文档精简（30 分钟）⚠️ **慎重**
执行前**务必备份**或使用 git 提交：
```bash
cd docs/archive

# 删除 T6 冗余文档（6 个）
rm tasks/T6/T6-DAY-0-PROMPT.md
rm tasks/T6/T6-DAY-2-PROMPT.md
rm tasks/T6/T6-DAY-MINUS-1-COMPLETION.md
rm tasks/T6/T6-DAY-MINUS-1-PROMPT.md
rm tasks/T6/T6-DAY-MINUS-2-COMPLETION.md
rm tasks/T6/T6-DAY-MINUS-3-COMPLETION.md

# 删除 T5 冗余文档（3 个）
rm tasks/T5/T5-PROPOSAL.md
rm tasks/T5/T5-REVIEW-FIXES.md
rm tasks/T5/t5_guard_update_derivation.md
rm tasks/T5/t5_replay_test_design.md

# 删除 T4 冗余文档（3 个）
rm tasks/T4/T4-DELIVERY-SUMMARY.md
rm tasks/T4/T4-PROGRESS-SUMMARY.md
rm tasks/T4/T4-START-PROMPT.md

# 删除 T3 冗余文档（2 个）
rm tasks/T3/T3-TEST-RESULTS.md
rm tasks/T3/T3-MEMORY-RECORDED.md

# 删除 C07 冗余文档（1 个）
rm tasks/C07/DAILY-LOG-2026-07-26-C07.md

# 删除旧日志（2 个）
rm logs/DAILY-LOG-2026-07-26.md
rm logs/TASK-COMPLETION-REPORT-20260726.md

# 删除 summaries 目录（2 个）
rm summaries/FINAL-SUMMARY-20260726.md
rm summaries/V2_1_ALIGNMENT_COMPLETION_REPORT.md
rmdir summaries

# 删除根目录遗留（1 个）
rm PROJECT-REORGANIZATION-PLAN.md
```

**效果**: 33 个归档文件 → 12 个（减少 64%）

---

#### Step 3: 更新索引（5 分钟）
更新 `docs/00-INDEX.md`:
- 修改文档数量统计
- 更新归档目录结构示例
- 更新最后修改日期为 2026-07-27

---

### 风险评估

#### 🟢 低风险操作（建议立即执行）
- ✅ Step 1.1: 根目录清理
- ✅ Step 1.2: 删除 T2/T3 过时脚本
- ✅ Step 3: 更新 00-INDEX.md

#### 🟡 中风险操作（建议 git commit 后执行）
- ⚠️ Step 2: 文档精简（删除 21 个归档文档）
- ⚠️ 删除 C07 脚本（如果未来需要参考会麻烦）

#### 🔴 不建议执行
- ❌ 删除 `DAILY-LOG-2026-07-27.md`（当前日志）
- ❌ 删除 `analyze_range_stats.py`（Range 层唯一统计工具）
- ❌ 删除任何 `*-COMPLETION-SUMMARY.md` 或 `*-FINAL-REPORT.md`

---

## 📊 清理效果预测

### 文件数量变化
| 类别 | 清理前 | 清理后 | 减少 |
|------|--------|--------|------|
| 根目录 .md | 3 | 2 | -1 |
| 根目录 .sh | 1 | 0 | -1 |
| docs/archive/ | 33 | 12 | -21 |
| scripts/ | 9 | 2-5 | -4~7 |
| **总计** | **49 文档 + 10 脚本** | **约 23 文档 + 2-5 脚本** | **-50%** |

### 目录结构对比

#### 清理前（混乱）
```
malf-engine/
├── TASK-SUMMARY.md          ❌ 遗留
├── commit_t4.sh             ❌ 遗留
├── docs/
│   ├── archive/ (33 个)     ❌ 过载
│   │   ├── logs/ (3)
│   │   ├── summaries/ (2)
│   │   └── tasks/ (27)      ❌ 重复严重
│   └── ...
└── scripts/ (9 个)          ❌ 过时脚本多
```

#### 清理后（整洁）
```
malf-engine/
├── docs/
│   ├── archive/ (12 个)     ✅ 精简
│   │   ├── logs/ (1)
│   │   └── tasks/ (11)      ✅ 每任务 1-4 个核心文档
│   └── ...
└── scripts/ (2-5 个)        ✅ 只保留有持续价值的
```

---

## 🚀 后续维护建议

### 防止再次混乱的原则

#### 1. 一个任务一个总结
每个任务（Tx/Cx）完成后，**只保留 1-2 个核心文档**：
- `{TASK}-COMPLETION-SUMMARY.md` 或 `{TASK}-FINAL-REPORT.md`（必须）
- `{TASK}-IMPLEMENTATION-PLAN.md`（可选，仅当有参考价值时）

删除：
- ❌ 所有 `*-PROMPT.md`（启动 prompt）
- ❌ 所有 `*-PROGRESS-*.md`（中间进度）
- ❌ 所有 `DAY-MINUS-*.md`（准备工作）
- ❌ 所有 `DAILY-LOG-*.md`（除非是最新的）

#### 2. 脚本及时清理
- 任务完成后，立即删除该任务的调试脚本（`debug_tx.py`）
- 只保留有持续价值的脚本（如 `analyze_range_stats.py`）

#### 3. 根目录零遗留
- 根目录永远不应该有 `TASK-*.md` 或 `commit_*.sh`
- 临时文件立即归档或删除

#### 4. 归档目录分层
```
docs/archive/tasks/{TASK}/
├── {TASK}-COMPLETION-SUMMARY.md  # 核心，必须
└── {TASK}-IMPLEMENTATION-PLAN.md # 可选
```

每个任务目录**不超过 4 个文件**。

---

## ✅ 执行清单

### 立即执行（低风险）
- [ ] 移动 `TASK-SUMMARY.md` → `docs/archive/tasks/T6/T6-TASK-SUMMARY.md`
- [ ] 删除 `commit_t4.sh`
- [ ] 删除 `scripts/debug/debug_t2.py`
- [ ] 删除 `scripts/debug/debug_t3_fixture.py`
- [ ] 删除 `scripts/verify/verify_t3.py`
- [ ] 删除 `scripts/verify/verify_t3_fixed.py`
- [ ] 更新 `docs/00-INDEX.md`（日期、统计）

### 可选执行（中风险，建议 git commit 后）
- [ ] 删除 docs/archive/ 中 21 个冗余文档（见阶段 2）
- [ ] 删除 C07 相关调试脚本（3 个，见阶段 3）

### 不执行（高风险）
- ❌ 不删除任何 `*-COMPLETION-SUMMARY.md`
- ❌ 不删除 `DAILY-LOG-2026-07-27.md`
- ❌ 不删除 `analyze_range_stats.py`

---

## 📝 总结

### 核心问题
1. **根目录遗留**: 2 个临时文件未归档
2. **归档过载**: 33 个文档中 21 个是重复/过时的
3. **脚本冗余**: 9 个脚本中 4-7 个是过时的

### 推荐方案
**激进清理**: 删除 50% 文件（26 个），整理后维护成本极低  
**保守清理**: 删除 30% 文件（15 个），保留更多参考材料

### 预期效果
- ✅ 根目录整洁（0 遗留文件）
- ✅ 归档目录精简（33 → 12 个）
- ✅ 脚本目录有序（9 → 2-5 个）
- ✅ 文档导航清晰（00-INDEX 更新）

---

**下一步**: 阅读本报告，决定执行范围，然后开始清理 🧹
