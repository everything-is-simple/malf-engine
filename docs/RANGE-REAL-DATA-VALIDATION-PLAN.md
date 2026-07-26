# Range 层真实数据验证 - 行动计划

**目标**: 使用 TDX 真实市场数据验证 Range 层实现的正确性和鲁棒性

**日期**: 2026-07-26

---

## 📋 总体策略

### 验证范围
- **数据源**: 上证 600000（浦发银行）日线数据
- **数据量**: 前 200 bars（已有 Core 层验证）
- **验证层次**: Range 层字段完整性 + 统计分析

### 验证目标
1. ✅ **功能正确性**: Range 字段逻辑正确，无异常值
2. ✅ **统计合理性**: 诞生频率、resolution 分布符合预期
3. ✅ **边界情况**: 发现并处理意外组合
4. ✅ **性能基线**: 记录处理时间，为后续优化提供基准

---

## 🎯 三步执行计划

### Step 1: 扩展冒烟测试（验证功能）

**任务**: 在 `test_real_data_smoke.py` 中添加 Range 层字段验证

**实现**:
```python
def test_sh600000_range_layer_smoke():
    """Range 层真实数据冒烟测试"""
    bars = load_sh600000_bars(limit=200)
    engine = MALFCoreEngine(k=2)
    
    range_births = []
    range_resolutions = []
    
    for bar in bars:
        snapshot = engine.on_bar(bar)
        
        # 收集 Range 诞生事件
        if snapshot.range_birth_bar_dt == snapshot.bar_dt:
            range_births.append({
                'bar_dt': snapshot.bar_dt,
                'boundary_init_high': snapshot.range_boundary_init_high,
                'boundary_init_low': snapshot.range_boundary_init_low,
                'direction': snapshot.direction.value
            })
        
        # 收集 Range resolution 事件
        if snapshot.range_resolution_bar_dt == snapshot.bar_dt:
            range_resolutions.append({
                'bar_dt': snapshot.bar_dt,
                'type': snapshot.range_resolution_type,
                'distance': snapshot.range_resolution_distance,
                'evolution_count': snapshot.range_evolution_count
            })
        
        # 验证不变量
        if snapshot.system_state == SystemState.TRANSITION:
            # boundary_init 必须存在
            assert snapshot.range_boundary_init_high is not None
            assert snapshot.range_boundary_init_low is not None
            # boundary_now 必须存在
            assert snapshot.range_boundary_now_high is not None
            assert snapshot.range_boundary_now_low is not None
            # R2 不变量：boundary_now 包含 boundary_init
            assert snapshot.range_boundary_now_high >= snapshot.range_boundary_init_high
            assert snapshot.range_boundary_now_low <= snapshot.range_boundary_init_low
    
    # 基本断言
    assert len(range_births) > 0, "应至少有一个 Range 诞生"
    assert len(range_resolutions) > 0, "应至少有一个 Range resolution"
    
    print(f"\n✅ Range 诞生次数: {len(range_births)}")
    print(f"✅ Range resolution 次数: {len(range_resolutions)}")
```

**验证点**:
- ✅ Range 字段完整性（非 None）
- ✅ R2 不变量（boundary_now 包含 boundary_init）
- ✅ 基本统计（诞生/resolution 次数 > 0）

---

### Step 2: 生成统计报告（分析分布）

**任务**: 创建独立脚本 `analyze_range_stats.py`，生成详细统计报告

**实现**:
```python
#!/usr/bin/env python3
"""Range 层真实数据统计分析"""

import json
from pathlib import Path
from collections import Counter
from malf.core_engine import MALFCoreEngine
from malf.types import SystemState

# 加载数据
bars = load_sh600000_bars(limit=200)
engine = MALFCoreEngine(k=2)

# 统计变量
range_events = []
current_range = None

for bar in bars:
    snapshot = engine.on_bar(bar)
    
    # 跟踪 Range 生命周期
    if snapshot.range_birth_bar_dt == snapshot.bar_dt:
        current_range = {
            'birth_bar_dt': snapshot.bar_dt,
            'direction': snapshot.direction.value,
            'boundary_init': (snapshot.range_boundary_init_high, snapshot.range_boundary_init_low),
            'max_evolution_count': 0,
            'resolution_type': None,
            'duration': 0
        }
    
    if current_range and snapshot.system_state == SystemState.TRANSITION:
        current_range['duration'] += 1
        current_range['max_evolution_count'] = max(
            current_range['max_evolution_count'],
            snapshot.range_evolution_count
        )
    
    if snapshot.range_resolution_bar_dt == snapshot.bar_dt:
        if current_range:
            current_range['resolution_type'] = snapshot.range_resolution_type
            current_range['resolution_distance'] = snapshot.range_resolution_distance
            range_events.append(current_range)
            current_range = None

# 统计分析
total_ranges = len(range_events)
continuation_count = sum(1 for r in range_events if r['resolution_type'] == 'continuation')
reversal_count = sum(1 for r in range_events if r['resolution_type'] == 'reversal')
avg_duration = sum(r['duration'] for r in range_events) / total_ranges if total_ranges > 0 else 0
evolution_counts = [r['max_evolution_count'] for r in range_events]
evolution_distribution = Counter(evolution_counts)

# 输出报告
report = f"""
# Range 层真实数据统计报告

**数据源**: 上证 600000（浦发银行）  
**数据量**: 200 bars  
**分析日期**: 2026-07-26

---

## 📊 基础统计

- **Range 总数**: {total_ranges}
- **平均持续时间**: {avg_duration:.2f} bars
- **最长持续时间**: {max(r['duration'] for r in range_events) if range_events else 0} bars
- **最短持续时间**: {min(r['duration'] for r in range_events) if range_events else 0} bars

---

## 🎯 Resolution 类型分布

| 类型 | 数量 | 占比 |
|------|------|------|
| Continuation | {continuation_count} | {continuation_count/total_ranges*100:.1f}% |
| Reversal | {reversal_count} | {reversal_count/total_ranges*100:.1f}% |

---

## 📈 Evolution 次数分布

| Evolution Count | 数量 | 占比 |
|----------------|------|------|
"""

for count in sorted(evolution_distribution.keys()):
    freq = evolution_distribution[count]
    pct = freq / total_ranges * 100
    report += f"| {count} | {freq} | {pct:.1f}% |\n"

report += f"""
---

## 🔍 异常检测

- **超长 Range**: {len([r for r in range_events if r['duration'] > 20])} 个（持续 > 20 bars）
- **高频演化**: {len([r for r in range_events if r['max_evolution_count'] > 5])} 个（演化 > 5 次）

---

## ✅ 结论

"""

# 保存报告
with open('docs/RANGE-REAL-DATA-REPORT.md', 'w', encoding='utf-8') as f:
    f.write(report)

print(report)
```

**输出**:
- Markdown 格式报告（`docs/RANGE-REAL-DATA-REPORT.md`）
- 终端彩色输出

---

### Step 3: 案例分析（深入异常）

**任务**: 如果发现异常，导出案例并分析

**触发条件**:
- Range 持续 > 20 bars
- Evolution count > 5
- Resolution distance 异常大

**实现**:
```python
def export_anomaly_case(range_event, bars, output_path):
    """导出异常 Range 案例为 fixture 格式"""
    
    # 提取相关 bars
    start_idx = find_bar_index(bars, range_event['birth_bar_dt'])
    end_idx = start_idx + range_event['duration'] + 5  # 多取 5 个
    
    case_bars = bars[start_idx:end_idx]
    
    # 生成 fixture
    fixture = {
        "fixture_id": f"ANOMALY_{range_event['birth_bar_dt']}",
        "description": f"真实数据异常案例：{range_event}",
        "source": "上证 600000 真实数据",
        "input_bars": [
            {
                "bar_dt": b.bar_dt,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close
            }
            for b in case_bars
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fixture, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 导出异常案例: {output_path}")
```

**输出**:
- `tests/fixtures/range/ANOMALY_*.json`
- 可转化为新测试用例

---

## 📊 成功标准

### 必须通过
- ✅ 所有不变量验证通过（R2, boundary_init 冻结）
- ✅ 无运行时错误或异常
- ✅ Range 诞生/resolution 次数 > 0

### 合理性检查
- ✅ Continuation/Reversal 比例在 30%-70% 之间
- ✅ 平均 Range 持续时间在 2-10 bars
- ✅ Evolution count 大部分在 0-3 之间
- ✅ 无超长 Range（> 30 bars）

### 可选
- 性能基线：200 bars 处理时间 < 100ms
- 案例库：发现 1-2 个有价值的边界案例

---

## 🚀 执行顺序

1. **Step 1 实现**（~20 分钟）
   - 修改 `test_real_data_smoke.py`
   - 运行测试验证通过

2. **Step 2 实现**（~30 分钟）
   - 创建 `analyze_range_stats.py`
   - 生成统计报告
   - 分析结果合理性

3. **Step 3 可选**（~10 分钟）
   - 仅在发现异常时执行
   - 导出 1-2 个案例

4. **总结提交**（~10 分钟）
   - 更新测试文件
   - 提交统计报告
   - 记录发现

**预计总时间**: 1-1.5 小时

---

## 📝 预期产出

### 代码变更
1. `tests/test_real_data_smoke.py` - 新增 Range 层验证
2. `analyze_range_stats.py` - 统计分析脚本（新建）

### 文档产出
1. `docs/RANGE-REAL-DATA-REPORT.md` - 统计分析报告
2. 可选：`tests/fixtures/range/ANOMALY_*.json` - 异常案例

### 知识收获
1. Range 层在真实数据上的表现特征
2. Continuation/Reversal 真实分布
3. Evolution 频率真实分布
4. 潜在优化方向

---

**准备就绪，开始执行 Step 1！** 🚀
