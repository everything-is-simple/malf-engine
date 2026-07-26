# malf-engine 需要修订的地方清单

> **生成日期：** 2026-07-26  
> **基于版本：** MALF v2.1 Definitive  
> **当前实施状态：** Core 层已完成（47 passed），Range 层待开始

---

## 修订分类

修订按优先级分为 4 级：
- **P0：** 阻塞性，必须在指定刀数前完成
- **P1：** 高优先级，影响实现质量
- **P2：** 中优先级，改善可维护性
- **P3：** 低优先级，长期完善

---

## P0：阻塞性修订（必须完成）

### P0-1：类型名重命名（第六刀前）

**问题：**  
当前代码使用 v2.0 命名 `WaveProbabilitySnapshot`，与 v2.1 权威定义不一致。

**影响范围：**
1. `src/malf/types.py` - 类型定义
   ```python
   # 当前（v2.0）
   @dataclass
   class WaveProbabilitySnapshot:
       ...
   
   # 需要改为（v2.1）
   @dataclass
   class WaveStructuralSnapshot:
       ...
   ```

2. `src/malf/core_engine.py` - 类型引用
   ```python
   # 需要全局替换
   WaveProbabilitySnapshot → WaveStructuralSnapshot
   ```

3. `tests/` 所有测试文件 - 类型引用
   ```bash
   # 需要批量替换（约 47 个测试文件）
   grep -r "WaveProbabilitySnapshot" tests/ --files-with-matches
   ```

4. `tests/fixtures/*.json` - 可能包含类型名字符串

**执行计划：**
1. 第六刀开工前 1 天执行
2. 顺序：types.py → core_engine.py → tests/ → 跑全部测试确认绿
3. 预计工作量：30 分钟
4. 风险：低（纯重命名，语义不变）

**验收标准：**
```bash
# 1. 类型名全部替换
grep -r "WaveProbabilitySnapshot" src/ tests/ | wc -l  # 应该为 0

# 2. 新类型名可找到
grep -r "WaveStructuralSnapshot" src/ tests/ | wc -l  # 应该 > 0

# 3. 测试通过
pytest  # 应该仍然 47 passed, 1 skipped
```

**负责人：** 待分配  
**截止时间：** 第六刀开工前

---

### P0-2：v2.1 文档引用说明（立即执行）

**问题：**  
Core 层代码基于 v2.0 实现，但 v2.1 已发布，需要在代码注释中明确说明兼容性。

**修订：**  
在关键模块的 docstring 中增加版本说明：

```python
# src/malf/core_engine.py

"""
MALF Core Engine - 结构状态机

本模块实现 MALF v2.1 Core 层（§1-§10）。

版本说明：
- 设计基于：MALF v2.0 Definitive (claude-20260616)
- 权威定义：MALF v2.1 Definitive (deepseek-20260726)
- 语义兼容性：v2.1 与 v2.0 完全等价（v2.1 是清晰表达版本）
- 命名差异：WaveProbabilitySnapshot（v2.0）→ WaveStructuralSnapshot（v2.1）

v2.1 权威文档：
I:\\asteria-riskbench-Definitive-validated\\MALF_Definitive_v2_1-deepseek-20260726\\

编号对照：
- D1-D18：定义（Definitions）
- T1-T10：定理（Theorems）
- O1-O8：操作边界（Operational Boundaries）

本模块实现：
- §2：Pivot 检测与确认（fractal k=2）
- §3：初始化逻辑（D18/O6）
- §4-§8：状态机九步顺序（O2）
- §9：快照输出与指纹
"""
```

**影响范围：**
- `src/malf/core_engine.py`
- `src/malf/pivot_detection.py`
- `src/malf/initialization.py`
- `src/malf/types.py`

**执行计划：** 立即执行（不影响功能）  
**预计工作量：** 20 分钟  
**负责人：** 待分配

---

## P1：高优先级修订（影响实现质量）

### P1-1：Range 层实施准备文档（第六刀前）

**需要创建：** `docs/T6-RANGE-IMPLEMENTATION-GUIDE.md`

**内容大纲：**

```markdown
# 第六刀：Range 层实施指南

## 目标
实现 MALF v2.1 Range 层（§1-§8），将 transition 升格为"震荡区间"一等公民。

## v2.1 关键设计点

### 1. 两层边界模型（§3）

Core 层和 Range 层各自维护一套 boundary：

| 边界 | 用途 | 演化规则 | 使用场景 |
|------|------|---------|---------|
| boundary_init | Core 状态机 | 从 transition 冻结，不变 | new wave 判定 |
| boundary_now | Range 统计 | 基于 init 演化，用已确认 pivot | resolution_distance_pct、Lifespan 统计 |

**实现策略：**
- CoreStateSnapshot 只记录 boundary_init
- RangeSnapshot 记录 boundary_init + boundary_now
- Core 引擎的 _check_new_wave_confirmation() 使用 init
- Range 引擎的 _calculate_resolution_distance() 使用 now

### 2. Continuation 命名陷阱（§6）

⚠️ **致命陷阱**：continuation_range 延续的是 **break 方向**，不是旧 wave 方向！

| 场景 | 旧 wave | Break 方向 | Resolution 方向 | Range 类型 |
|------|---------|-----------|----------------|-----------|
| 场景 1 | UP | 向下 break | 向下突破 | continuation（延续 break 的下行） |
| 场景 2 | UP | 向下 break | 向上突破 | reversal（反转 break 的下行） |
| 场景 3 | DOWN | 向上 break | 向上突破 | continuation（延续 break 的上行） |
| 场景 4 | DOWN | 向上 break | 向下突破 | reversal（反转 break 的上行） |

**测试覆盖要求：**
- 4 种场景各 1 个 golden fixture
- 专门的 test_continuation_naming_trap() 测试

### 3. Resolution 判定（§4-§5）

3 种 resolution 结果：
1. resolved_up：new wave 方向向上
2. resolved_down：new wave 方向向下
3. unresolved：当前仍在 transition（alive range）

**resolution_distance_pct 公式（v2.1 §5 明确）：**
```python
resolution_distance_pct = (
    abs(confirmation_pivot.extreme_price - range.birth_break_price)
    / abs(boundary_high_init - boundary_low_init)
)
```

### 4. 测试覆盖要求（v2.1 §9）

必须覆盖：
- [ ] 不变量 R1-R5（5 个测试）
- [ ] boundary 演化（3 个边界情况）
- [ ] continuation 命名陷阱（4 个场景）
- [ ] resolution_distance_pct 公式（2 个极端情况）
- [ ] unresolved range 处理（1 个测试）

## Fixture 设计

基于 v2.1 §9 测试覆盖要求，设计 6 个 golden fixture：

1. `range_simple_continuation.json` - 场景 1（UP→下 break→下突破）
2. `range_simple_reversal.json` - 场景 2（UP→下 break→上突破）
3. `range_boundary_evolution.json` - boundary_now 演化 3 次
4. `range_unresolved_alive.json` - transition 持续 50 根 bar
5. `range_resolution_distance_extreme.json` - distance = 0.05 和 0.95
6. `range_double_reversal.json` - 两个连续 reversal range

## 实施步骤

1. [ ] S6-1：推 6 个 fixture 预期输出
2. [ ] S6-2：预期输出定稿存 JSON
3. [ ] S6-3：写 Range 数据结构（types.py）
4. [ ] S6-4：写 boundary 演化逻辑（range.py::_evolve_boundary()）
5. [ ] S6-5：写 resolution 判定逻辑（range.py::_check_resolution()）
6. [ ] S6-6：写单元测试（先 RED）
7. [ ] S6-7：端到端测试（逐 bar 喂入，全等比对）
8. [ ] S6-8：真实数据冒烟（记录 range 分布）
9. [ ] S6-9：回补文档

## 完成标志

S6-7 绿 + S6-8 无意外崩溃 + S6-9 文档更新。
```

**执行计划：** 第六刀开工前 2 天  
**预计工作量：** 3 小时  
**负责人：** 待分配

---

### P1-2：Types.py 补充 Range 和 Lifespan 数据结构（第六刀）

**需要补充：**

```python
# src/malf/types.py

from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class RangeSnapshot:
    """Range 快照（v2.1 §2 Range）
    
    表示一个震荡区间的完整状态。
    """
    range_id: Optional[str]
    break_bar_dt: datetime
    break_price: float
    old_wave_direction: Literal["UP", "DOWN"]
    
    # 两层边界
    boundary_high_init: float  # 从 transition 冻结
    boundary_low_init: float
    boundary_high_now: float   # 基于 init 演化
    boundary_low_now: float
    
    evolution_count: int  # boundary_now 演化次数
    
    # Resolution 状态
    range_state: Literal["alive", "resolved_up", "resolved_down"]
    resolution_bar_dt: Optional[datetime]
    resolution_direction: Optional[Literal["UP", "DOWN"]]
    resolution_distance_pct: Optional[float]
    
    # 分类
    range_type: Optional[Literal["continuation_range", "reversal_range"]]
    
    span_bars: int  # 持续 bar 数
    
    # Lineage
    range_rule_version: str  # 例如 "v2.1.0"


@dataclass
class WaveLifespanSnapshot:
    """Wave Lifespan 快照（v2.1 §3 Lifespan）
    
    表示一个已终止 wave 的生命周期统计。
    """
    wave_id: str
    direction: Literal["UP", "DOWN"]
    
    # 统计指标（v2.1 恢复完整集）
    new_count: int           # 新高/低次数
    no_new_span: int         # 停滞 bars
    wave_span_total: int     # 总持续 bars
    progress_pct: float      # 推进百分比
    
    price_range: float       # 价格范围
    primitive_count: int     # 包含的 primitive 数量
    pivot_count: int         # 包含的 pivot 数量
    
    # Rank（percentile_rank，范围 [0, 1)）
    new_count_rank: Optional[float]
    no_new_span_rank: Optional[float]
    wave_span_total_rank: Optional[float]
    progress_pct_rank: Optional[float]
    
    # Birth descriptors
    birth_type: Literal["initial", "post_break"]
    candidate_replacement_count: int
    confirmation_distance_pct: float
    birth_range_span_bars: Optional[int]
    birth_range_boundary_evolution_count: Optional[int]
    
    # Peer sample 信息
    peer_sample_size: int
    peer_sample_cutoff: datetime


@dataclass
class RangeLifespanSnapshot:
    """Range Lifespan 快照（v2.1 §3 Lifespan）
    
    表示一个已 resolved Range 的生命周期统计。
    """
    range_id: str
    range_type: Literal["continuation_range", "reversal_range"]
    
    # 统计指标
    span_bars: int
    evolution_count: int
    resolution_distance_pct: float
    amplitude_pct: float  # boundary_now 范围
    
    # Rank
    span_bars_rank: Optional[float]
    evolution_count_rank: Optional[float]
    resolution_distance_pct_rank: Optional[float]
    
    # Peer sample 信息
    peer_sample_size: int
    peer_sample_cutoff: datetime
```

**执行计划：** 第六刀 S6-3  
**预计工作量：** 1 小时  
**负责人：** 待分配

---

### P1-3：WaveStructuralSnapshot 补充完整字段（第八刀前）

**需要补充：**

基于 v2.1 Service §2，WaveStructuralSnapshot 需要包含：
1. Core 层字段（已有）
2. Range 层字段（第六刀补充）
3. WaveLifespan 字段（第七刀补充）
4. RangeLifespan 字段（第七刀补充）
5. Structural Position 字段（第八刀补充）

**当前缺失：** Range/Lifespan/Structural Position 全部字段

**执行计划：** 分三刀逐步补充  
**预计工作量：** 每刀 30 分钟  
**负责人：** 待分配

---

## P2：中优先级修订（改善可维护性）

### P2-1：增加版本常量文件（第六刀）

**需要创建：** `src/malf/version.py`

```python
"""MALF 版本常量

定义所有 rule_version 字符串，避免硬编码。
"""

# 规格版本
MALF_SPEC_VERSION = "v2.1"

# 各层 rule version
CORE_RULE_VERSION = "v2.1.0"
RANGE_RULE_VERSION = "v2.1.0"
LIFESPAN_RULE_VERSION = "v2.1.0"
STRUCTURAL_POSITION_RULE_VERSION = "v2.1.0"
SERVICE_RULE_VERSION = "v2.1.0"

# 子规则版本
PIVOT_DETECTION_RULE_VERSION = "fractal-k2-v1"
PERCENTILE_RANK_FORMULA_VERSION = "strict-less-than-v1"

# 完整 rule_versions 字典
def get_rule_versions() -> dict:
    """返回完整的 rule_versions 字典（用于快照）"""
    return {
        "core": CORE_RULE_VERSION,
        "range": RANGE_RULE_VERSION,
        "lifespan": LIFESPAN_RULE_VERSION,
        "structural_position": STRUCTURAL_POSITION_RULE_VERSION,
        "service": SERVICE_RULE_VERSION,
    }
```

**执行计划：** 第六刀 S6-3（与 types.py 同步）  
**预计工作量：** 15 分钟  
**负责人：** 待分配

---

### P2-2：增加 reason_codes 枚举（第九刀前）

**需要创建：** `src/malf/reason_codes.py`

```python
"""MALF Reason Codes 枚举

定义所有 None 值的 reason_codes，对应 v2.1 Service §8 失败模式。
"""

from enum import Enum

class ReasonCode(str, Enum):
    """失败/退化原因码"""
    
    # Core 层
    UNINITIALIZED = "uninitialized"
    INSUFFICIENT_BARS = "insufficient_bars"
    
    # Range 层
    RANGE_ALIVE = "range_alive"
    NO_TRANSITION = "no_transition"
    
    # Lifespan 层
    PEER_SAMPLE_INSUFFICIENT = "peer_sample_insufficient"
    WAVE_ALIVE = "wave_alive"
    NO_TERMINATED_WAVES = "no_terminated_waves"
    
    # Structural Position 层
    SAME_DIR_INSUFFICIENT_HISTORY = "same_dir_insufficient_history"
    OPP_DIR_INSUFFICIENT_HISTORY = "opp_dir_insufficient_history"
    CROSS_NO_PRIOR_WAVE = "cross_no_prior_wave"
    CROSS_ALIVE_WARNING = "cross_alive_warning"
    
    # Service 层
    INPUT_VALIDATION_FAILED = "input_validation_failed"
    TIMESTAMP_DISCONTINUITY = "timestamp_discontinuity"


def format_reason_codes(codes: list[ReasonCode]) -> list[str]:
    """将枚举转换为字符串列表"""
    return [code.value for code in codes]
```

**执行计划：** 第八刀（Structural Position 时需要）  
**预计工作量：** 20 分钟  
**负责人：** 待分配

---

### P2-3：BUILD-PLAN.md 增加 v2.1 章节映射（第六刀前）

**修订：** 在 BUILD-PLAN.md 每刀的开头增加 v2.1 章节映射

```markdown
## 第六刀：Range 层

**目标**：实现 Range 对象、boundary 演化、resolution 判定  
**覆盖（v2.1 §2 Range）**：
- §1：层职责
- §2：Range 对象定义
- §3：两层边界模型 ⚠️ 核心设计
- §4-§5：Resolution 判定
- §6：Range 分类 ⚠️ 命名陷阱
- §7：不变量 R1-R5
- §8：持久化
- §9：测试覆盖要求

**v2.1 关键变更：**
- boundary_init vs boundary_now 使用场景对照表（§3）
- resolution_distance_pct 公式明确（§5）
- continuation 命名陷阱警告框（§6）
```

**执行计划：** 第六刀开工前  
**预计工作量：** 30 分钟  
**负责人：** 待分配

---

## P3：低优先级修订（长期完善）

### P3-1：性能基准文档（第九刀后）

**需要创建：** `docs/PERFORMANCE-BENCHMARKS.md`

**内容：** 基于 v2.1 Bridge §7

```markdown
# MALF Engine 性能基准

## 目标

基于 v2.1 Bridge §7 的性能要求：
- 单 symbol 单 bar 处理时间：< 10ms
- 内存消耗：peer_sample N=1000 时约 XXX MB
- 存储增长：每 symbol 每年约 XXX MB

## 测试环境

- CPU: AMD Ryzen 7 5800H
- RAM: 32GB
- OS: Windows 11
- Python: 3.10

## 基准测试

### 1. Core 层性能

| 场景 | Bar 数 | 平均处理时间 | P99 | 内存峰值 |
|------|--------|-------------|-----|---------|
| Simple up wave | 100 | XX ms | XX ms | XX MB |
| Complex transition | 100 | XX ms | XX ms | XX MB |

### 2. 端到端性能

| 层 | Bar 数 | 平均处理时间 | 备注 |
|----|--------|-------------|------|
| Core only | 1000 | XX ms | 已完成 |
| + Range | 1000 | XX ms | 第六刀后测 |
| + Lifespan | 1000 | XX ms | 第七刀后测 |
| + Structural Position | 1000 | XX ms | 第八刀后测 |
| Full pipeline | 1000 | XX ms | 第九刀后测 |

### 3. 真实数据性能

sh600000（上证指数 ETF）前 5000 根日线：
- 总处理时间：XX 秒
- 平均每 bar：XX ms
- Pivot 数量：XX 个
- Wave 数量：XX 个
- Range 数量：XX 个

## 瓶颈分析

（第九刀后补充）

## 优化建议

（第九刀后补充）
```

**执行计划：** 第九刀完成后  
**预计工作量：** 2 小时  
**负责人：** 待分配

---

### P3-2：错误处理和日志规范（第六刀起）

**需要创建：** `docs/ERROR-HANDLING-GUIDELINES.md`

**内容：**

```markdown
# MALF Engine 错误处理和日志规范

## 原则

基于 v2.1 Service §8 失败模式：
1. **不抛异常**：任何失败都用 None + reason_codes
2. **不跳过 bar**：保证每个 bar 都有 snapshot 输出
3. **可审计**：所有 None 都必须有 reason_codes

## 错误分类

### 1. 预期失败（退化处理）

使用 reason_codes，不记录 error 日志：
- peer_sample 不足
- transition alive
- wave alive

### 2. 输入异常（拒绝处理）

返回 rejected snapshot，记录 warning 日志：
- timestamp 不连续
- OHLC 数据无效
- bar_dt 回退

### 3. 实现 bug（应该崩溃）

抛出 AssertionError 或 RuntimeError：
- 状态机违反不变量
- 数据结构不一致

## 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 状态机转换 | "Transition to UP_ALIVE at bar_dt=..." |
| INFO | 关键事件 | "New wave confirmed: wave_id=..." |
| WARNING | 输入异常 | "Timestamp discontinuity detected..." |
| ERROR | 实现 bug | "Invariant violated: guard is None while wave is alive" |

## 示例

```python
# 预期失败（退化）
if peer_sample_size < PEER_SAMPLE_MIN_N:
    return WaveLifespanSnapshot(
        ...,
        new_count_rank=None,
        reason_codes=[ReasonCode.PEER_SAMPLE_INSUFFICIENT],
    )

# 输入异常（拒绝）
if bar_dt <= self._last_bar_dt:
    logger.warning(f"Bar datetime out of order: {bar_dt} <= {self._last_bar_dt}")
    return WaveStructuralSnapshot(
        ...,
        usage="rejected",
        reason_codes=[ReasonCode.TIMESTAMP_DISCONTINUITY],
    )

# 实现 bug（崩溃）
assert self._current_wave is not None, \
    f"Invariant violated: wave is None while system_state={self._system_state}"
```
```

**执行计划：** 第六刀起逐步完善  
**预计工作量：** 1 小时（初稿）+ 每刀 15 分钟（完善）  
**负责人：** 待分配

---

### P3-3：CI/CD 集成（第九刀后）

**需要创建：** `.github/workflows/test.yml`

```yaml
name: MALF Engine Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=term-missing
      
      - name: Check code coverage
        run: |
          coverage report --fail-under=80
```

**执行计划：** 第九刀完成后  
**预计工作量：** 1 小时  
**负责人：** 待分配

---

## 修订进度追踪

| ID | 优先级 | 修订项 | 负责人 | 截止时间 | 状态 |
|----|--------|--------|--------|---------|------|
| P0-1 | P0 | 类型名重命名 | - | 第六刀前 | ⏸ 待分配 |
| P0-2 | P0 | v2.1 文档引用说明 | - | 立即 | ⏸ 待分配 |
| P1-1 | P1 | Range 实施准备文档 | - | 第六刀前 2 天 | ⏸ 待分配 |
| P1-2 | P1 | Types.py 补充数据结构 | - | 第六刀 S6-3 | ⏸ 待分配 |
| P1-3 | P1 | WaveStructuralSnapshot 补充 | - | 第八刀前 | ⏸ 待分配 |
| P2-1 | P2 | 版本常量文件 | - | 第六刀 | ⏸ 待分配 |
| P2-2 | P2 | reason_codes 枚举 | - | 第八刀 | ⏸ 待分配 |
| P2-3 | P2 | BUILD-PLAN 章节映射 | - | 第六刀前 | ⏸ 待分配 |
| P3-1 | P3 | 性能基准文档 | - | 第九刀后 | ⏸ 待分配 |
| P3-2 | P3 | 错误处理规范 | - | 第六刀起 | ⏸ 待分配 |
| P3-3 | P3 | CI/CD 集成 | - | 第九刀后 | ⏸ 待分配 |

---

## 附录：快速执行清单

### 第六刀开工前（3 天倒计时）

**Day -3：**
- [ ] P1-1：创建 T6-RANGE-IMPLEMENTATION-GUIDE.md（3 小时）
- [ ] P2-3：更新 BUILD-PLAN 章节映射（30 分钟）

**Day -2：**
- [ ] P0-2：补充代码 docstring 版本说明（20 分钟）

**Day -1：**
- [ ] P0-1：类型名重命名（30 分钟）
  - [ ] 改 types.py
  - [ ] 改 core_engine.py
  - [ ] 改 tests/
  - [ ] 跑测试确认绿

**Day 0（第六刀开工）：**
- [ ] P1-2：补充 Range 数据结构（1 小时）
- [ ] P2-1：创建 version.py（15 分钟）
- [ ] 开始 S6-1（推 fixture）

---

**本清单最后更新：** 2026-07-26  
**下次更新：** 第六刀开工日
