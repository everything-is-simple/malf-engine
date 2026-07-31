# 📋 用户操作指南 - 文件清理 + 真实数据验证

**日期**: 2026-07-27  
**任务**: 执行文件清理 + Lifespan 层真实数据验证

---

## ✅ 第一步：文件清理

### 为什么需要清理？

当前根目录混乱，有大量临时脚本和报告：
- 临时验证脚本：`verify_t7_3.py`, `verify_t7_4.py`, `debug_t7_4.py`
- 临时测试脚本：`run_*.py`
- 临时 PowerShell 脚本：`TEST-*.ps1`, `run-*.ps1`, `create-pr*.ps1`
- 完成报告：`*-REPORT.md`, `*-COMPLETE.md`

### 执行清理

在 PowerShell 中运行：

```powershell
cd I:\asteria-riskbench-components\malf-engine
.\CLEANUP-FILES.ps1
```

### 清理内容

脚本会自动：
1. ✅ 创建规范目录结构（`.work/`, `scripts/`, `docs/archive/`）
2. ✅ 删除临时验证/调试脚本
3. ✅ 删除临时 PowerShell 脚本
4. ✅ 归档完成报告到 `docs/archive/tasks/T7.3-T7.4/`
5. ✅ 归档验证报告到 `docs/reports/lifespan/`
6. ✅ 移动测试脚本到 `scripts/`

### 验证清理结果

运行后检查根目录：

```powershell
Get-ChildItem -Path . -File | Where-Object { $_.Extension -in @(".md", ".py", ".ps1") }
```

**期望结果**：只有 4 个文件
- `README.md`
- `CLAUDE.md`
- `pyproject.toml`
- `.gitignore`

加上清理脚本本身：
- `CLEANUP-FILES.ps1`（清理完成后可以删除）

---

## ✅ 第二步：提交清理结果

```powershell
git add -A
git status  # 检查更改
git commit -m "chore: 文件清理 - 整理项目目录结构

- 创建规范目录结构（.work/, scripts/, docs/archive/）
- 删除临时验证/调试脚本
- 归档完成报告到 docs/archive/tasks/T7.3-T7.4/
- 归档验证报告到 docs/reports/lifespan/
- 更新文件组织规范（docs/dev/FILE-ORGANIZATION.md）
- 更新 CLAUDE.md 添加文件创建规则"

git push origin HEAD
```

---

## 🧪 第三步：真实数据验证（可选）

### 准备真实数据

验证脚本需要真实 OHLC 数据。当前脚本是占位符实现，需要您提供数据源。

### 选项 A：使用现有数据源

如果您有数据源（如 CSV 文件、数据库连接），修改脚本中的 `load_test_data()` 函数：

```python
def load_test_data(symbol: str, limit: int = 200) -> list[PriceBar]:
    """加载真实 OHLC 数据。"""
    # TODO: 从您的数据源加载
    # 示例：读取 CSV
    import csv
    bars = []
    with open(f"data/{symbol}.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bar = PriceBar(
                symbol=symbol,
                timeframe="D",
                bar_dt=row["date"],
                open=int(float(row["open"]) * 1000),
                high=int(float(row["high"]) * 1000),
                low=int(float(row["low"]) * 1000),
                close=int(float(row["close"]) * 1000)
            )
            bars.append(bar)
            if len(bars) >= limit:
                break
    return bars
```

### 选项 B：跳过真实数据验证

如果暂时没有数据源，可以跳过此步骤。Lifespan 层已通过 19 个单元测试验证，功能是可靠的。

### 运行验证（如果有数据）

```powershell
cd I:\asteria-riskbench-components\malf-engine
python scripts\verify\verify_lifespan_multi_stocks.py
```

### 验证内容

脚本会验证 5 只股票：
1. sh600000 - 浦发银行
2. sh600036 - 招商银行
3. sh600519 - 贵州茅台
4. sh601318 - 中国平安
5. sh601857 - 中国石油

对每只股票验证：
- WaveLifespan 指标计算
- RangeLifespan 指标计算
- percentile_rank 计算
- peer_sample 过滤

### 查看结果

验证完成后，报告会保存到：
```
docs/reports/lifespan/MULTI-STOCK-VALIDATION-{timestamp}.json
```

---

## 📊 完成状态

完成清理后，您的项目结构将变为：

```
malf-engine/
├── src/malf/              ← 源代码
├── tests/                 ← 测试
├── docs/                  ← 文档（整理后）
│   ├── spec/
│   ├── guide/
│   ├── dev/
│   ├── reports/
│   └── archive/
│       └── tasks/
│           └── T7.3-T7.4/  ← 新归档
├── scripts/               ← 脚本（整理后）
│   ├── verify/            ← 验证脚本
│   ├── debug/
│   └── tools/
├── .work/                 ← 临时工作区（gitignore）
├── README.md              ← 根目录只有 4 个文件
├── CLAUDE.md
├── pyproject.toml
└── .gitignore
```

---

## 🎯 下一步

文件清理完成后，可以：

1. **继续开发 Structural Position 层**（T8.1-T8.4）
2. **真实数据验证**（如果有数据源）
3. **休息片刻** 🎉

---

**创建日期**: 2026-07-27  
**预计执行时间**: 5-10 分钟（清理） + 可选（验证）
