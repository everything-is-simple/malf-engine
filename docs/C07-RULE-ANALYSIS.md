# C-07 规则分析：早期 Pivot 替换

**文档目的**: 理解 C-07 规则的替换逻辑，为实现提供清晰的指导

**规则来源**: MALF v2.1 Core §3 初始化判定，`src/malf/initialization.py` 注释

---

## 问题背景

### 当前状态

初始化判定需要识别 3 个 pivot 的特定模式：
- **UP 方向**: H0 → L1 → H2, 其中 H2 > H0
- **DOWN 方向**: L0 → H1 → L2, 其中 L2 < L0

**问题**: 在确认完整序列之前，可能出现"同类型"pivot 的重复：

1. **H0/L0 替换**（C-07 主场景）:
   - H0 确认后、L1 确认前，又出现第二个 H
   - L0 确认后、H1 确认前，又出现第二个 L

2. **L1/H1 替换**（C-07 扩展场景）:
   - L1 确认后、H2 确认前，又出现第二个 L
   - H1 确认后、L2 确认前，又出现第二个 H

### 真实场景示例

**offset=0 真实数据错误**:
```
Error: L0 之后、H1 确认前出现第二个 L（【填洞 C-07】替换场景）暂未实现
Bar 12: 触发条件
```

这是真实市场数据中会遇到的场景，不是边缘情况。

---

## C-07 规则定义

### 规则名称
**C-07: 早期 Pivot 替换规则**

### 适用阶段
UNINITIALIZED 阶段，尚未确认初始波段（< 3 confirmed pivots）

### 规则内容

#### 场景 1: H0 替换
**条件**:
- 已确认 H0（第一个 H pivot）
- 尚未确认 L1（等待第一个 L pivot）
- 新确认一个 H pivot

**判定**:
- 如果新 H 的 price **> H0.price**: **替换** H0
- 如果新 H 的 price **≤ H0.price**: **忽略**

**替换操作**:
1. 用新 H 替换 H0 位置
2. 重置后续候选（L1 候选范围重新开始）
3. 继续等待 L1

#### 场景 2: L0 替换
**条件**:
- 已确认 L0（第一个 L pivot）
- 尚未确认 H1（等待第一个 H pivot）
- 新确认一个 L pivot

**判定**:
- 如果新 L 的 price **< L0.price**: **替换** L0
- 如果新 L 的 price **≥ L0.price**: **忽略**

**替换操作**:
1. 用新 L 替换 L0 位置
2. 重置后续候选（H1 候选范围重新开始）
3. 继续等待 H1

#### 场景 3: L1 替换
**条件**:
- 已确认 H0 和 L1（UP 方向序列）
- 尚未确认 H2（等待突破 H0 的 H）
- 新确认一个 L pivot

**判定**:
- 如果新 L 的 price **< L1.price**: **替换** L1（更新 guard 候选）
- 如果新 L 的 price **≥ L1.price**: **忽略**

**替换操作**:
1. 用新 L 替换 L1 位置
2. L1 作为 guard 候选，选择最低点合理
3. 继续等待 H2

#### 场景 4: H1 替换
**条件**:
- 已确认 L0 和 H1（DOWN 方向序列）
- 尚未确认 L2（等待突破 L0 的 L）
- 新确认一个 H pivot

**判定**:
- 如果新 H 的 price **> H1.price**: **替换** H1（更新 guard 候选）
- 如果新 H 的 price **≤ H1.price**: **忽略**

**替换操作**:
1. 用新 H 替换 H1 位置
2. H1 作为 guard 候选，选择最高点合理
3. 继续等待 L2

---

## 替换语义

### 核心原则：选择"更极端"的 pivot

替换的本质是：**在序列完整前，动态更新"最极端"的 pivot**

- **H0/L0**: 寻找初始趋势的起点，选择"最极端"作为参考基准
  - H0 应该是"最高"的高点
  - L0 应该是"最低"的低点

- **L1/H1**: 寻找反转的极值点，作为 guard 候选
  - L1（UP 方向 guard）应该是"最低"的低点
  - H1（DOWN 方向 guard）应该是"最高"的高点

### 候选范围重置

**关键设计决策**: 替换 H0/L0 后，后续候选范围如何界定？

**方案 A（保守）**: 只认替换点**之后**的 pivot
- 优点：时序严格，符合单遍处理
- 缺点：可能错过替换前已确认的更好候选

**方案 B（激进）**: 允许使用替换前已确认的 pivot
- 优点：充分利用历史信息
- 缺点：违反单遍处理，需要回溯

**本实现选择**: **方案 A（保守）**
- 理由：保持单遍处理特性，确定性优先
- 实现：替换时不回看历史 pivot，从替换点继续前进

---

## 实现策略

### 数据结构

在 `find_initial_wave()` 中，使用状态机追踪：

```python
# 状态变量
first_pivot: Optional[Pivot] = None      # H0 or L0
second_pivot: Optional[Pivot] = None     # L1 or H1

# 遍历 pivots_in_confirm_order
for p in pivots_in_confirm_order:
    if first_pivot is None:
        first_pivot = p
        continue
    
    if second_pivot is None:
        # 检查是否同类型（触发替换）
        if p.pivot_type == first_pivot.pivot_type:
            # 场景 1/2: H0/L0 替换
            if should_replace(p, first_pivot):
                first_pivot = p  # 替换
            # else: 忽略
            continue
        else:
            second_pivot = p  # 确认第二个 pivot
            continue
    
    # second_pivot 已定，等待第三个
    if p.pivot_type == second_pivot.pivot_type:
        # 场景 3/4: L1/H1 替换
        if should_replace(p, second_pivot):
            second_pivot = p  # 替换
        # else: 忽略
        continue
    
    # p 是第三个 pivot，检查初始化条件
    if check_initialization_condition(first_pivot, second_pivot, p):
        return InitialWaveResult(confirmed=True, ...)
```

### 替换判定函数

```python
def should_replace(new_pivot: Pivot, old_pivot: Pivot) -> bool:
    """判断是否应该用 new_pivot 替换 old_pivot"""
    assert new_pivot.pivot_type == old_pivot.pivot_type
    
    if new_pivot.pivot_type == PivotType.H:
        # H pivot: 更高则替换
        return new_pivot.price > old_pivot.price
    else:
        # L pivot: 更低则替换
        return new_pivot.price < old_pivot.price
```

---

## 测试用例设计

### 测试覆盖矩阵

| 场景 | 方向 | 替换位置 | 是否替换 | 最终结果 | Fixture |
|------|------|---------|---------|---------|---------|
| C07-1 | DOWN | L0 | 是（更低） | 初始化成功 | `c07_l0_replacement.json` |
| C07-2 | UP | H0 | 是（更高） | 初始化成功 | `c07_h0_replacement.json` |
| C07-3 | UP | L1 | 是（更低） | 初始化成功 | `c07_l1_replacement.json` |
| C07-4 | DOWN | H1 | 是（更高） | 初始化成功 | `c07_h1_replacement.json` |

### Fixture 结构示例：C07-1 (L0 替换)

```json
{
  "name": "C07-1: L0 替换（DOWN 方向）",
  "bars": [
    {"bar_dt": "d01", "high": 150, "low": 100},  // L0_old @ 100 (确认 @ d03)
    {"bar_dt": "d02", "high": 140, "low": 110},
    {"bar_dt": "d03", "high": 130, "low": 105},  // L0_old 确认
    {"bar_dt": "d04", "high": 125, "low": 90},   // L0_new @ 90 (更低，替换)
    {"bar_dt": "d05", "high": 135, "low": 100},
    {"bar_dt": "d06", "high": 160, "low": 110},  // H1 @ 160 (确认 @ d08)
    {"bar_dt": "d07", "high": 150, "low": 115},
    {"bar_dt": "d08", "high": 145, "low": 120},  // H1 确认
    {"bar_dt": "d09", "high": 130, "low": 80},   // L2 @ 80 < L0_new (90)
    {"bar_dt": "d10", "high": 125, "low": 85},
    {"bar_dt": "d11", "high": 120, "low": 90}    // L2 确认，初始化成功
  ],
  "expected_snapshots": {
    "d11": {
      "system_state": "down_alive",
      "guard_price": 160,           // H1
      "progress_extreme_price": 80  // L2
    }
  }
}
```

**关键验证点**:
1. L0 @ 100 确认后，L0_new @ 90 替换成功
2. 最终初始化判定基于 L0_new (90)，不是 L0_old (100)
3. L2 (80) < L0_new (90) 触发 DOWN 初始化

---

## 边界情况

### 1. 多次替换
**场景**: H0 → H0' → H0'' → L1 → H2
- 每次都选择"更极端"的
- 最终 H0 = max(H0, H0', H0'')

### 2. 替换后不满足初始化条件
**场景**: L0_old @ 100 → L0_new @ 90 → H1 @ 120 → L2 @ 95
- L2 (95) >= L0_new (90)，不满足初始化条件
- 继续等待下一个 L pivot

### 3. 不替换的情况
**场景**: H0 @ 150 → H_new @ 140（更低）
- 不替换，忽略 H_new
- 继续用 H0 @ 150

### 4. 无替换的干净序列
**场景**: H0 → L1 → H2（无重复类型）
- 现有逻辑已覆盖，无需改动

---

## 实现检查清单

- [ ] 实现 `should_replace()` 判定函数
- [ ] 修改 UP 方向逻辑：支持 H0 和 L1 替换
- [ ] 修改 DOWN 方向逻辑：支持 L0 和 H1 替换
- [ ] 移除 4 处 `NotImplementedError`
- [ ] 创建 4 个测试 fixtures（C07-1/2/3/4）
- [ ] 编写 4 个单元测试用例
- [ ] 验证 offset=0 真实数据不再报错
- [ ] 更新文档：标记 C-07 已实现

---

## 规格模糊点与设计决策

### 模糊点 1: 候选范围重置
**规格**: "更高的 H 可替换 H0，且替换后需重新评估条件"
**模糊**: 是否可以使用替换前的 pivot 作为 L1 候选？
**决策**: 否，只认替换后的 pivot（保持单遍处理）

### 模糊点 2: L1/H1 替换
**规格**: 完全未提及 L1/H1 是否可替换
**决策**: 允许替换，语义与 H0/L0 一致（选择最极端的 guard 候选）

### 设计原则
1. **确定性**: 相同输入序列产生相同输出
2. **单遍处理**: 不回溯，从左到右扫描
3. **极值优先**: 选择"最极端"的 pivot 作为参考点

---

**文档版本**: v1.0  
**创建日期**: 2026-07-26  
**状态**: 待实现
