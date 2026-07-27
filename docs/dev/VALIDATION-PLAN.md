# malf-engine 验证阶段计划

> **状态**: 建造完成（20/20 刀），进入验证阶段  
> **目标**: 在真实数据上验证引擎正确性，校准参数，建立生产就绪性  
> **最后更新**: 2026-07-27

---

## 验证哲学

**梁文锋的判断**：这个雏形的地基是好的——零依赖、整数价格、TDD 铁律、规格合规 95%。但引擎从未在真实完整数据上跑过。下一步不是"继续造"，而是**验证**——把引擎扔进真实数据，让它证明自己能产出正确的月/周/日结构快照。

**验证不是测试**。测试验证"代码按规格工作"，验证确认"规格在现实中有用"。

---

## 验证前 P0 修复清单

### ✅ P0-1: service_engine.py 字段名错误（已修复）

**问题**: `build_wave_structural_snapshot()` 中使用了不存在的字段名
- ❌ `core.progress_price` → ✅ `core.progress_extreme_price`
- ❌ `core.guard_price` → ✅ `core.current_effective_guard_price`
- ❌ `core.guard_bar_dt` → ✅ `core.current_effective_guard_extreme_bar_dt`
- ❌ `core.break_price` / `core.break_bar_dt` → ✅ `None` (TODO: 需从 Range 获取)
- ❌ `active_range.boundary_high_now` → ✅ `active_range.boundary_now_high`
- ❌ `active_range.candidate_replacement_count` → ✅ `core.candidate_replacement_count`
- ❌ `active_range.range_type` → ✅ `active_range.resolution_type`

**状态**: ✅ 已修复（2026-07-27）  
**提交**: 待提交

### ⏸ P0-2: BUILD-PLAN.md 重复章节

**问题**: Service 层在两处状态矛盾（85-93 行标记"✅ 完成"，944-963 行标记"⏸ 待做"）

**修复方案**: 删除 944-963 行的旧章节，统一状态为"✅ 完成"

**优先级**: P2（不阻塞验证）

---

## 验证阶段里程碑

### 🎯 V1: 真实数据流水线（1-2 天）

**目标**: 证明引擎能在完整历史数据上跑通，不崩溃，产出快照序列

**数据集**: 5 只 ETF 日线（TDX 格式）
- 510300 (沪深300ETF)
- 510500 (中证500ETF)
- 159915 (创业板ETF)
- 512880 (证券ETF)
- 513100 (纳指ETF)

**验证脚本**: `scripts/verify/v1_real_data_pipeline.py`

**产出**:
1. 每只标的的完整 snapshot 序列（`var/published/{symbol}/D/snapshots.jsonl`）
2. 统计报告：
   - 总 bar 数、成功处理数、失败数
   - Wave 数量（UP/DOWN 分布）
   - Range 数量（continuation/reversal 分布）
   - 状态转换序列（UNINITIALIZED → UP_ALIVE → TRANSITION → ...）
   - 异常日志（未预期的错误、状态不一致）

**验收标准**:
- [ ] 5 只标的全部处理完成（无崩溃）
- [ ] 每只标的产出 ≥ 1 个 wave
- [ ] 状态转换符合状态机规则（无非法跳转）
- [ ] lineage_hash 可重现（相同输入 → 相同 hash）

**不验收**:
- ❌ 不验证 wave 是否"正确"（那是 V2 的事）
- ❌ 不验证 rank 分布（那是 V3 的事）
- ❌ 不优化性能（先跑通再谈快慢）

---

### 🎯 V2: 结构正确性抽查（2-3 天）

**目标**: 人工抽查 10-20 个关键 bar，验证结构判定与规格一致

**方法**:
1. 从 V1 产出中选取典型场景：
   - 初始化成功（H0 → L1 → H2）
   - Guard break（同向 / 反向）
   - Range 诞生与 resolution
   - Pivot 替换（C-07 规则）
2. 人工对照 TDX K线图，逐字段验证：
   - Pivot 是否正确识别（k=2 窗口）
   - Guard 价格是否正确
   - Progress 追踪是否正确
   - Range 边界是否正确（init vs now）
   - Range 分类是否正确（continuation vs reversal）

**产出**:
- `docs/reports/VALIDATION-V2-STRUCTURAL-CORRECTNESS.md`
- 抽查清单（bar_dt + 预期 vs 实际）
- 发现的缺陷列表（如有）

**验收标准**:
- [ ] 10 个抽查案例中，≥ 9 个完全正确
- [ ] 发现的缺陷全部修复并回归测试

---

### 🎯 V3: 参数校准（1-2 天）

**目标**: 用真实数据校准阈值，替换"拍脑袋"的值

**待校准参数**:
1. **P2 same_dir_threshold**: 当前 0.10（未经校准）
2. **P3 cross_threshold**: 当前 0.15（未经校准）
3. **PEER_SAMPLE_MIN_N**: 当前 30（可能需调整）

**校准方法**:
1. 从 V1 产出中提取所有 wave 的 rank 差值分布
2. 绘制分布直方图
3. 根据分布选择合理阈值（如 percentile 20/80）
4. 回测标签准确率

**产出**:
- `docs/reports/VALIDATION-V3-PARAMETER-CALIBRATION.md`
- 阈值分布图
- 校准后的参数值
- 标签准确率报告

**验收标准**:
- [ ] P2/P3 标签在真实数据上有意义（不全是"flat"/"balanced"）
- [ ] peer_sample 充足率 ≥ 80%（避免过多 None）

---

### 🎯 V4: progress_pct 公式核对（1 天）

**目标**: 确认 `(wave_end - wave_start) / wave_start` 是否符合规格

**方法**:
1. 查阅 MALF_03_Lifespan_v2_1 规格原文
2. 用 golden fixture 验证公式
3. 若规格未明确，用真实数据测试合理性

**产出**:
- `docs/reports/VALIDATION-V4-PROGRESS-PCT-FORMULA.md`
- 公式定稿
- 单元测试（如有变更）

**验收标准**:
- [ ] 公式有规格依据 OR 真实数据验证合理
- [ ] 单元测试覆盖边界情况

---

### 🎯 V5: 补 bar_index 字段（0.5 天）

**目标**: `CoreStateSnapshot` 添加 `bar_index` 字段

**修改点**:
- `types.py`: 添加 `bar_index: int` 字段
- `core_engine.py`: 传入 `bar_index`
- 所有测试: 更新 fixture

**验收标准**:
- [ ] 全部测试通过
- [ ] `bar_index` 正确递增

---

### 🎯 V6: 清理文档（0.5 天）

**目标**: 删除 BUILD-PLAN.md 重复章节，统一状态

**验收标准**:
- [ ] BUILD-PLAN.md 无矛盾状态
- [ ] CLAUDE.md 反映最新进度

---

## 验证后的决策点

验证完成后，根据结果决定下一步：

### 路径 A: 验证通过 → 接入 RiskBench 产品层
- 确定 `var/published/` 目录结构
- 实现 Viewer 只读快照（不重算）
- 建立 current.json 原子指针机制

### 路径 B: 发现重大缺陷 → 回到建造阶段
- 记录缺陷（docs/reports/）
- 修复 + 回归测试
- 重新验证

### 路径 C: 规格不足 → 补充规格
- 记录规格空白
- 与规格作者对齐
- 补充规格后重新实现

---

## 不做的事（明确边界）

❌ **不加新功能**：验证阶段不添加新层级、新视图、新指标  
❌ **不做性能优化**：先跑通再谈快慢，过早优化是万恶之源  
❌ **不发 PyPI**：引擎是 RiskBench 内部组件，不是通用库  
❌ **不加 CI/CD**：单人单机，本地 pytest 就够了  
❌ **不做并行计算**：确定性 replay 优先于速度  

---

## 验证进度跟踪

| 里程碑 | 状态 | 预计耗时 | 实际耗时 | 完成日期 |
|--------|------|----------|----------|----------|
| V1: 真实数据流水线 | ⏸ 待开始 | 1-2 天 | - | - |
| V2: 结构正确性抽查 | ⏸ 待开始 | 2-3 天 | - | - |
| V3: 参数校准 | ⏸ 待开始 | 1-2 天 | - | - |
| V4: progress_pct 核对 | ⏸ 待开始 | 1 天 | - | - |
| V5: 补 bar_index | ⏸ 待开始 | 0.5 天 | - | - |
| V6: 清理文档 | ⏸ 待开始 | 0.5 天 | - | - |

**总预计**: 6-10 天  
**开始日期**: 待定  
**目标完成**: 待定

---

## 验证后的最终交付物

1. **验证报告**（6 份）
   - V1-V6 各一份，记录方法、数据、结果、结论
2. **校准参数**
   - P2/P3 阈值、peer_sample 最小值
3. **真实数据快照**
   - 5 只 ETF 完整 snapshot 序列
4. **缺陷修复记录**
   - 发现的问题 + 修复提交
5. **生产就绪性评估**
   - 能否接入 RiskBench 的判断依据

---

## 附录：验证脚本模板

### V1 真实数据流水线

```python
# scripts/verify/v1_real_data_pipeline.py

"""
V1: 真实数据流水线验证

目标：
- 证明引擎能在完整历史数据上跑通
- 产出完整 snapshot 序列
- 记录统计信息和异常

数据集：
- 510300, 510500, 159915, 512880, 513100（TDX 日线）

产出：
- var/published/{symbol}/D/snapshots.jsonl
- docs/reports/VALIDATION-V1-PIPELINE-REPORT.md
"""

import sys
from pathlib import Path
from datetime import datetime

# 假设已有 TDX 读取模块
from tdx_reader import load_daily_bars  # 待实现

from malf.core_engine import CoreEngine
from malf.service_engine import build_wave_structural_snapshot
from malf.persistence import persist_snapshot, update_current_pointer

SYMBOLS = ["510300", "510500", "159915", "512880", "513100"]
TIMEFRAME = "D"
BASE_PATH = Path("var")

def run_pipeline():
    """运行完整流水线"""
    report = {
        "start_time": datetime.now().isoformat(),
        "symbols": {},
    }
    
    for symbol in SYMBOLS:
        print(f"Processing {symbol}...")
        
        # 1. 加载数据
        bars = load_daily_bars(symbol)  # 返回 List[PriceBar]
        
        # 2. 初始化引擎
        engine = CoreEngine(symbol=symbol, timeframe=TIMEFRAME)
        
        # 3. 逐 bar 推进
        stats = {
            "total_bars": len(bars),
            "success": 0,
            "errors": [],
            "waves": 0,
            "ranges": 0,
        }
        
        for i, bar in enumerate(bars):
            try:
                # 推进引擎
                core_snapshot = engine.process_bar(bar)
                
                # 组装 snapshot（简化版，实际需传入更多参数）
                snapshot = build_wave_structural_snapshot(
                    symbol=symbol,
                    timeframe=TIMEFRAME,
                    bar_dt=bar.bar_dt,
                    bar_index=i,
                    core=core_snapshot,
                    # ... 其他参数
                )
                
                # 持久化
                filepath = persist_snapshot(snapshot, BASE_PATH)
                update_current_pointer(snapshot, filepath, BASE_PATH)
                
                stats["success"] += 1
                
            except Exception as e:
                stats["errors"].append({
                    "bar_index": i,
                    "bar_dt": bar.bar_dt,
                    "error": str(e),
                })
        
        report["symbols"][symbol] = stats
        print(f"  {symbol}: {stats['success']}/{stats['total_bars']} bars processed")
    
    report["end_time"] = datetime.now().isoformat()
    
    # 写入报告
    report_path = Path("docs/reports/VALIDATION-V1-PIPELINE-REPORT.md")
    write_report(report, report_path)
    
    print(f"\nReport written to {report_path}")

def write_report(report, path):
    """写入验证报告"""
    # 待实现：格式化为 Markdown
    pass

if __name__ == "__main__":
    run_pipeline()
```

---

**这是验证的开始，不是建造的延续。**
