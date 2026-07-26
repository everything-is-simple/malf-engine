# T5 Guard 更新逻辑推导（D9 守护唯一性铁律）

**推导日期**: 2026-07-26  
**规格依据**: 规格 §2.5 / D9 守护唯一性铁律  
**推导人**: Claude Opus 4.8

---

## 规格原文

**D9 守护唯一性铁律（D9 / T3）**：
> HH/LL 推进只更新 `progress_extreme`；**只有后续确认的 HL（up）或 LH（down）才能替换 guard**。
> guard 是一个**单元素栈**——只有「回撤确认」的极值才能替换。这是 break 判定的根基，不可松动。
>
> 初始 wave 的 first guard：initial up = `H0→L1→H2>H0` 中的 L1；initial down = `L0→H1→L2<L0` 中的 H1。

**T2 方向配对**：
> up = HH推进 + HL守护；down = LL推进 + LH守护，二者必须成对

**推导目标**: 验证在 UP_ALIVE/DOWN_ALIVE 状态下，新的回撤 pivot 确认时是否正确替换 guard。

---

## 场景 A: UP_ALIVE 状态下 Guard 更新

### 初始化序列（复用第一刀模式）

使用 k=2 窗口，需要左右各 k 根 bars。

**Bars 序列**:
```
d00: O=100, H=102, L=99,  C=101
d01: O=101, H=105, L=100, C=104
d02: O=104, H=110, L=103, C=108  ← H0 extreme (110)
d03: O=108, H=107, L=104, C=105  ← H0 右侧第 1 根
d04: O=105, H=106, L=102, C=103  ← H0 confirm
d05: O=103, H=104, L=96,  C=98   ← L1 extreme (96)
d06: O=98,  H=101, L=97,  C=100  ← L1 右侧第 1 根
d07: O=100, H=103, L=98,  C=102  ← L1 confirm
d08: O=102, H=108, L=101, C=107
d09: O=107, H=114, L=106, C=112  ← H2 extreme (114)
d10: O=112, H=111, L=108, C=109  ← H2 右侧第 1 根
d11: O=109, H=110, L=106, C=108  ← H2 confirm → UP_ALIVE
```

**Pivot 序列**:
- H0: price=110, extreme_bar_dt=d02, confirm_bar_dt=d04
- L1: price=96,  extreme_bar_dt=d05, confirm_bar_dt=d07
- H2: price=114, extreme_bar_dt=d09, confirm_bar_dt=d11

**d11 快照（初始化完成）**:
- system_state = UP_ALIVE
- direction = UP
- wave_core_state = ALIVE
- current_effective_guard_price = 96 (L1)
- current_effective_guard_extreme_bar_dt = d05
- current_effective_guard_confirm_bar_dt = d07
- progress_extreme_price = 114 (H2)
- progress_extreme_bar_dt = d09

### Guard 更新场景

继续喂入新 bars，产生 **L3 = 98**（新的 L pivot）。

**新 Bars 序列**:
```
d12: O=108, H=110, L=105, C=107
d13: O=107, H=108, L=98,  C=102  ← L3 extreme (98)
d14: O=102, H=106, L=100, C=104  ← L3 右侧第 1 根
d15: O=104, H=107, L=102, C=105  ← L3 confirm
```

**新 Pivot**:
- L3: price=98, extreme_bar_dt=d13, confirm_bar_dt=d15

**关键推导**:

1. **d13**: L3 extreme 发生，但尚未确认
   - system_state = UP_ALIVE
   - guard = 96 (不变)
   - progress = 114 (不变)

2. **d14**: L3 右侧第 1 根
   - system_state = UP_ALIVE
   - guard = 96 (不变)
   - progress = 114 (不变)

3. **d15**: L3 confirm（关键时刻）
   - **触发 D9 Guard 更新**：L3 是回撤 pivot（L in UP_ALIVE）
   - system_state = UP_ALIVE（仍然 alive，未 break）
   - **current_effective_guard_price = 98**（L3 替换 L1）
   - current_effective_guard_extreme_bar_dt = d13
   - current_effective_guard_confirm_bar_dt = d15
   - progress_extreme_price = 114（不受影响，D9：guard 和 progress 独立）
   - progress_extreme_bar_dt = d09

**验证点**:
- ✅ Guard 从 96 更新为 98
- ✅ Guard 的时间戳指向 L3
- ✅ system_state 仍为 UP_ALIVE（98 > 96，未突破原 guard，不触发 break）
- ✅ progress 不受影响（D9 铁律）

---

## 场景 B: DOWN_ALIVE 状态下 Guard 更新

### 初始化序列（对称 UP 方向）

**Bars 序列**:
```
d00: O=95, H=98,  L=94,  C=96
d01: O=96, H=97,  L=92,  C=93
d02: O=93, H=95,  L=90,  C=92   ← L0 extreme (90)
d03: O=92, H=96,  L=91,  C=95   ← L0 右侧第 1 根
d04: O=95, H=98,  L=94,  C=97   ← L0 confirm
d05: O=97, H=100, L=96,  C=98   ← H1 extreme (100)
d06: O=98, H=99,  L=95,  C=96   ← H1 右侧第 1 根
d07: O=96, H=97,  L=94,  C=95   ← H1 confirm
d08: O=95, H=94,  L=88,  C=90
d09: O=90, H=91,  L=80,  C=82   ← L2 extreme (80)
d10: O=82, H=86,  L=81,  C=84   ← L2 右侧第 1 根
d11: O=84, H=87,  L=83,  C=85   ← L2 confirm → DOWN_ALIVE
```

**Pivot 序列**:
- L0: price=90,  extreme_bar_dt=d02, confirm_bar_dt=d04
- H1: price=100, extreme_bar_dt=d05, confirm_bar_dt=d07
- L2: price=80,  extreme_bar_dt=d09, confirm_bar_dt=d11

**d11 快照（初始化完成）**:
- system_state = DOWN_ALIVE
- direction = DOWN
- current_effective_guard_price = 100 (H1)
- progress_extreme_price = 80 (L2)

### Guard 更新场景

继续喂入新 bars，产生 **H3 = 95**（新的 H pivot）。

**新 Bars 序列**:
```
d12: O=85, H=87,  L=82,  C=84
d13: O=84, H=95,  L=83,  C=92   ← H3 extreme (95)
d14: O=92, H=94,  L=89,  C=91   ← H3 右侧第 1 根
d15: O=91, H=93,  L=88,  C=90   ← H3 confirm
```

**新 Pivot**:
- H3: price=95, extreme_bar_dt=d13, confirm_bar_dt=d15

**关键推导**:

1. **d15**: H3 confirm（关键时刻）
   - **触发 D9 Guard 更新**：H3 是回撤 pivot（H in DOWN_ALIVE）
   - system_state = DOWN_ALIVE（仍然 alive，未 break）
   - **current_effective_guard_price = 95**（H3 替换 H1）
   - current_effective_guard_extreme_bar_dt = d13
   - current_effective_guard_confirm_bar_dt = d15
   - progress_extreme_price = 80（不受影响）

**验证点**:
- ✅ Guard 从 100 更新为 95
- ✅ Guard 的时间戳指向 H3
- ✅ system_state 仍为 DOWN_ALIVE（95 < 100，未突破原 guard，不触发 break）
- ✅ progress 不受影响

---

## 场景 C: Guard 不应更新的情况（反例）

### C1: UP_ALIVE 状态下，H pivot 不更新 guard

**初始状态**: guard=96, progress=114

**新 Pivot**: H3 = 120（新的 H pivot，推进 progress）

**预期行为**:
- ✅ progress_extreme_price 更新为 120（D16 已实现）
- ✅ current_effective_guard_price 保持 96（**不变**，因为 H 不是回撤 pivot）

**推导依据**: D9 铁律 + T2 方向配对
- UP wave: HH 推进（只更新 progress），HL 守护（才更新 guard）
- H pivot 是 HH 关系，只更新 progress

### C2: Guard 是单元素栈（替换，不是并存）

**初始状态**: guard=L1=96

**序列**:
1. L3=98 confirm → guard 更新为 98（替换 L1）
2. L4=99 confirm → guard 更新为 99（替换 L3，不是并存）

**预期行为**:
- ✅ 每次只有一个 current_effective_guard
- ✅ 新的回撤 pivot 直接替换旧的 guard
- ✅ 旧 guard（L1, L3）不再影响 break 判定

---

## 测试用例设计

基于以上推导，设计 4 个单元测试：

### Test 1: `test_guard_update_up_alive`
- **场景**: 场景 A
- **验证**: UP_ALIVE 状态下，L3 替换 L1 为 guard

### Test 2: `test_guard_update_down_alive`
- **场景**: 场景 B
- **验证**: DOWN_ALIVE 状态下，H3 替换 H1 为 guard

### Test 3: `test_guard_no_update_on_progress_pivot`
- **场景**: 场景 C1
- **验证**: UP_ALIVE 状态下，H pivot 不更新 guard

### Test 4: `test_guard_replaces_previous_guard`
- **场景**: 场景 C2
- **验证**: Guard 是单元素栈，新 guard 替换旧 guard

---

## 实现要点

### 调用时机
在 `on_bar()` 的 S3 分支（UP_ALIVE/DOWN_ALIVE）：
```python
if bar.bar_dt in pivots_by_confirm_dt:
    new_pivot = pivots_by_confirm_dt[bar.bar_dt]
    self._update_progress_if_better(new_pivot)  # D16 已实现
    self._update_guard_if_valid(new_pivot)      # D9 新增
```

### 方法签名
```python
def _update_guard_if_valid(self, new_pivot: Pivot) -> None:
    """D9 守护唯一性铁律: 更新 guard（如果新 pivot 是回撤类型）。
    
    规则（D9）：
    - UP wave: 只有新 L pivot（回撤）才能替换 guard
    - DOWN wave: 只有新 H pivot（回撤）才能替换 guard
    - Guard 是单元素栈，新的回撤 pivot 直接替换旧的
    """
```

### 对称实现
```python
if self._system_state == SystemState.UP_ALIVE:
    if new_pivot.pivot_type == PivotType.L:
        self._guard_price = new_pivot.price
        self._guard_extreme_bar_dt = new_pivot.extreme_bar_dt
        self._guard_confirm_bar_dt = new_pivot.confirm_bar_dt
elif self._system_state == SystemState.DOWN_ALIVE:
    if new_pivot.pivot_type == PivotType.H:
        self._guard_price = new_pivot.price
        self._guard_extreme_bar_dt = new_pivot.extreme_bar_dt
        self._guard_confirm_bar_dt = new_pivot.confirm_bar_dt
```

---

## 推导完成确认

- ✅ 场景 A（UP guard 更新）推导完成
- ✅ 场景 B（DOWN guard 更新）推导完成
- ✅ 反例场景（C1, C2）推导完成
- ✅ 测试用例设计完成
- ✅ 实现要点明确

**下一步**: S5-T1-2 写单元测试（TDD RED）

---

**推导完成日期**: 2026-07-26  
**验证人**: 待测试验证
