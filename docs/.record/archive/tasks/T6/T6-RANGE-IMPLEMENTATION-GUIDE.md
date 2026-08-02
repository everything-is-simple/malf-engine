# 第六刀：Range 层实施指南

> **目标**：实现 MALF v2.1 Range 层（§1-§8），将 transition 升格为"震荡区间"一等公民。
>
> **权威规格**：`I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\MALF_02_Range_v2_1-deepseek-20260726.md`
>
> **创建日期**：2026-07-26  
> **负责人**：待分配  
> **状态**：准备中（Day -3）

---

## 1. Range 层职责概览

Range 层将 Core 的 transition（中间未决态）升格为"一等公民"结构对象。Range 有：

- **自己的边界**：可从 init 值演化（使用已确认 pivot）
- **自己的生命周期**：从 break 开始，到 resolution 结束
- **自己的户口**：在 Lifespan 层有自己的排名池
- **自己的分类**：continuation / reversal

**重要**：Range 层不修改 Core 状态机。Core 使用 `boundary_init` 值（冻结），Range 层在 `boundary_init` 基础上允许演化为 `boundary_now`。

---

## 2. v2.1 关键设计点（必读）

### 2.1 两层边界模型（§3，致命区别）

**这是 Range 层最容易出错的地方。** Core 层和 Range 层各自维护一套 boundary：

| 边界 | 持有者 | 可否演化 | 用途 | 演化规则 |
|------|--------|---------|------|---------|
| `boundary_init` | Core + Range | ❌ 不可变 | Core 状态机做 new wave 确认判定（T6） | 从 transition 冻结，永不改变 |
| `boundary_now` | Range | ✅ 可演化 | Range 统计（resolution_distance_pct）、Lifespan 统计 | 基于 init 演化，仅使用已确认 pivot |

#### 边界使用场景对照表（实现者必须遵循）

| 使用场景 | 使用的边界 | 理由 | 代码位置 |
|---------|-----------|------|---------|
| Core new wave 判定（T6 双条件） | `boundary_init` | 状态机稳定性。判定边界在 break 时冻结 | `core_engine.py::_check_new_wave_confirmation()` |
| Range resolution_distance_pct 计算 | `boundary_now` | 反映真实震荡范围。演化后的边界更准确 | `range.py::_calculate_resolution_distance()` |
| Range boundary 演化（R3） | `boundary_now` | 演化发生在 now 值上 | `range.py::_evolve_boundary()` |
| Lifespan 统计 | `boundary_now` | 统计真实特征，使用演化后的值 | `lifespan.py`（第七刀） |
| 快照输出（transition_boundary_*） | `boundary_init` | 快照报告 Core 判定使用的边界，保持可审计性 | `CoreStateSnapshot` |
| 快照输出（range_boundary_now_*） | `boundary_now` | 单独字段报告 Range 的当前边界 | `RangeSnapshot` |

**实现策略**：
- `CoreStateSnapshot` 只记录 `boundary_init`（已在第五刀实现）✅
- `RangeSnapshot` 记录 `boundary_init` + `boundary_now`（第六刀实现）
- Core 引擎的 `_check_new_wave_confirmation()` 使用 `init`（已在第四刀实现）✅
- Range 引擎的 `_calculate_resolution_distance()` 使用 `now`（第六刀实现）

#### Boundary 演化规则（R3）

Transition 内每确认一个新 pivot，检查是否扩展 boundary：

- **上边界扩展**：新 pivot 的 `extreme_price > boundary_high_now`（严格大于）→ 更新 `boundary_high_now`
- **下边界扩展**：新 pivot 的 `extreme_price < boundary_low_now`（严格小于）→ 更新 `boundary_low_now`
- 每次更新 `evolution_count += 1`

**关键约束**：
- ✅ 仅使用已确认 pivot（`confirm_bar_dt` 非空）
- ✅ 未确认的 pivot 不参与 boundary 演化
- ✅ Break bar 的极值不参与演化（C-05 已在 Core 层实现）

---

### 2.2 Continuation 命名陷阱（§6，致命陷阱）

⚠️ **这是 Range 层最容易理解错的概念！**

`continuation_range` 的 "continuation" 延续的是 **break 方向**，不是旧 wave 方向！

#### 四种场景对照表

| 场景 | 旧 wave 方向 | Break 方向 | Resolution 方向 | Range 类型 | 解释 |
|------|------------|-----------|----------------|-----------|------|
| 场景 1 | UP | 向下 break（guard 被向下突破） | 向下突破（resolved_down） | **continuation** | 延续了 break 的下行方向 |
| 场景 2 | UP | 向下 break（guard 被向下突破） | 向上突破（resolved_up） | **reversal** | 反转了 break 的下行方向 |
| 场景 3 | DOWN | 向上 break（guard 被向上突破） | 向上突破（resolved_up） | **continuation** | 延续了 break 的上行方向 |
| 场景 4 | DOWN | 向上 break（guard 被向上突破） | 向下突破（resolved_down） | **reversal** | 反转了 break 的上行方向 |

#### 判定逻辑（v2.1 §6）

```python
# 伪代码
if old_wave_direction == "UP" and resolution_direction == "UP":
    range_type = "continuation_range"  # 旧 UP，最终 UP
elif old_wave_direction == "UP" and resolution_direction == "DOWN":
    range_type = "reversal_range"      # 旧 UP，最终 DOWN
elif old_wave_direction == "DOWN" and resolution_direction == "DOWN":
    range_type = "continuation_range"  # 旧 DOWN，最终 DOWN
elif old_wave_direction == "DOWN" and resolution_direction == "UP":
    range_type = "reversal_range"      # 旧 DOWN，最终 UP
```

**记忆技巧**：
- 旧 wave 和 new wave 方向**相同** → continuation（延续趋势）
- 旧 wave 和 new wave 方向**相反** → reversal（反转趋势）

**测试覆盖要求**：
- [ ] 场景 1：UP → 下 break → 下突破 = continuation（1 个 golden fixture）
- [ ] 场景 2：UP → 下 break → 上突破 = reversal（1 个 golden fixture）
- [ ] 场景 3：DOWN → 上 break → 上突破 = continuation（1 个 golden fixture）
- [ ] 场景 4：DOWN → 上 break → 下突破 = reversal（1 个 golden fixture）

---

### 2.3 Resolution 判定（§4-§5）

当 Core 层的 T6 双条件满足（new wave 确认）时，Range 结束：

#### 三种 Resolution 结果

1. **resolved_up**：new wave 方向向上
2. **resolved_down**：new wave 方向向下
3. **unresolved**：当前仍在 transition（alive range）

#### Resolution 时记录的信息

```python
# 当 new wave 确认时
range.resolution_bar_dt = confirmation_pivot.confirm_bar_dt
range.resolution_type = "up" if new_wave_direction == "UP" else "down"
range.resolution_price = confirmation_pivot.extreme_price
range.span_bars = resolution_bar_dt 到 break_bar_dt 的 bar 数
```

#### Resolution Distance 公式（v2.1 §5）

**注意**：这个公式在 v2.1 中已明确，与 v2.0 不同！

```python
# v2.1 明确公式
resolution_distance_pct = (
    abs(confirmation_pivot.extreme_price - range.birth_break_price)
    / abs(boundary_high_init - boundary_low_init)
)
```

**关键点**：
- ✅ 使用 `confirmation_pivot.extreme_price`（H pivot 用 high，L pivot 用 low）
- ✅ **不是** confirmation bar 的 high/low，是 pivot 的 extreme_price
- ✅ 使用 `boundary_init` 计算分母（不是 `boundary_now`）
- ✅ `birth_break_price` 是触发 guard break 的那根 bar 的 close 价格

**边界情况**：
- 可正可负（当 boundary 演化后突破价格未超出演化后的边界时，可能为负）
- 测试必须覆盖：正 distance、负 distance、接近 0、接近 1

---

## 3. 测试覆盖要求（v2.1 §9）

### 3.1 核心不变量测试（必须覆盖）

| 测试类别 | 最少测试数 | 覆盖内容 | 优先级 |
|---------|----------|---------|--------|
| Range 创建 | 2 | UP break 后 Range 创建、DOWN break 后 Range 创建 | P0 |
| Boundary 初始化 | 2 | boundary_init 与 Core transition boundary 一致 | P0 |
| Boundary 演化 | 3 | 上边界扩展、下边界扩展、不扩展（价格在区间内） | P0 |
| Resolution 判定 | 4 | up resolution、down resolution、continuation、reversal | P0 |
| Resolution distance | 2 | 正 distance、负 distance（boundary 演化后） | P1 |
| 两层边界分离 | 2 | Core 用 init 值、Range 用 now 值 | P0 |

### 3.2 边界情况测试（必须覆盖）

| 测试类别 | 最少测试数 | 场景描述 | 优先级 |
|---------|----------|---------|--------|
| 无演化 | 1 | Transition 内无新 pivot | P1 |
| 单 pivot 演化 | 1 | Transition 内仅 1 个 pivot 触发演化 | P1 |
| 多次演化 | 1 | Boundary_now 演化 3+ 次 | P1 |
| 演化后 resolution | 1 | Boundary 演化后才满足 resolution 条件 | P1 |
| Unresolved range | 1 | Transition 持续 50+ bar，未 resolution | P2 |

### 3.3 不变量列表（R1-R5）

| 编号 | 不变量 | 测试方法 |
|------|--------|---------|
| R1 | Range 的 boundary_init 值来自 Core 的 transition boundary，不可变 | 断言 boundary_init 在 Range 生命周期内不变 |
| R2 | Range 的 boundary_now 值基于 boundary_init 演化，仅使用已确认 pivot | 断言每次演化时 pivot.confirm_bar_dt 非空 |
| R3 | Range 演化不修改 Core 状态机使用的 boundary 值 | 断言 Core 的 transition_boundary_* 不受 Range 演化影响 |
| R4 | Range 在 resolution 时冻结，不可再演化 | 断言 resolution 后 boundary_now 不再变化 |
| R5 | continuation_range 和 reversal_range 分池统计（Lifespan 层） | 第七刀验证 |

---

## 4. Fixture 设计方案

基于 v2.1 §9 测试覆盖要求和 BUILD-CONTRACT.md 铁律，设计 6 个 golden fixture：

### 4.1 Fixture 1: range_simple_continuation_up.json

**目标**：验证场景 1（UP → 下 break → 下突破 = continuation）

**序列设计**：
- 窗口填充：3 根 bars（满足 k=2）
- 初始化：H0→L1→H2>H0 进入 UP_ALIVE
- Guard break：bar N 的 close < guard（LH break）
- Transition：形成 L0 candidate
- Resolution：H1 确认且 H1.low > boundary_high_init → resolved_down
- Range 类型：continuation（旧 UP，最终 DOWN）

**关键验证点**：
- [ ] boundary_init = Core 的 transition boundary
- [ ] boundary_now 初始等于 boundary_init
- [ ] L0 确认后 boundary_now 可能扩展
- [ ] resolution_type = "down"
- [ ] range_type = "continuation_range"

### 4.2 Fixture 2: range_simple_reversal_up.json

**目标**：验证场景 2（UP → 下 break → 上突破 = reversal）

**序列设计**：
- 窗口填充：3 根 bars
- 初始化：H0→L1→H2>H0 进入 UP_ALIVE
- Guard break：bar N 的 close < guard（LH break）
- Transition：形成 L0 candidate
- Resolution：H1 确认且 H1.high > boundary_high_init → resolved_up
- Range 类型：reversal（旧 UP，最终 UP）

**关键验证点**：
- [ ] resolution_type = "up"
- [ ] range_type = "reversal_range"
- [ ] 命名陷阱：reversal 表示"反转了 break 的下行方向"

### 4.3 Fixture 3: range_boundary_evolution.json

**目标**：验证 boundary_now 演化（3 次演化）

**序列设计**：
- UP_ALIVE → LH break → transition
- L0 确认 → boundary_low_now 扩展（evolution_count = 1）
- L1 确认且 L1 < L0 → boundary_low_now 再次扩展（evolution_count = 2）
- H0 确认 → boundary_high_now 扩展（evolution_count = 3）
- H1 确认且突破 → resolved_up

**关键验证点**：
- [ ] evolution_count = 3
- [ ] boundary_init 不变
- [ ] boundary_now 每次演化后更新
- [ ] Core 的 transition_boundary_* 不受影响（R3）

### 4.4 Fixture 4: range_unresolved_alive.json

**目标**：验证 unresolved range（长时间 transition）

**序列设计**：
- UP_ALIVE → LH break → transition
- 多个 L/H pivot 在 boundary 内震荡（50 根 bar）
- 未满足 T6 双条件（无 resolution）
- 最终状态：range_state = "alive"

**关键验证点**：
- [ ] resolution_bar_dt = None
- [ ] resolution_type = None
- [ ] range_type = None
- [ ] span_bars >= 50

### 4.5 Fixture 5: range_resolution_distance_extreme.json

**目标**：验证 resolution_distance_pct 边界情况

**序列设计**：
- 场景 A：resolution_distance_pct ≈ 0.05（小幅突破）
- 场景 B：resolution_distance_pct ≈ 0.95（大幅突破）

**关键验证点**：
- [ ] 使用 confirmation_pivot.extreme_price（不是 bar.high/low）
- [ ] 使用 boundary_init 计算分母
- [ ] 公式正确：abs(extreme_price - break_price) / abs(high_init - low_init)

### 4.6 Fixture 6: range_continuation_down.json

**目标**：验证场景 3（DOWN → 上 break → 上突破 = continuation）

**序列设计**：
- 窗口填充：3 根 bars
- 初始化：L0→H1→L2<L0 进入 DOWN_ALIVE
- Guard break：bar N 的 close > guard（HL break）
- Transition：形成 H0 candidate
- Resolution：L1 确认且 L1.high < boundary_low_init → resolved_up
- Range 类型：continuation（旧 DOWN，最终 UP）

**关键验证点**：
- [ ] 对称实现（与 fixture 1 对称）
- [ ] resolution_type = "up"
- [ ] range_type = "continuation_range"

---

## 5. 数据结构设计

### 5.1 RangeSnapshot（待实现）

```python
# src/malf/types.py

@dataclass
class RangeSnapshot:
    """Range 快照（v2.1 §2 Range）
    
    表示一个震荡区间的完整状态。
    """
    range_id: str | None
    break_bar_dt: str  # ISO format datetime
    break_price: float
    old_wave_direction: Literal["UP", "DOWN"]
    
    # 两层边界（关键设计点）
    boundary_high_init: float  # 从 transition 冻结，不可变
    boundary_low_init: float
    boundary_high_now: float   # 基于 init 演化，可变
    boundary_low_now: float
    
    # 演化统计
    evolution_count: int  # boundary_now 演化次数
    pivot_count: int      # Range 内形成的 pivot 数量
    candidate_replacement_count: int  # Candidate 被替换次数
    
    # Resolution 状态
    range_state: Literal["alive", "resolved_up", "resolved_down"]
    resolution_bar_dt: str | None
    resolution_direction: Literal["UP", "DOWN"] | None
    resolution_price: float | None
    resolution_distance_pct: float | None
    span_bars: int
    
    # 分类
    range_type: Literal["continuation_range", "reversal_range"] | None
    
    # Lineage
    range_rule_version: str  # 例如 "v2.1.0"
```

### 5.2 版本常量（待实现）

```python
# src/malf/version.py

"""MALF 版本常量

定义所有 rule_version 字符串，避免硬编码。
"""

MALF_VERSION = "v2.1"
RULE_VERSION = "deepseek-20260726"

# 各层 rule version
CORE_RULE_VERSION = "v2.1.0"
RANGE_RULE_VERSION = "v2.1.0"
LIFESPAN_RULE_VERSION = "v2.1.0"
STRUCTURAL_POSITION_RULE_VERSION = "v2.1.0"
SERVICE_RULE_VERSION = "v2.1.0"
```

---

## 6. 实施步骤（S6-1 至 S6-9）

遵循 BUILD-CONTRACT.md 铁律：先推 fixture，再写实现，TDD RED → GREEN → REFACTOR。

### S6-1：推 6 个 fixture 预期输出（人肉推导 + debug 脚本）

**任务**：人肉推导 6 个 fixture 的每根 bar 的 RangeSnapshot 预期输出

**铁律复核**（BUILD-CONTRACT.md §5）：
- [ ] **铁律 1**：窗口填充 >= k 根 bars（k=2）
- [ ] **铁律 2**：Pivot 确认严格不等式（逐根检查）
- [ ] **铁律 3**：工具辅助推导（创建 `debug_t6.py`）

**工具设计**：`debug_t6.py`
```python
# 伪代码
def verify_range_fixture(bars, expected_range):
    """验证 Range fixture 的 pivot 和 boundary 演化"""
    # 1. 验证 pivot 检测
    pivots = detect_pivots(bars, k=2)
    print("Detected pivots:", pivots)
    
    # 2. 验证 boundary_init 计算
    boundary_init = calculate_transition_boundaries(...)
    print("boundary_init:", boundary_init)
    
    # 3. 验证 boundary_now 演化
    for pivot in pivots:
        if pivot.extreme_price > boundary_high_now:
            print(f"Evolve boundary_high_now: {boundary_high_now} -> {pivot.extreme_price}")
        # ... 同理 boundary_low_now
    
    # 4. 验证 resolution 判定
    if check_new_wave_confirmation(...):
        print("Resolution detected at bar:", ...)
```

**交付物**：
- [ ] `docs/t6_fixture_derivation_notes.md`（6 个 fixture 的推导笔记）
- [ ] `debug_t6.py`（验证脚本）
- [ ] 人肉推导与脚本结果一致

**预计工作量**：4-6 小时（每个 fixture 约 1 小时）

---

### S6-2：预期输出定稿存 JSON

**任务**：将 6 个 fixture 的预期输出写入 JSON 文件

**文件清单**：
- [ ] `tests/fixtures/range_simple_continuation_up.json`
- [ ] `tests/fixtures/range_simple_reversal_up.json`
- [ ] `tests/fixtures/range_boundary_evolution.json`
- [ ] `tests/fixtures/range_unresolved_alive.json`
- [ ] `tests/fixtures/range_resolution_distance_extreme.json`
- [ ] `tests/fixtures/range_continuation_down.json`

**JSON 结构示例**：
```json
{
  "description": "Range simple continuation (UP → down break → down resolution)",
  "bars": [...],
  "expected_snapshots": [
    {
      "bar_index": 0,
      "bar_dt": "2023-01-01T09:30:00",
      "range_snapshot": null  // 初始化前无 Range
    },
    {
      "bar_index": 10,
      "bar_dt": "2023-01-15T09:30:00",
      "range_snapshot": {
        "range_id": "R001",
        "break_bar_dt": "2023-01-10T09:30:00",
        "break_price": 98.5,
        "old_wave_direction": "UP",
        "boundary_high_init": 105.0,
        "boundary_low_init": 95.0,
        "boundary_high_now": 105.0,
        "boundary_low_now": 95.0,
        "evolution_count": 0,
        "range_state": "alive",
        "resolution_bar_dt": null,
        "resolution_type": null,
        "range_type": null,
        "span_bars": 5
      }
    }
  ]
}
```

**验证清单**：
- [ ] JSON 格式验证通过（`python -m json.tool < fixture.json`）
- [ ] 所有 bar_dt 时间戳连续（无跳跃）
- [ ] Pivot 时间戳对齐（extreme_bar_dt < confirm_bar_dt）
- [ ] Boundary 演化单调（演化后的值更极端）

**预计工作量**：2 小时

---

### S6-3：写 Range 数据结构（types.py）

**任务**：补充 `RangeSnapshot` 和版本常量

**文件修改**：
- [ ] `src/malf/types.py`：添加 `RangeSnapshot` dataclass
- [ ] `src/malf/version.py`：创建版本常量文件

**测试覆盖**：
- [ ] `tests/test_types.py::test_range_snapshot_creation`（验证字段完整性）
- [ ] `tests/test_version.py::test_version_constants`（验证版本号格式）

**预计工作量**：1 小时

---

### S6-4：写 boundary 演化逻辑（range.py::_evolve_boundary()）

**任务**：实现 Range 引擎的 boundary 演化

**新建文件**：`src/malf/range.py`

**核心方法**：
```python
class MALFRangeEngine:
    """Range 层引擎（v2.1 §2 Range）
    
    职责：
    - 跟踪 transition 内的 pivot
    - 演化 boundary_now（基于已确认 pivot）
    - 判定 resolution（基于 Core 的 new wave 确认）
    - 分类 range_type（continuation / reversal）
    """
    
    def _evolve_boundary(self, pivot: Pivot) -> None:
        """演化 boundary_now（R3）
        
        Args:
            pivot: 已确认的 pivot（confirm_bar_dt 非空）
        
        Raises:
            AssertionError: pivot 未确认时
        """
        assert pivot.confirm_bar_dt is not None, "Pivot must be confirmed"
        
        if pivot.pivot_type == "H":
            if pivot.extreme_price > self._range.boundary_high_now:
                self._range.boundary_high_now = pivot.extreme_price
                self._range.evolution_count += 1
        elif pivot.pivot_type == "L":
            if pivot.extreme_price < self._range.boundary_low_now:
                self._range.boundary_low_now = pivot.extreme_price
                self._range.evolution_count += 1
```

**单元测试**：
- [ ] `tests/test_range_engine.py::test_evolve_boundary_up`
- [ ] `tests/test_range_engine.py::test_evolve_boundary_down`
- [ ] `tests/test_range_engine.py::test_evolve_boundary_no_change`（价格在区间内）
- [ ] `tests/test_range_engine.py::test_evolve_boundary_unconfirmed_pivot_raises`

**预计工作量**：2 小时

---

### S6-5：写 resolution 判定逻辑（range.py::_check_resolution()）

**任务**：实现 Range 的 resolution 判定和分类

**核心方法**：
```python
def _check_resolution(self, core_snapshot: CoreStateSnapshot) -> None:
    """检查 resolution（基于 Core new wave 确认）
    
    Args:
        core_snapshot: Core 层快照
    
    Notes:
        - Resolution 触发条件：Core 的 system_state 从 transition 转为 up_alive/down_alive
        - Resolution 类型：基于 new wave 方向
        - Range 类型：基于 old_wave 和 new_wave 方向对比
    """
    if core_snapshot.system_state in ["UP_ALIVE", "DOWN_ALIVE"]:
        # New wave 已确认
        new_wave_direction = "UP" if core_snapshot.system_state == "UP_ALIVE" else "DOWN"
        
        self._range.resolution_bar_dt = core_snapshot.bar_dt
        self._range.resolution_direction = new_wave_direction
        self._range.resolution_price = core_snapshot.wave_progress_extreme_price
        
        # 计算 resolution_distance_pct（v2.1 §5 公式）
        self._range.resolution_distance_pct = (
            abs(self._range.resolution_price - self._range.break_price)
            / abs(self._range.boundary_high_init - self._range.boundary_low_init)
        )
        
        # 判定 range_type（v2.1 §6）
        if self._range.old_wave_direction == new_wave_direction:
            self._range.range_type = "continuation_range"
        else:
            self._range.range_type = "reversal_range"
        
        self._range.range_state = f"resolved_{new_wave_direction.lower()}"
```

**单元测试**：
- [ ] `tests/test_range_engine.py::test_resolution_up`
- [ ] `tests/test_range_engine.py::test_resolution_down`
- [ ] `tests/test_range_engine.py::test_resolution_distance_calculation`
- [ ] `tests/test_range_engine.py::test_range_type_continuation`
- [ ] `tests/test_range_engine.py::test_range_type_reversal`

**预计工作量**：2 小时

---

### S6-6：写单元测试（先 RED）

**任务**：创建完整的单元测试，验证 Range 引擎逻辑

**测试文件**：`tests/test_range_engine.py`

**测试清单**（TDD RED → GREEN）：
- [ ] test_range_creation_on_guard_break（2 个：up/down）
- [ ] test_boundary_init_equals_core_transition_boundary（R1）
- [ ] test_boundary_evolution_up_expansion（R2）
- [ ] test_boundary_evolution_down_expansion（R2）
- [ ] test_boundary_evolution_no_change（价格在区间内）
- [ ] test_range_does_not_modify_core_boundary（R3）
- [ ] test_resolution_freezes_range（R4）
- [ ] test_continuation_range_scenario_1（UP → 下 break → 下 resolution）
- [ ] test_continuation_range_scenario_3（DOWN → 上 break → 上 resolution）
- [ ] test_reversal_range_scenario_2（UP → 下 break → 上 resolution）
- [ ] test_reversal_range_scenario_4（DOWN → 上 break → 下 resolution）

**预计工作量**：3 小时

---

### S6-7：端到端测试（逐 bar 喂入，全等比对）

**任务**：使用 6 个 golden fixtures 进行端到端测试

**测试文件**：`tests/test_t6_range_integration.py`

**测试方法**：
```python
def test_range_simple_continuation_up():
    """端到端测试：range_simple_continuation_up.json"""
    fixture = load_fixture("range_simple_continuation_up.json")
    
    core_engine = MALFCoreEngine()
    range_engine = MALFRangeEngine()
    
    for i, bar in enumerate(fixture["bars"]):
        core_snapshot = core_engine.on_bar(bar)
        range_snapshot = range_engine.on_bar(bar, core_snapshot)
        
        expected = fixture["expected_snapshots"][i]["range_snapshot"]
        assert range_snapshot == expected, f"Mismatch at bar {i}"
```

**测试清单**：
- [ ] test_range_simple_continuation_up（fixture 1）
- [ ] test_range_simple_reversal_up（fixture 2）
- [ ] test_range_boundary_evolution（fixture 3）
- [ ] test_range_unresolved_alive（fixture 4）
- [ ] test_range_resolution_distance_extreme（fixture 5）
- [ ] test_range_continuation_down（fixture 6）

**预计工作量**：2 小时

---

### S6-8：真实数据冒烟（记录 range 分布）

**任务**：验证 Range 引擎在真实数据上的稳定性

**测试文件**：`tests/test_real_data_smoke.py`（新增测试）

**测试方法**：
```python
def test_sh600000_range_engine_smoke():
    """真实数据冒烟：sh600000 前 200 根，Range 引擎"""
    bars = load_tdx_data("I:/new_tdx64", "sh600000", count=200)
    
    core_engine = MALFCoreEngine()
    range_engine = MALFRangeEngine()
    
    range_count = 0
    continuation_count = 0
    reversal_count = 0
    evolution_count_total = 0
    
    for bar in bars:
        core_snapshot = core_engine.on_bar(bar)
        range_snapshot = range_engine.on_bar(bar, core_snapshot)
        
        if range_snapshot and range_snapshot.range_state.startswith("resolved"):
            range_count += 1
            if range_snapshot.range_type == "continuation_range":
                continuation_count += 1
            elif range_snapshot.range_type == "reversal_range":
                reversal_count += 1
            evolution_count_total += range_snapshot.evolution_count
    
    # 不断言具体数量，只验证不崩溃
    print(f"Total ranges: {range_count}")
    print(f"Continuation: {continuation_count}, Reversal: {reversal_count}")
    print(f"Avg evolution per range: {evolution_count_total / max(range_count, 1):.2f}")
```

**验证点**：
- [ ] 不崩溃
- [ ] Range 数量 > 0（真实数据必然有 transition）
- [ ] continuation 和 reversal 都有出现（验证分类逻辑）
- [ ] 记录 evolution_count 分布

**预计工作量**：1 小时

---

### S6-9：回补文档

**任务**：更新项目文档，标记第六刀完成

**文档清单**：
- [ ] `docs/BUILD-PLAN.md`：勾选第六刀所有 step
- [ ] `src/malf/range.py`：补充完整 docstring
- [ ] `docs/DAILY-LOG-2026-07-XX.md`：记录调试过程、技术决策、遗留问题
- [ ] `docs/T6-COMPLETION-SUMMARY.md`：总结第六刀成果

**预计工作量**：1 小时

---

## 7. 完成标志

第六刀 done = 以下全部达标：

1. ✅ **S6-7 端到端测试全绿**：6 个 golden fixtures 全部通过
2. ✅ **S6-8 真实数据冒烟无崩溃**：sh600000 前 200 根，Range 引擎稳定运行
3. ✅ **S6-9 文档更新完整**：BUILD-PLAN.md + 模块 docstring + DAILY-LOG
4. ✅ **不变量 R1-R4 有测试覆盖**：每个不变量至少 1 个测试
5. ✅ **Continuation 命名陷阱有测试覆盖**：4 种场景各 1 个测试
6. ✅ **总测试数达标**：预计 47 + 15 = 62 passed（Core 47 + Range 15）

**禁止**：
- ❌ S6-7 未全绿就进入 S6-8
- ❌ 真实数据发现崩溃但未修复就标记完成
- ❌ 跳过 S6-9 文档回补

---

## 8. 技术风险与应对

### 8.1 风险：两层边界混用（高概率）

**风险描述**：实现时误用 `boundary_now` 在 Core 状态机判定中，或误用 `boundary_init` 在 Range 统计中。

**影响**：Core 状态机行为不稳定，或 Range 统计失真。

**应对措施**：
1. **强类型约束**：在 Range 引擎方法签名中明确参数名称
   ```python
   def _calculate_resolution_distance(
       self,
       extreme_price: float,
       break_price: float,
       boundary_high_init: float,  # 明确使用 init
       boundary_low_init: float,
   ) -> float:
   ```
2. **代码审查清单**：实现后逐方法检查边界使用是否符合对照表
3. **单元测试覆盖**：test_range_does_not_modify_core_boundary（R3）

### 8.2 风险：Continuation 命名理解错误（中概率）

**风险描述**：将 "continuation" 理解为"延续旧 wave 方向"，导致分类逻辑错误。

**影响**：range_type 分类错误，Lifespan 层分池错误。

**应对措施**：
1. **专门测试用例**：4 种场景各 1 个 golden fixture，覆盖所有排列组合
2. **注释警告**：在 `_classify_range_type()` 方法开头增加警告注释
   ```python
   def _classify_range_type(self, old_wave_direction, new_wave_direction):
       """判定 range_type（v2.1 §6）
       
       ⚠️ 命名陷阱：continuation 延续的是 break 方向，不是旧 wave 方向！
       - 旧 UP + 新 UP = continuation（延续了向上趋势）
       - 旧 UP + 新 DOWN = reversal（反转了向上趋势）
       """
   ```
3. **人工复核**：S6-1 推导 fixture 时，逐个场景对照 §6 命名陷阱警告框

### 8.3 风险：Resolution distance 公式错误（中概率）

**风险描述**：误用 `boundary_now` 或误用 bar.high/low 而非 pivot.extreme_price。

**影响**：resolution_distance_pct 计算错误，Lifespan 层统计失真。

**应对措施**：
1. **公式注释**：在 `_calculate_resolution_distance()` 方法中引用 v2.1 §5 原文
2. **边界测试**：test_resolution_distance_extreme（极小值、极大值、负值）
3. **Debug 打印**：实现时增加临时 debug 日志，验证公式每一项的值

### 8.4 风险：Fixture 窗口填充不足（低概率，第三刀已踩坑）

**风险描述**：忘记在序列开头添加 >= k 根窗口填充 bars。

**影响**：首个 pivot 检测失败，fixture 预期输出错误。

**应对措施**：
1. **铁律 1 检查**：S6-1 推导时强制检查窗口填充
2. **Debug 脚本验证**：debug_t6.py 输出首个 pivot 的索引，验证 >= k
3. **模板复用**：参考第三刀修复后的 T3 fixtures（d00-d02 窗口填充）

---

## 9. 参考资料

### 9.1 规格文档

- **权威规格**：`I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\MALF_02_Range_v2_1-deepseek-20260726.md`
- **本地引用**：`docs/MALF_V2_1_AUTHORITY_REFERENCE.md`
- **补丁文档**：`IMPLEMENTATION-CONTRACT-PATCH.md`（v2.1 已回写，保留作历史记录）

### 9.2 项目文档

- **建造合同**：`docs/BUILD-CONTRACT.md`（铁律 1-7）
- **建造计划**：`docs/BUILD-PLAN.md`（第一到五刀经验）
- **修订清单**：`docs/REVISION-CHECKLIST.md`（P0-P3 分级）

### 9.3 前序成果

- **第一刀**：uninitialized → up_alive（16 passed）
- **第二刀**：uninitialized → down_alive（对称实现）
- **第三刀**：Guard break（LH/HL break）
- **第四刀**：Transition candidate 演化（flip-flop）
- **第五刀**：Guard 更新 + bar_count + Replay（47 passed, 1 skipped）

---

## 10. 工作量估算

| Step | 任务 | 预计工作量 | 关键路径 |
|------|------|-----------|---------|
| S6-1 | 推 6 个 fixture 预期输出 | 4-6 小时 | ✅ 是 |
| S6-2 | 预期输出定稿存 JSON | 2 小时 | ✅ 是 |
| S6-3 | 写 Range 数据结构 | 1 小时 | ❌ 否 |
| S6-4 | 写 boundary 演化逻辑 | 2 小时 | ✅ 是 |
| S6-5 | 写 resolution 判定逻辑 | 2 小时 | ✅ 是 |
| S6-6 | 写单元测试 | 3 小时 | ✅ 是 |
| S6-7 | 端到端测试 | 2 小时 | ✅ 是 |
| S6-8 | 真实数据冒烟 | 1 小时 | ❌ 否 |
| S6-9 | 回补文档 | 1 小时 | ❌ 否 |

**总工作量**：18-20 小时（约 3 个工作日）

**关键路径**：S6-1 → S6-2 → S6-4 → S6-5 → S6-6 → S6-7（约 15-17 小时）

---

## 11. 开工前检查清单（Day 0）

在开始 S6-1 之前，确认以下事项：

### 11.1 环境就绪

- [ ] Python 环境正常：`/d/miniconda/py310/python.exe --version`
- [ ] pytest 可运行：`/d/miniconda/py310/python.exe -m pytest --version`
- [ ] 第五刀测试全绿：`/d/miniconda/py310/python.exe -m pytest -v`（47 passed, 1 skipped）

### 11.2 文档就绪

- [ ] 已读 `MALF_02_Range_v2_1-deepseek-20260726.md` 完整规格
- [ ] 已读 `docs/MALF_V2_1_AUTHORITY_REFERENCE.md` Range 章节
- [ ] 已读 `docs/BUILD-CONTRACT.md` 铁律 1-7
- [ ] 已读本文档（T6-RANGE-IMPLEMENTATION-GUIDE.md）

### 11.3 前置任务完成

- [ ] **P0-1**：类型名重命名（WaveStructuralSnapshot → WaveStructuralSnapshot）
- [ ] **P0-2**：v2.1 文档引用说明（core_engine.py docstring）
- [ ] **P2-3**：BUILD-PLAN.md 增加 v2.1 章节映射

### 11.4 工具准备

- [ ] Excel 或 Python 可视化工具（画 bar 序列折线图）
- [ ] JSON 格式验证工具（`python -m json.tool`）
- [ ] `debug_t6.py` 模板准备（参考 `debug_t3.py` / `debug_t4.py`）

---

## 12. 成功标志（第六刀完成后）

当以下全部达成时，第六刀可以标记为完成：

1. ✅ **测试全绿**：62+ passed, 1 skipped（Core 47 + Range 15+）
2. ✅ **不变量覆盖**：R1-R4 各有专门测试
3. ✅ **命名陷阱覆盖**：4 种 continuation/reversal 场景全部测试通过
4. ✅ **真实数据稳定**：sh600000 前 200 根无崩溃，Range 数量 > 0
5. ✅ **文档完整**：BUILD-PLAN.md + DAILY-LOG + T6-COMPLETION-SUMMARY.md
6. ✅ **代码质量**：通过代码审查，边界使用符合对照表（§2.1）

达标后，才排第七刀（Lifespan 层：双轨系统 + percentile_rank）。

---

## 附录 A：v2.1 Range 章节快速索引

| 章节 | 内容 | 关键点 |
|------|------|--------|
| §1 | 层职责 | Range 是一等公民，有自己的边界、生命周期、分类 |
| §2 | Range 对象 | 字段定义，两层边界（init/now） |
| §3 | Boundary 演化 | 两层边界模型、使用场景对照表、演化规则（R3） |
| §4 | Resolution | 3 种结果（resolved_up/down/unresolved） |
| §5 | Resolution Distance | 公式明确（使用 extreme_price + boundary_init） |
| §6 | Range Type 分类 | Continuation 命名陷阱（延续 break 方向） |
| §7 | 不变量 | R1-R5（init 不变、now 演化、分池统计） |
| §8 | 编号对照 | R1-R8 与 v2.0 一致 |
| §9 | 测试覆盖 | 核心不变量 + 边界情况，最少测试数要求 |

---

## 附录 B：第六刀与前五刀的接口

### B.1 Core 层输出 → Range 层输入

Range 层依赖 Core 层的以下输出：

| Core 输出 | Range 使用 | 用途 |
|----------|-----------|------|
| `system_state` | transition 检测 | 判断是否在 Range 生命周期内 |
| `transition_boundary_high/low` | boundary_init 初始化 | Range 的 init 边界来自 Core |
| `transition_entry_bar_dt` | Range 起点 | break_bar_dt = transition_entry_bar_dt |
| `guard_price` | break_price 计算 | break_price = break bar 的 close |
| Pivot 序列 | boundary_now 演化 | 使用已确认 pivot 扩展边界 |
| New wave 确认 | Resolution 触发 | system_state 转为 alive 时 Range 结束 |

### B.2 Range 层输出 → Lifespan 层输入（第七刀）

Range 层为 Lifespan 层提供：

| Range 输出 | Lifespan 使用 | 用途 |
|-----------|--------------|------|
| `range_type` | 分池 | continuation/reversal 三池分开 |
| `span_bars` | 排名 | Range 持续时间排名 |
| `evolution_count` | 排名 | Boundary 演化次数排名 |
| `resolution_distance_pct` | 排名 | 突破幅度排名 |

---

**本文档版本**：v1.0  
**创建日期**：2026-07-26  
**下次更新**：第六刀开工日（Day 0）或 S6-1 完成后


