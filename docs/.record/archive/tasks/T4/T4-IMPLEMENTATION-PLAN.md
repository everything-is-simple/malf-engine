# 第四刀实施计划：Transition 期间 Active Candidate 演化

## 目标

实现 transition 状态下的 active candidate 演化逻辑，包括：
- Active candidate 跟踪
- Candidate 替换（O4/T5 规则）
- New wave 确认（T6 双条件）

## 规格依据

**核心规则**（规格 §2.7）：

### 1. 双边界（D12）
| 旧波方向 | boundary_high | boundary_low |
|---|---|---|
| 旧 up wave break | old final HH price | broken HL price |
| 旧 down wave break | broken LH price | old final LL price |

### 2. Candidate 替换（O4/T5）
- `active_candidate = latest candidate_guard`
- 新候选一出现就替换旧的，**不分同向反向**（flip-flop）
- `candidate_replacement_count` 计所有替换事件

### 3. New Wave 双条件（D16/D17/T6）
| 方向 | progress confirmation | 严格性 |
|---|---|---|
| up | active candidate L 之后 H 且 `H > boundary_high` | 严格 `>` |
| down | active candidate H 之后 L 且 `L < boundary_low` | 严格 `<` |

**缺一不可**：active_candidate_guard 存在 **且** 其后 confirmation 严格突破对侧边界。

### 4. 关键约束（C-05）
Break bar 自身的极值**不进** transition 的 candidate 逻辑。Transition 的 candidate 从 break bar **之后**的已确认 pivot 开始计。

### 5. Confirmation 时序（C-02）
D16「之后」= 严格 `bar_dt(candidate) < bar_dt(confirmation)`。同一根 bar 的 high 不能既是 candidate 又是 confirmation。

## 实施步骤

### Step 1: 扩展数据结构 ✓
**目标**：添加 transition 相关字段到 CoreStateSnapshot

**新增字段**：
```python
# Transition 状态字段
transition_boundary_high: Optional[int] = None
transition_boundary_low: Optional[int] = None
active_candidate_guard_price: Optional[int] = None
active_candidate_guard_extreme_bar_dt: Optional[str] = None
active_candidate_guard_confirm_bar_dt: Optional[str] = None
active_candidate_direction: Optional[Direction] = None
candidate_replacement_count: int = 0
```

**文件**：`src/malf/types.py::CoreStateSnapshot`

### Step 2: Golden Fixture 设计
**目标**：人肉推导 transition 演化场景

#### 场景 A：UP → transition → L0 candidate
```
序列：H0→L1→H2>H0 (up_alive) → bar breaks guard → L0 candidate appears
验证：
- boundary_high = H2.price (old final HH)
- boundary_low = L1.price (broken guard)
- active_candidate = L0 (第一个反向 pivot)
- active_candidate_direction = DOWN
```

#### 场景 B：L0 → L0' 替换（flip-flop，同向）
```
序列：基于场景 A，出现 L0' < L0
验证：
- active_candidate 从 L0 替换为 L0'
- candidate_replacement_count += 1
```

#### 场景 C：L0 → H1（flip-flop，反向）
```
序列：基于场景 A，出现 H1
验证：
- active_candidate 从 L0 (DOWN) 切换为 H1 (UP)
- candidate_replacement_count += 1
```

#### 场景 D：New wave 确认
```
序列：L0 confirmed → H1 appears → H1 > boundary_high
验证：
- 触发 new up wave
- system_state → up_alive
- new wave 起点 = H1
```

**文件**：
- `tests/fixtures/t4_transition_l0_candidate.json`
- `tests/fixtures/t4_transition_l0_replacement.json`
- `tests/fixtures/t4_transition_flip_flop.json`
- `tests/fixtures/t4_transition_new_wave.json`

### Step 3: 写测试（RED）
**目标**：测试驱动开发

**单元测试**：`tests/test_transition_candidate.py`
- `test_boundary_calculation_up_break`
- `test_boundary_calculation_down_break`
- `test_first_candidate_detection`
- `test_candidate_replacement_same_direction`
- `test_candidate_flip_flop_opposite_direction`
- `test_new_wave_confirmation_with_candidate`
- `test_new_wave_no_confirmation_without_candidate`

**端到端测试**：`tests/test_t4_transition_evolution.py`
- `test_t4_transition_l0_candidate_end_to_end`
- `test_t4_transition_l0_replacement_end_to_end`
- `test_t4_transition_flip_flop_end_to_end`
- `test_t4_transition_new_wave_end_to_end`

### Step 4: 实现逻辑（GREEN）
**目标**：实现 transition 演化

**文件**：`src/malf/core_engine.py`

**新增方法**：
```python
def _calculate_boundaries(self) -> tuple[int, int]:
    """计算 transition 双边界（D12）"""
    
def _update_active_candidate(self, bar: PriceBar, new_pivots: List[Pivot]) -> None:
    """更新 active candidate（O4/T5 flip-flop）"""
    
def _check_new_wave_confirmation(self, bar: PriceBar, new_pivots: List[Pivot]) -> bool:
    """检查 new wave 确认（T6 双条件）"""
```

**修改**：
```python
def on_bar(self, bar: PriceBar) -> CoreStateSnapshot:
    # ... existing code ...
    
    # S3: Guard break detection
    elif self._system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
        if self._check_guard_break(bar):
            # 计算双边界
            self._transition_boundary_high, self._transition_boundary_low = self._calculate_boundaries()
            self._system_state = SystemState.TRANSITION
            self._wave_core_state = WaveCoreState.TERMINATED
            # 初始化 candidate 状态
            self._active_candidate_guard_price = None
            self._candidate_replacement_count = 0
    
    # S4: Transition 期间 active candidate 演化（新增）
    elif self._system_state == SystemState.TRANSITION:
        # 检测新的 pivots（从 break bar 之后开始）
        new_pivots_this_bar = [p for p in all_pivots if p.confirm_bar_dt == bar.bar_dt]
        
        # 更新 active candidate（flip-flop）
        self._update_active_candidate(bar, new_pivots_this_bar)
        
        # 检查 new wave 确认
        if self._check_new_wave_confirmation(bar, new_pivots_this_bar):
            # 进入 new wave（方向由 confirmation 决定）
            pass
```

### Step 5: 真实数据验证
**目标**：验证 bar 12 的 L0 替换场景能正确处理

**文件**：`tests/test_real_data_smoke.py`

**新增测试**：
```python
def test_sh600000_with_transition_evolution():
    """真实数据冒烟：验证 transition 演化不崩溃"""
    # 处理前 200 bars
    # 验证：
    # - 能进入 transition 状态
    # - 能正确跟踪 active candidate
    # - 不抛未预期异常
    # - 记录 candidate_replacement_count
```

### Step 6: 文档回补
**目标**：满足铁律 7

**文件更新**：
1. `docs/BUILD-PLAN.md`：添加第四刀章节，标记步骤完成
2. `src/malf/core_engine.py` docstring：更新范围声明
3. `docs/DAILY-LOG-2026-07-26.md`（或新建 2026-07-27.md）：记录实施过程
4. `docs/T4-COMPLETION-SUMMARY.md`：完成总结

## 对称性设计

### UP → transition
- 旧波：up_alive (H0→L1→H2>H0)
- Break: close < L1 (guard)
- boundary_high = H2 (old final HH)
- boundary_low = L1 (broken guard)
- 跟踪 candidate: L pivots (反向，DOWN)
- New wave 条件: 
  - active candidate L 存在
  - 之后出现 H > boundary_high (UP wave)
  - 或之后出现 L < boundary_low (DOWN wave)

### DOWN → transition
- 旧波：down_alive (L0→H1→L2<L0)
- Break: close > H1 (guard)
- boundary_high = H1 (broken guard)
- boundary_low = L2 (old final LL)
- 跟踪 candidate: H pivots (反向，UP)
- New wave 条件:
  - active candidate H 存在
  - 之后出现 L < boundary_low (DOWN wave)
  - 或之后出现 H > boundary_high (UP wave)

## 遵循的铁律

- ✓ **铁律 1**：窗口填充充足
- ✓ **铁律 2**：Pivot 确认严格不等式
- ✓ **铁律 3**：人肉推导工具辅助（创建 debug_t4.py）
- ✓ **铁律 4**：Fixture 先于实现
- ✓ **铁律 5**：对称实现优先
- ✓ **铁律 6**：真实数据冒烟
- ✓ **铁律 7**：文档回补

## 完成标志

第四刀 done = 单元测试绿 + 端到端测试绿 + 真实数据冒烟通过 + 三份文档更新
