# 文件组织规范

**版本**: 2026-07-27  
**目的**: 防止项目文件混乱，保持根目录整洁

---

## 📁 目录结构

```
malf-engine/
├── src/malf/              # 源代码（永久）
├── tests/                 # 测试代码（永久）
│   ├── fixtures/          # Golden fixtures
│   └── test_*.py
├── docs/                  # 文档（永久）
│   ├── spec/              # 规格定义
│   ├── guide/             # 用户指南
│   ├── dev/               # 开发文档
│   ├── reports/           # 验证报告
│   └── archive/           # 归档文档
│       └── tasks/         # 任务完成报告
├── scripts/               # 工具脚本（永久）
│   ├── verify/            # 真实数据验证脚本
│   ├── debug/             # 调试脚本（可定期清理）
│   └── tools/             # 工具脚本
├── .work/                 # 临时工作区（gitignore）
│   ├── test-runs/         # 测试运行记录
│   ├── debug/             # 调试临时文件
│   └── scratch/           # 其他临时文件
├── README.md              # 项目说明
├── CLAUDE.md              # Claude 工作指南
├── pyproject.toml         # 项目配置
└── .gitignore             # Git 忽略规则
```

---

## 📝 文件命名规范

### 源代码（`src/malf/`）
- **格式**: `{layer}_engine.py`
- **示例**: `core_engine.py`, `lifespan_engine.py`

### 测试文件（`tests/`）
- **格式**: `test_{module}.py` 或 `test_{feature}.py`
- **示例**: `test_wave_lifespan.py`, `test_range_ranks.py`

### Golden Fixtures（`tests/fixtures/`）
- **格式**: `t{task}_{feature}_{scenario}.json`
- **示例**: `t7_3_range_lifespan_continuation.json`

### 验证脚本（`scripts/verify/`）
- **格式**: `verify_{layer}_{dataset}.py`
- **示例**: `verify_lifespan_sh600000.py`, `verify_lifespan_multi_stocks.py`

### 调试脚本（`.work/debug/` 或 `scripts/debug/`）
- **格式**: `debug_{issue}.py`
- **示例**: `debug_t7_4_golden_fixture.py`
- **原则**: 任务完成后删除或归档

### 开发文档（`docs/dev/`）
- **格式**: `{TOPIC}.md` 或 `{TOPIC}-{SUBTOPIC}.md`
- **示例**: `BUILD-PLAN.md`, `AI-TASK-WORKFLOW.md`

### 验证报告（`docs/reports/{layer}/`）
- **格式**: `{FEATURE}-VALIDATION.md` 或 `LAYER-COMPLETE.md`
- **示例**: `lifespan/LAYER-COMPLETE.md`

### 任务归档（`docs/archive/tasks/{TASK}/`）
- **格式**: `{TASK}-COMPLETION.md`, `SUMMARY.md`
- **示例**: `T7.3-T7.4/SUMMARY.md`

---

## 🚫 根目录禁止事项

**根目录只允许这些文件**：
- ✅ `README.md`
- ✅ `CLAUDE.md`
- ✅ `pyproject.toml`
- ✅ `.gitignore`

**禁止出现在根目录**：
- ❌ `verify_*.py` - 应放在 `scripts/verify/` 或 `.work/debug/`
- ❌ `debug_*.py` - 应放在 `.work/debug/` 或 `scripts/debug/`
- ❌ `run_*.py` - 临时脚本，任务完成后删除
- ❌ `test_*.py` - 应放在 `tests/`
- ❌ `TEST-*.ps1` - 临时脚本，任务完成后移到 `scripts/` 或删除
- ❌ `*-REPORT.md` - 应归档到 `docs/archive/tasks/`
- ❌ `*-COMPLETE.md` - 应归档到 `docs/reports/`
- ❌ `test-report-*.txt` - 应删除或移到 `.work/test-runs/`

---

## 🤖 AI 助手执行规则

### 创建文件前的决策树

```
问自己 3 个问题：

1. 这是什么类型的文件？
   - 源代码 → src/malf/
   - 测试 → tests/
   - Golden fixture → tests/fixtures/
   - 文档 → docs/{category}/
   - 验证脚本 → scripts/verify/
   - 调试脚本 → .work/debug/
   - 临时脚本 → .work/scratch/

2. 这个文件是永久的还是临时的？
   - 永久 → 放到规范目录
   - 临时 → 放到 .work/ 并在代码中注释 "TODO: 临时文件"

3. 任务完成后还需要这个文件吗？
   - 需要 → 确保在正确的永久目录
   - 不需要 → 放到 .work/ 或立即删除
```

### 任务完成后的清理检查清单

每次任务完成（如 T7.3, T7.4）后，执行以下检查：

- [ ] 删除 `.work/` 下的临时文件
- [ ] 删除根目录的 `verify_*.py` 和 `debug_*.py`
- [ ] 删除根目录的临时 PowerShell 脚本
- [ ] 归档完成报告到 `docs/archive/tasks/{TASK}/`
- [ ] 归档验证报告到 `docs/reports/{layer}/`
- [ ] 移动有用的脚本到 `scripts/`
- [ ] 运行 `git status` 检查根目录是否干净

---

## 📋 清理脚本

项目提供了 `CLEANUP-FILES.ps1` 脚本来自动执行清理：

```powershell
.\CLEANUP-FILES.ps1
```

这个脚本会：
1. 创建规范的目录结构
2. 删除临时验证/调试脚本
3. 删除临时 PowerShell 脚本
4. 归档完成报告
5. 移动测试脚本到 `scripts/`
6. 清理测试报告

---

## 🎯 成功标准

**干净的根目录只有 4 个文件**：
```
malf-engine/
├── README.md
├── CLAUDE.md
├── pyproject.toml
└── .gitignore
```

加上这些目录（但不在根目录展开）：
```
├── src/
├── tests/
├── docs/
├── scripts/
└── .work/ (gitignore)
```

---

## 📝 维护

- **更新时机**: 发现新的混乱模式时
- **维护者**: 每个开发者（包括 AI 助手）
- **审查频率**: 每次任务完成时

---

**创建日期**: 2026-07-27  
**最后更新**: 2026-07-27
