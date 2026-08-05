# malf-engine API 参考

**版本**: MALF v2.1  
**更新日期**: 2026-07-26

---

## 📦 主要类

### `MALFCoreEngine`

核心引擎，单遍处理 bar 序列，输出结构快照。

#### 构造函数

```python
MALFCoreEngine(k: int = 2)
```

**参数**:
- `k` (int): Pivot 检测窗口大小，默认 2（左右各 2 个 bar 确认极值）

**示例**:
```python
from malf.core_engine import MALFCoreEngine

engine = MALFCoreEngine(k=2)
```

#### 方法

##### `on_bar(bar: PriceBar) -> CoreStateSnapshot`

处理一个 bar，返回当前状态快照。

**参数**:
- `bar` (PriceBar): 价格 bar

**返回**:
- `CoreStateSnapshot`: 当前系统状态快照

**示例**:
```python
snapshot = engine.on_bar(bar)
print(f"State: {snapshot.system_state.value}")
```

**注意**:
- 确定性：相同输入序列产生相同输出
- 单遍：每个 bar 只处理一次，不回溯
- 无副作用：不修改输入 bar

---

## 📊 数据类

### `PriceBar`

价格 bar 数据。

```python
@dataclass
class PriceBar:
    symbol: str          # 标的代码，e.g., "sh600000"
    timeframe: str       # 时间周期，e.g., "1d", "1h"
    bar_dt: str          # Bar 时间标识，e.g., "20260726", "202607261430"
    open: int            # 开盘价（整数，单位：分）
    high: int            # 最高价（整数，单位：分）
    low: int             # 最低价（整数，单位：分）
    close: int           # 收盘价（整数，单位：分）
```

**示例**:
```python
from malf.types import PriceBar

bar = PriceBar(
    symbol="sh600000",
    timeframe="1d",
    bar_dt="20260726",
    open=10000,    # 100.00 元
    high=10500,    # 105.00 元
    low=9800,      # 98.00 元
    close=10300    # 103.00 元
)
```

---

### `CoreStateSnapshot`

系统状态快照，包含 Core 层和 Range 层字段。

#### Core 层字段

```python
@dataclass
class CoreStateSnapshot:
    # 基础信息
    symbol: str                              # 标的代码
    timeframe: str                           # 时间周期
    bar_dt: str                              # 当前 bar 时间
    
    # 系统状态
    system_state: SystemState                # UNINITIALIZED | UP_ALIVE | DOWN_ALIVE | TRANSITION
    direction: Optional[Direction]           # UP | DOWN | None
    wave_core_state: WaveCoreState          # UNINITIALIZED | ALIVE | TERMINATED
    
    # Guard 信息
    current_effective_guard_price: Optional[int]           # 当前有效 guard 价格
    current_effective_guard_extreme_bar_dt: Optional[str]  # Guard extreme bar 时间
    current_effective_guard_confirm_bar_dt: Optional[str]  # Guard 确认 bar 时间
    
    # Progress 信息
    progress_extreme_price: Optional[int]    # 进展极值价格
    progress_extreme_bar_dt: Optional[str]   # 进展极值 bar 时间
    
    # Bar count
    bar_count: Optional[int]                 # 波段内 bar 计数
    
    # Transition 信息
    break_bar_dt: Optional[str]              # Guard break bar 时间
    transition_boundary_high: Optional[int]  # Transition 上界
    transition_boundary_low: Optional[int]   # Transition 下界
    
    # Candidate 信息
    active_candidate_guard_price: Optional[int]           # 候选 guard 价格
    active_candidate_guard_extreme_bar_dt: Optional[str]  # 候选 guard extreme bar
    active_candidate_guard_confirm_bar_dt: Optional[str]  # 候选 guard 确认 bar
    active_candidate_direction: Optional[Direction]       # 候选方向
    candidate_replacement_count: int                      # 候选替换次数
```

#### Range 层字段（v2.1 新增）

```python
    # Range 诞生与边界
    range_birth_bar_dt: Optional[str]        # Range 诞生时刻
    range_boundary_init_high: Optional[int]  # 冻结上界（判定用）
    range_boundary_init_low: Optional[int]   # 冻结下界（判定用）
    range_boundary_now_high: Optional[int]   # 演化上界（统计用）
    range_boundary_now_low: Optional[int]    # 演化下界（统计用）
    
    # Range 演化
    range_evolution_count: int               # 演化次数（默认 0）
    
    # Range Resolution
    range_resolution_bar_dt: Optional[str]   # Resolution 确认时刻
    range_resolution_type: Optional[str]     # "continuation" | "reversal"
    range_resolution_distance: Optional[int] # 突破距离（有符号）
```

#### 元数据字段

```python
    # 版本信息
    core_rule_version: str                   # Core 规则版本（权威 Service §5："v2.1"）
    pivot_detection_rule_version: str        # Pivot 检测规则版本（权威 O1："fractal_k2_v1.0"）
    price_policy: str                        # 价格域（权威："source_integer_fixed_point"）
    runtime_fingerprint: str                 # 运行时指纹
    schema_version: str                      # 快照 schema 版本
    note: str                                # 备注
```

---

## 🔤 枚举类型

### `SystemState`

系统状态枚举。

```python
class SystemState(Enum):
    UNINITIALIZED = "uninitialized"  # 未初始化（< 3 pivots）
    UP_ALIVE = "up_alive"            # UP 波段存活
    DOWN_ALIVE = "down_alive"        # DOWN 波段存活
    TRANSITION = "transition"        # 震荡期（Range alive）
```

### `Direction`

波段方向枚举。

```python
class Direction(Enum):
    UP = "up"      # 向上
    DOWN = "down"  # 向下
```

### `WaveCoreState`

波段核心状态枚举。

```python
class WaveCoreState(Enum):
    UNINITIALIZED = "uninitialized"  # 未初始化
    ALIVE = "alive"                  # 存活
    TERMINATED = "terminated"        # 终止
```

### `PivotType`

Pivot 类型枚举。

```python
class PivotType(Enum):
    H = "H"  # 高点
    L = "L"  # 低点
```

---

## 📋 字段使用指南

### 何时字段有效？

| 字段类别 | 有效条件 | 示例 |
|---------|---------|------|
| 基础信息 | 始终有效 | `symbol`, `bar_dt` |
| Guard | `system_state` 为 `*_ALIVE` | `current_effective_guard_price` |
| Progress | `system_state` 为 `*_ALIVE` | `progress_extreme_price` |
| Transition | `system_state` 为 `TRANSITION` | `transition_boundary_high` |
| Candidate | `system_state` 为 `TRANSITION` | `active_candidate_guard_price` |
| **Range (birth/boundary)** | **`system_state` 为 `TRANSITION`** | **`range_birth_bar_dt`** |
| **Range (resolution)** | **Resolution 发生后** | **`range_resolution_bar_dt`** |

### 字段访问模式

#### 检查系统状态
```python
if snapshot.system_state == SystemState.UP_ALIVE:
    print(f"UP wave, guard={snapshot.current_effective_guard_price}")
elif snapshot.system_state == SystemState.TRANSITION:
    print(f"TRANSITION, Range born at {snapshot.range_birth_bar_dt}")
```

#### 安全访问可选字段
```python
# 不推荐
guard = snapshot.current_effective_guard_price  # 可能为 None

# 推荐
if snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
    guard = snapshot.current_effective_guard_price
    assert guard is not None  # 状态已保证非 None
```

#### Range 字段访问
```python
# 检查 Range 是否存在
if snapshot.system_state == SystemState.TRANSITION:
    # Range 正在进行
    print(f"Range birth: {snapshot.range_birth_bar_dt}")
    print(f"Evolution count: {snapshot.range_evolution_count}")
    
    # boundary_init 和 boundary_now 必定非 None
    assert snapshot.range_boundary_init_high is not None
    assert snapshot.range_boundary_now_low is not None

# 检查 Range 是否已 resolve
if snapshot.range_resolution_bar_dt is not None:
    # Range 已 resolve
    print(f"Resolution type: {snapshot.range_resolution_type}")
    print(f"Resolution distance: {snapshot.range_resolution_distance}")
```

---

## 🔍 完整示例

### 基础使用

```python
from malf.core_engine import MALFCoreEngine
from malf.types import PriceBar, SystemState

# 初始化引擎
engine = MALFCoreEngine(k=2)

# 准备数据
bars = [
    PriceBar("TEST", "1d", "d01", 10000, 10500, 9500, 10300),
    PriceBar("TEST", "1d", "d02", 10300, 11000, 10200, 10800),
    # ... more bars
]

# 逐 bar 处理
for bar in bars:
    snapshot = engine.on_bar(bar)
    
    # 根据状态处理
    if snapshot.system_state == SystemState.UNINITIALIZED:
        print(f"{bar.bar_dt}: Waiting for initialization...")
    
    elif snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
        print(f"{bar.bar_dt}: {snapshot.direction.value.upper()} wave alive")
        print(f"  Guard: {snapshot.current_effective_guard_price}")
        print(f"  Progress: {snapshot.progress_extreme_price}")
        print(f"  Bar count: {snapshot.bar_count}")
    
    elif snapshot.system_state == SystemState.TRANSITION:
        print(f"{bar.bar_dt}: TRANSITION (Range alive)")
        print(f"  Range birth: {snapshot.range_birth_bar_dt}")
        print(f"  Evolution count: {snapshot.range_evolution_count}")
        print(f"  Boundary init: [{snapshot.range_boundary_init_high}, "
              f"{snapshot.range_boundary_init_low}]")
        
        # 检查是否 resolve
        if snapshot.range_resolution_bar_dt == snapshot.bar_dt:
            print(f"  >>> RESOLVED: {snapshot.range_resolution_type}")
```

### 统计分析

```python
# 收集统计数据
stats = {
    'total_bars': 0,
    'up_bars': 0,
    'down_bars': 0,
    'transition_bars': 0,
    'range_count': 0,
    'continuation_count': 0,
    'reversal_count': 0,
}

for bar in bars:
    snapshot = engine.on_bar(bar)
    stats['total_bars'] += 1
    
    if snapshot.system_state == SystemState.UP_ALIVE:
        stats['up_bars'] += 1
    elif snapshot.system_state == SystemState.DOWN_ALIVE:
        stats['down_bars'] += 1
    elif snapshot.system_state == SystemState.TRANSITION:
        stats['transition_bars'] += 1
    
    if snapshot.range_birth_bar_dt == snapshot.bar_dt:
        stats['range_count'] += 1
    
    if snapshot.range_resolution_bar_dt == snapshot.bar_dt:
        if snapshot.range_resolution_type == 'continuation':
            stats['continuation_count'] += 1
        elif snapshot.range_resolution_type == 'reversal':
            stats['reversal_count'] += 1

# 打印报告
print(f"Total bars: {stats['total_bars']}")
print(f"UP bars: {stats['up_bars']} ({stats['up_bars']/stats['total_bars']*100:.1f}%)")
print(f"DOWN bars: {stats['down_bars']} ({stats['down_bars']/stats['total_bars']*100:.1f}%)")
print(f"TRANSITION bars: {stats['transition_bars']} ({stats['transition_bars']/stats['total_bars']*100:.1f}%)")
print(f"Ranges: {stats['range_count']}")
print(f"  Continuation: {stats['continuation_count']}")
print(f"  Reversal: {stats['reversal_count']}")
```

---

## 🚨 常见错误

### 1. 未检查状态就访问字段

```python
# ❌ 错误
guard = snapshot.current_effective_guard_price  # 可能为 None
print(f"Guard: {guard}")

# ✅ 正确
if snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
    guard = snapshot.current_effective_guard_price
    print(f"Guard: {guard}")
```

### 2. 混淆 boundary_init 和 boundary_now

```python
# ❌ 错误：用 boundary_now 判定 resolution
if pivot_price < snapshot.range_boundary_now_low:
    print("Resolved!")  # 错误！应该用 boundary_init

# ✅ 正确：引擎内部已判定，直接检查字段
if snapshot.range_resolution_bar_dt == snapshot.bar_dt:
    print(f"Resolved: {snapshot.range_resolution_type}")
```

### 3. 假设 Range 字段始终存在

```python
# ❌ 错误
print(f"Range birth: {snapshot.range_birth_bar_dt}")  # 非 TRANSITION 时为 None

# ✅ 正确
if snapshot.system_state == SystemState.TRANSITION:
    print(f"Range birth: {snapshot.range_birth_bar_dt}")
```

---

## 📚 相关文档

- **使用指南**: `docs/RANGE-LAYER-GUIDE.md`
- **设计文档**: `docs/T6-DAY-0-COMPLETION.md`
- **真实数据验证**: `docs/RANGE-REAL-DATA-VALIDATION-COMPLETE.md`

---

**最后更新**: 2026-07-26  
**API 版本**: v2.1  
**状态**: 稳定 ✅
