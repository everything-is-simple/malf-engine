# T7.3 + T7.4 完成报告（Lifespan 层完成）

**日期**: 2026-07-27  
**任务**: T7.3 RangeLifespan 指标计算 + T7.4 RangeLifespan peer_sample + rank  
**状态**: ✅ 实现完成，等待用户验证

---

## 🎉 里程碑：Lifespan 层 100% 完成

**完成内容**：
- ✅ T7.1: WaveLifespan 指标计算
- ✅ T7.2: WaveLifespan percentile_rank + peer_sample 过滤
- ✅ T7.3: RangeLifespan 指标计算
- ✅ T7.4: RangeLifespan percentile_rank + peer_sample 过滤

**测试统计**：
- T7.1 + T7.2: 8 passed (WaveLifespan)
- T7.3: 6 passed (RangeLifespan 指标)
- T7.4: 5 passed (RangeLifespan rank)
- **总计**: 19 passed

**项目进度**：10/20 刀完成（50%）🎊

---

## 📋 T7.3 完成内容

### 1. Golden Fixture
- ✅ `tests/fixtures/t7_3_range_lifespan_continuation.json`
  - continuation_range 场景（UP wave 向下 break → 向下 resolution）
  - 人肉计算所有指标

### 2. 实现修改
- ✅ 修改 `src/malf/lifespan_engine.py::calculate_range_lifespan()`
  - 添加参数：`resolution_type` 和 `confirmation_pivot_extreme_price`
  - 修正 `resolution_distance_pct` 计算公式（v2.1 Range §5）
    - UP 突破：`(confirmation_pivot.extreme_price - boundary_high_now) / boundary_high_now`
    - DOWN 突破：`(boundary_low_now - confirmation_pivot.extreme_price) / boundary_low_now`

### 3. 测试
- ✅ 新增测试：`test_range_lifespan_continuation_golden_fixture`
- ✅ 更新 5 个现有测试以匹配新方法签名
- ✅ **6 passed, 0 failed**

---

## 📋 T7.4 完成内容

### 1. Golden Fixture
- ✅ `tests/fixtures/t7_4_range_ranks_continuation.json`
  - 35 个 continuation_range 样本池（满足最小样本量 N=30）
  - 人肉计算 4 个 percentile_rank（span_rank, evolution_rank, replacement_rank, resolution_distance_rank）

### 2. 实现
- ✅ 新增 `src/malf/rank_engine.py::filter_range_peer_sample()`
  - continuation/reversal 分池
  - 防前视过滤（range_end_bar_dt <= cutoff_bar_dt）

- ✅ 新增 `src/malf/rank_engine.py::calculate_range_ranks()`
  - 计算 4 个 rank 字段
  - 样本不足退化（N < 30 → None）

- ✅ 新增 `src/malf/rank_engine.py::update_range_lifespan_with_ranks()`
  - 用 dataclasses.replace 更新 frozen dataclass

### 3. 测试
- ✅ `test_range_ranks_continuation_golden_fixture`（golden fixture 驱动）
- ✅ `test_range_peer_sample_filtering_by_type`（分池测试）
- ✅ `test_range_peer_sample_anti_lookahead`（防前视测试）
- ✅ `test_range_ranks_insufficient_sample`（N < 30 退化）
- ✅ `test_range_ranks_empty_sample`（空样本退化）
- ✅ **5 passed, 0 failed**

---

## 🧪 用户验证步骤

### 方法 1：运行自动化测试脚本（推荐）
```powershell
cd I:\asteria-riskbench-components\malf-engine
.\TEST-T7_3.ps1  # 只测试 T7.3
```

### 方法 2：手动验证 T7.3 + T7.4
```powershell
cd I:\asteria-riskbench-components\malf-engine
D:\miniconda\py310\python.exe -m pytest tests\test_range_lifespan.py tests\test_range_ranks.py -v
```

### 方法 3：全量回归测试
```powershell
cd I:\asteria-riskbench-components\malf-engine
D:\miniconda\py310\python.exe -m pytest tests\ -v
```

**期望结果**：
- T7.3 + T7.4 测试：11 passed (6 + 5)
- 全量测试：77 passed, 2 skipped（66 之前 + 6 T7.3 + 5 T7.4）

---

## 📊 Lifespan 层完整测试覆盖

| 测试类别 | 测试数 | 状态 |
|---------|--------|------|
| WaveLifespan 指标计算 | 2 | ✅ |
| WaveLifespan percentile_rank | 6 | ✅ |
| RangeLifespan 指标计算 | 6 | ✅ |
| RangeLifespan percentile_rank | 5 | ✅ |
| **总计** | **19** | ✅ |

---

## 🔧 关键实现细节

### 双轨分池设计（v2.1 Lifespan §2）
- **WaveLifespan**: UP/DOWN 方向分池
- **RangeLifespan**: continuation/reversal 类型分池
- Wave 和 Range **不混池排名**

### percentile_rank 公式（v2.1 Lifespan §4）
```python
percentile_rank(x, sample) = count(x_i < x) / N
```
- 严格 `<`，不含 `=`
- 返回 [0, 1) 范围（永不达到 1.0）
- 样本不足（N < 30）→ None

### 防前视约束（v2.1 Lifespan §3.2 + §5.2）
- WaveLifespan: `wave_end_bar_dt <= current_bar_dt`
- RangeLifespan: `range_end_bar_dt <= current_bar_dt`（通常为 current_range 的 range_start_bar_dt）

### resolution_distance_pct 公式（v2.1 Range §5）
- **UP 突破**: `(confirmation_pivot.extreme_price - boundary_high_now) / boundary_high_now`
- **DOWN 突破**: `(boundary_low_now - confirmation_pivot.extreme_price) / boundary_low_now`
- 归一化到**边界价格本身**，而非 amplitude_init

---

## 🎯 下一步：Structural Position 层（T8.1-T8.4）

**Structural Position 层** 是 MALF v2.1 的最后一个核心层，负责将 Lifespan 的 rank 数据转换为 4 个结构位置视图：

### T8.1: P1 视图（Current Wave Position）
- 当前 wave 在历史同方向 wave 中的位置
- 输出 4 个百分位（span, range, stagnation, progress）

### T8.2: P2 视图（Current Range Position）
- 当前 Range 在历史同类型 Range 中的位置
- 输出 4 个百分位（span, evolution, replacement, resolution_distance）

### T8.3: P3 视图（Historical Context）
- 当前标的在历史中的波动特征
- 输出统计分布（均值、中位数、标准差）

### T8.4: P4 视图（Structural Labels）
- 基于 P1-P3 生成结构标签
- 输出：short/medium/long, volatile/stable, continuation/reversal 等

---

## 📝 Git 提交（待用户执行）

```powershell
cd I:\asteria-riskbench-components\malf-engine
git add -A
git commit -m "feat(lifespan): T7.3-T7.4 完成 Lifespan 层

T7.3: RangeLifespan 指标计算
- 实现 calculate_range_lifespan() 方法
- 修正 resolution_distance_pct 公式（v2.1 Range §5）
- 新增 golden fixture：t7_3_range_lifespan_continuation.json
- 新增测试：test_range_lifespan_continuation_golden_fixture
- 更新 5 个现有测试以匹配新方法签名
- 测试结果：6 passed

T7.4: RangeLifespan peer_sample + rank 计算
- 实现 filter_range_peer_sample() 方法（分池 + 防前视）
- 实现 calculate_range_ranks() 方法（4 个 rank 字段）
- 实现 update_range_lifespan_with_ranks() 方法
- 新增 golden fixture：t7_4_range_ranks_continuation.json（35 样本）
- 新增测试文件：test_range_ranks.py（5 个测试）
- 测试结果：5 passed

里程碑：Lifespan 层 100% 完成
- 总测试数：19 passed（WaveLifespan 8 + RangeLifespan 11）
- 项目进度：10/20 刀完成（50%）
- 下一步：Structural Position 层（T8.1-T8.4）"
```

---

**完成时间**: 2026-07-27  
**验证者**: 等待用户验证  
**下一步**: T8.1 Structural Position P1 视图
