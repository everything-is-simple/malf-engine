# Range 层使用指南

**版本**: MALF v2.1  
**更新日期**: 2026-07-26  
**目标读者**: malf-engine 使用者

---

## 📖 概念介绍

### 什么是 Range？

**Range** 是 MALF v2.1 定义的市场结构特征，表示波段终止后进入的震荡区间。

**生命周期**：
```
Wave ALIVE → Guard Break → TRANSITION (Range alive) → Resolution → New Wave ALIVE
```

**关键时刻**：
1. **Range 诞生**（Birth）：Guard break 时刻，系统进入 TRANSITION
2. **Range 演化**（Evolution）：TRANSITION 期间 pivot 突破 boundary_now
3. **Range 解决**（Resolution）：Pivot 突破 boundary_init，确认新波段方向

---

## 🎯 核心概念

### 1. Boundary（边界）

Range 有**两套边界**：

#### boundary_init（判定边界）
- **定义**：Range 诞生时从 transition_boundary 继承，**永不改变**
- **用途**：Resolution 判定（T6 定理）
- **字段**：
  - `range_boundary_init_high`: 冻结上界
  - `range_boundary_init_low`: 冻结下界

#### boundary_now（统计边界）
- **定义**：TRANSITION 期间动态扩张的边界
- **用途**：统计分析、可视化
- **字段**：
  - `range_boundary_now_high`: 演化上界（只增不减）
  - `range_boundary_now_low`: 演化下界（只减不增）

**R2 不变量**：`boundary_now` 始终包含 `boundary_init`
```python
assert snapshot.range_boundary_now_high >= snapshot.range_boundary_init_high
assert snapshot.range_boundary_now_low <= snapshot.range_boundary_init_low
```

### 2. Evolution（演化）

**定义**：TRANSITION 期间，pivot 突破 `boundary_now` 时触发

**条件**：
- H pivot: `price > boundary_now.high` → 演化，`evolution_count += 1`
- L pivot: `price < boundary_now.low` → 演化，`evolution_count += 1`

**注意**：
- 演化**不影响** Resolution 判定（仍基于 `boundary_init`）
- `evolution_count` 用于统计分析，反映 TRANSITION 期间的波动强度

### 3. Resolution（解决）

**定义**：Pivot 突破 `boundary_init`，确认新波段方向

**T6 定理**（判定规则）：
```python
if direction == DOWN and pivot_type == L and price < boundary_init.low:
    resolution_type = "continuation"  # 延续向下
elif direction == DOWN and pivot_type == H and price > boundary_init.high:
    resolution_type = "reversal"      # 反转向上
# UP 方向对称
```

**Resolution Distance**：
```python
# DOWN continuation: 负值（向下突破距离）
distance = price - boundary_init.low  # e.g., 85 - 96 = -11

# UP continuation: 正值（向上突破距离）
distance = price - boundary_init.high  # e.g., 125 - 120 = 5
```

---

## 💻 使用示例

### 示例 1: 检测 Range 诞生

```python
from malf.core_engine import MALFCoreEngine
from malf.types import PriceBar, SystemState

engine = MALFCoreEngine(k=2)

for bar in bars:
    snapshot = engine.on_bar(bar)
    
    # 检测 Range 诞生
    if snapshot.range_birth_bar_dt == snapshot.bar_dt:
        print(f"Range born at {snapshot.bar_dt}")
        print(f"  Direction: {snapshot.direction.value}")
        print(f"  Boundary init: [{snapshot.range_boundary_init_high}, "
              f"{snapshot.range_boundary_init_low}]")
```

### 示例 2: 跟踪 Range 演化

```python
if snapshot.system_state == SystemState.TRANSITION:
    print(f"TRANSITION at {snapshot.bar_dt}")
    print(f"  Evolution count: {snapshot.range_evolution_count}")
    print(f"  Boundary now: [{snapshot.range_boundary_now_high}, "
          f"{snapshot.range_boundary_now_low}]")
    
    # 计算边界扩张率
    init_width = (snapshot.range_boundary_init_high - 
                  snapshot.range_boundary_init_low)
    now_width = (snapshot.range_boundary_now_high - 
                 snapshot.range_boundary_now_low)
    expansion = (now_width - init_width) / init_width * 100
    print(f"  Expansion: {expansion:.1f}%")
```

### 示例 3: 捕获 Resolution

```python
if snapshot.range_resolution_bar_dt == snapshot.bar_dt:
    print(f"Range resolved at {snapshot.bar_dt}")
    print(f"  Type: {snapshot.range_resolution_type}")
    print(f"  Distance: {snapshot.range_resolution_distance}")
    print(f"  New state: {snapshot.system_state.value}")
    
    # 根据 resolution 类型决策
    if snapshot.range_resolution_type == "continuation":
        print("  -> Trend continues in same direction")
    elif snapshot.range_resolution_type == "reversal":
        print("  -> Trend reverses direction")
```

### 示例 4: Range 统计分析

```python
range_events = []

for bar in bars:
    snapshot = engine.on_bar(bar)
    
    # 收集 Range 事件
    if snapshot.range_resolution_bar_dt == snapshot.bar_dt:
        range_events.append({
            'birth': snapshot.range_birth_bar_dt,
            'resolution': snapshot.range_resolution_bar_dt,
            'type': snapshot.range_resolution_type,
            'evolution_count': snapshot.range_evolution_count,
            'distance': snapshot.range_resolution_distance,
        })

# 统计分析
total = len(range_events)
continuation_count = sum(1 for e in range_events 
                        if e['type'] == 'continuation')
reversal_count = sum(1 for e in range_events 
                     if e['type'] == 'reversal')

print(f"Total Ranges: {total}")
print(f"Continuation: {continuation_count} ({continuation_count/total*100:.1f}%)")
print(f"Reversal: {reversal_count} ({reversal_count/total*100:.1f}%)")
```

---

## 🔍 字段参考

### Range 层字段（`CoreStateSnapshot`）

| 字段 | 类型 | 说明 | 何时有效 |
|------|------|------|----------|
| `range_birth_bar_dt` | `Optional[str]` | Range 诞生时刻（bar_dt） | TRANSITION 时 |
| `range_boundary_init_high` | `Optional[int]` | 冻结上界（判定用） | TRANSITION 时 |
| `range_boundary_init_low` | `Optional[int]` | 冻结下界（判定用） | TRANSITION 时 |
| `range_boundary_now_high` | `Optional[int]` | 演化上界（统计用） | TRANSITION 时 |
| `range_boundary_now_low` | `Optional[int]` | 演化下界（统计用） | TRANSITION 时 |
| `range_evolution_count` | `int` | 演化次数 | 始终有效（默认 0） |
| `range_resolution_bar_dt` | `Optional[str]` | Resolution 确认时刻 | Resolution 后 |
| `range_resolution_type` | `Optional[str]` | `"continuation"` 或 `"reversal"` | Resolution 后 |
| `range_resolution_distance` | `Optional[int]` | 突破距离（有符号） | Resolution 后 |

---

## ❓ FAQ

### Q1: 为什么有两套 boundary？

**A**: 分离判定逻辑和统计逻辑
- `boundary_init` 用于 Resolution 判定（T6 定理），必须冻结以保持判定一致性
- `boundary_now` 用于统计分析和可视化，反映 TRANSITION 期间的实际波动范围

### Q2: Evolution 和 Resolution 有什么区别？

**A**: 
- **Evolution**：边界扩张，`evolution_count` 增加，但系统仍处于 TRANSITION
- **Resolution**：突破 `boundary_init`，系统离开 TRANSITION，进入新的 Wave ALIVE

### Q3: Continuation 和 Reversal 如何区分？

**A**: 基于突破方向与原波段方向的关系
- **Continuation**：突破方向与原波段方向一致（DOWN→DOWN 或 UP→UP）
- **Reversal**：突破方向与原波段方向相反（DOWN→UP 或 UP→DOWN）

### Q4: Range 持续多久是正常的？

**A**: 基于真实数据验证（上证 600000, 200 bars）：
- 平均持续：26 bars
- 范围：13-33 bars
- 长期 Range（>30 bars）占 2/3，说明真实市场震荡期较长

### Q5: Evolution count 一般是多少？

**A**: 基于真实数据：
- 平均：1-2 次
- 合成测试多为 2 次
- 真实数据平均 1 次（市场波动相对渐进）

### Q6: Resolution distance 的符号含义？

**A**:
- **正值**：向上突破（价格 > boundary_init.high）
- **负值**：向下突破（价格 < boundary_init.low）
- 绝对值越大，突破力度越强

### Q7: 如何判断 Range 字段是否有效？

**A**: 检查 `system_state`
```python
if snapshot.system_state == SystemState.TRANSITION:
    # Range 字段（除 resolution 外）有效
    assert snapshot.range_birth_bar_dt is not None
    assert snapshot.range_boundary_init_high is not None
```

### Q8: Range 层有哪些不变量？

**A**: 
1. **R2 不变量**：`boundary_now` 单调扩张（包含 `boundary_init`）
2. **boundary_init 冻结**：Range 诞生后永不改变
3. **evolution_count 单调**：只增不减
4. **Resolution 唯一性**：一个 Range 只有一次 Resolution

---

## 📊 真实数据表现

基于上证 600000（浦发银行）200 bars 验证：

| 指标 | 值 |
|------|-----|
| Range 密度 | 1.5% (每 67 bars 一个) |
| 平均持续 | 26 bars |
| Continuation 比例 | 66.7% |
| Reversal 比例 | 33.3% |
| 平均演化次数 | 1.0 |
| 边界扩张率 | 26%-59% (平均 40%) |

详见 `docs/RANGE-REAL-DATA-REPORT.md`。

---

## 🚀 最佳实践

### 1. 监控 Range 诞生
```python
if snapshot.range_birth_bar_dt == snapshot.bar_dt:
    # 记录 Range 起始状态
    log_range_birth(snapshot)
```

### 2. 验证 R2 不变量（调试用）
```python
if snapshot.system_state == SystemState.TRANSITION:
    assert snapshot.range_boundary_now_high >= snapshot.range_boundary_init_high
    assert snapshot.range_boundary_now_low <= snapshot.range_boundary_init_low
```

### 3. 使用 Resolution 信号
```python
if snapshot.range_resolution_bar_dt == snapshot.bar_dt:
    if snapshot.range_resolution_type == "continuation":
        # 趋势延续，加仓
        pass
    elif snapshot.range_resolution_type == "reversal":
        # 趋势反转，减仓或反向
        pass
```

### 4. 统计分析
```python
# 定期生成 Range 统计报告
analyze_range_statistics(range_events)
```

---

## 📚 相关文档

- **API 参考**: `docs/API.md`
- **设计文档**: `docs/T6-DAY-0-COMPLETION.md`
- **实现报告**: `docs/T6-DAY-1-REPORT.md`
- **测试扩展**: `docs/T6-DAY-2-REPORT.md`
- **真实数据验证**: `docs/RANGE-REAL-DATA-VALIDATION-COMPLETE.md`
- **统计报告**: `docs/RANGE-REAL-DATA-REPORT.md`

---

**最后更新**: 2026-07-26  
**Range 层版本**: v2.1  
**状态**: 生产就绪 ✅
