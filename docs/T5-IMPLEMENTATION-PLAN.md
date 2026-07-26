# 第五刀实施计划（T5 Implementation Plan）

**目标**: 闭合 Core 层，补齐关键逻辑缺口，为 Range 层打下坚实基础

**范围**: 方案 A（最小闭环）
1. Guard 更新逻辑（D9 守护唯一性铁律）
2. Wave bar_count 计算
3. 第一条 Replay 确定性测试（O8 铁律验证）

**原则**: 
- 严格遵循 TDD（RED → GREEN → REFACTOR）
- 每个 Step 完成后运行全部测试
- 文档先行，代码验证

---

## Task 1: Guard 更新逻辑（D9 守护唯一性铁律）

**规格依据**: 
- 规格 §2.5 / D9 守护唯一性铁律
- IMPLEMENTATION-CONTRACT-PATCH.md C-01

**规格原文**（D9）:
> HH/LL 推进只更新 `progress_extreme`；**只有后续确认的 HL（up）或 LH（down）才能替换 guard**。
> guard 是一个**单元素栈**——只有「回撤确认」的极值才能替换。

**当前状态**:
- ✅ D16 Progress Confirmation 已实现（HH/LL 更新 progress）
- ❌ Guard 替换逻辑未实现（HL/LH 应替换 guard）

**缺失场景**:
```
UP_ALIVE 状态：
- 初始 guard = L1 = 96
- 后续确认 L3 = 98（新的 L pivot）
- 应该：guard 从 96 更新为 98
- 当前：不做任何处理（缺失）

DOWN_ALIVE 状态：
- 初始 guard = H1 = 100
- 后续确认 H3 = 95（新的 H pivot）
- 应该：guard 从 100 更新为 95
- 当前：不做任何处理（缺失）
```

### Step 清单

#### S5-T1-1: 推导 fixture 预期输出

**任务**: 人肉推导 guard 更新场景的每根 bar 预期 snapshot

**场景设计**:
- **场景 A（UP guard 更新）**: H0→L1→H2>H0 进入 UP_ALIVE，后续 L3>L1 替换 guard
- **场景 B（DOWN guard 更新）**: L0→H1→L2<L0 进入 DOWN_ALIVE，后续 H3<H1 替换 guard

**验证点**:
- k=2 窗口填充正确
- Guard 替换时刻与 L3/H3 confirm_bar_dt 一致
- system_state 保持 UP_ALIVE/DOWN_ALIVE（不进 transition）
- progress_extreme 不受影响（D9：guard 和 progress 独立）

**交付物**: 
- `docs/t5_guard_update_derivation.md`（推导过程）
- 不创建 JSON fixture（单元测试足够，见 S5-T1-3）

**状态**: ⏭️ 待开始

---

#### S5-T1-2: 写单元测试（TDD RED）

**任务**: 创建 `tests/test_guard_update.py`，包含 4 个测试场景

**测试场景**:
1. `test_guard_update_up_alive` — UP_ALIVE 状态下，新 L pivot 替换 guard
2. `test_guard_update_down_alive` — DOWN_ALIVE 状态下，新 H pivot 替换 guard
3. `test_guard_no_update_on_progress_pivot` — UP_ALIVE 状态下，H pivot 不更新 guard（只更新 progress）
4. `test_guard_replaces_previous_guard` — 新 guard 直接替换旧 guard（单元素栈）

**断言内容**:
- `current_effective_guard_price` 更新正确
- `current_effective_guard_extreme_bar_dt` / `current_effective_guard_confirm_bar_dt` 正确
- `system_state` 仍为 UP_ALIVE/DOWN_ALIVE
- `progress_extreme_price` 不受 guard 更新影响

**预期结果**: 4 个测试全部 FAILED（因为逻辑未实现）

**状态**: ⏭️ 待开始

---

#### S5-T1-3: 实现 guard 更新逻辑（TDD GREEN）

**任务**: 在 `src/malf/core_engine.py` 实现 guard 更新逻辑

**实现位置**: `on_bar()` 方法的 S3 分支（UP_ALIVE/DOWN_ALIVE）

**新增方法**:
```python
def _update_guard_if_valid(self, new_pivot: Pivot) -> None:
    """D9 守护唯一性铁律: 更新 guard（如果新 pivot 是回撤类型）。
    
    规则（D9）：
    - UP wave: 只有新 L pivot（回撤）才能替换 guard
    - DOWN wave: 只有新 H pivot（回撤）才能替换 guard
    - Guard 是单元素栈，新的回撤 pivot 直接替换旧的
    """
```

**修改点**:
1. `on_bar()` S3 分支：在 D16 Progress Confirmation 之后调用 `_update_guard_if_valid()`
2. 新增 `_update_guard_if_valid()` 方法
3. 对称实现 UP/DOWN 方向

**预期结果**: 4 个测试全部 PASSED

**状态**: ⏭️ 待开始

---

#### S5-T1-4: 回归测试

**任务**: 运行全部测试，确保没有破坏现有功能

**验证点**:
- 所有现有测试仍然通过
- 新增 4 个 guard 更新测试通过
- 预期测试总数：34 + 4 = 38 passed, 1 skipped

**状态**: ⏭️ 待开始

---

#### S5-T1-5: 文档回补

**任务**: 更新 BUILD-PLAN.md，标记 Task 1 完成

**状态**: ⏭️ 待开始

---

### 完成标志

Task 1 done = S5-T1-2 RED + S5-T1-3 GREEN + S5-T1-4 全绿（38 passed, 1 skipped）

---

## Task 2: Wave bar_count 计算

**规格依据**: 
- 规格 §2.9 CoreStateSnapshot 字段
- Range 层依赖（future）

**当前状态**:
- ❌ `CoreStateSnapshot` 没有 `bar_count` 字段
- ❌ 没有跟踪 wave 持续时间

**需求**:
- 每个 snapshot 记录当前 wave 已持续的 bar 数量
- 从 initialization 确认的 bar 开始计数
- break 时记录最终 bar_count

### Step 清单

#### S5-T2-1: 扩展数据结构

**任务**: 在 `src/malf/types.py::CoreStateSnapshot` 添加 `bar_count` 字段

**新增字段**:
```python
@dataclass(frozen=True)
class CoreStateSnapshot:
    # ... 现有字段
    bar_count: int | None  # Wave 持续 bar 数量，uninitialized 时为 None
```

**状态**: ⏭️ 待开始

---

#### S5-T2-2: 写单元测试（TDD RED）

**任务**: 扩展现有测试，验证 bar_count 计算

**测试文件**: 
- `tests/test_core_uninitialized_to_up_alive.py` — 验证初始化后 bar_count 从 1 开始
- `tests/test_guard_break.py` — 验证 break 时 bar_count 正确

**断言内容**:
- uninitialized 时 `bar_count` 为 None
- 初始化确认的 bar：`bar_count` = 1
- 后续每根 bar：`bar_count` 递增
- break 时记录最终 bar_count

**预期结果**: 测试 FAILED（字段未实现）

**状态**: ⏭️ 待开始

---

#### S5-T2-3: 实现 bar_count 计算（TDD GREEN）

**任务**: 在 `src/malf/core_engine.py` 实现 bar_count 跟踪

**实现要点**:
1. 添加 `_wave_start_bar_dt: str | None` 实例变量（初始化时记录）
2. 在 `_make_snapshot()` 中计算 `bar_count`（当前 bar 距离 wave_start 的数量）
3. 初始化时设置 `_wave_start_bar_dt = bar.bar_dt`
4. transition 后清空（new wave 时重新设置）

**计算逻辑**:
```python
if self._wave_start_bar_dt is None:
    bar_count = None
else:
    bar_count = self._bars 中从 _wave_start_bar_dt 到当前 bar 的数量
```

**预期结果**: 所有测试 PASSED

**状态**: ⏭️ 待开始

---

#### S5-T2-4: 回归测试

**任务**: 运行全部测试

**预期**: 38 passed, 1 skipped（bar_count 不影响现有逻辑）

**状态**: ⏭️ 待开始

---

### 完成标志

Task 2 done = S5-T2-2 RED + S5-T2-3 GREEN + S5-T2-4 全绿

---

## Task 3: 第一条 Replay 确定性测试（O8 铁律验证）

**规格依据**: 
- 规格 §7 / O8 Replay 确定性
- BUILD-CONTRACT.md 验收线第一条

**规格原文**（O8）:
> 相同 source facts + source_run_id + core_rule_version + pivot_detection_rule_version + core_event_ordering_version + price_policy ⇒ 相同 pivots/structures/waves/breaks/transitions/candidates/snapshots。

**当前状态**:
- ❌ 没有任何 replay 测试
- ❌ 没有验证 `runtime_fingerprint` 的隔离性
- ❌ 没有验证版本标记正确性

### Step 清单

#### S5-T3-1: 设计 replay 测试场景

**任务**: 文档化 replay 测试的验证目标

**场景设计**:
- **场景 A（基础 replay）**: 同一 fixture，跑两遍，逐字节比对
- **场景 B（跨 session）**: reset engine，重新喂相同 bars，验证结果一致

**验证点**:
- 所有 snapshot 字段一致（除 `runtime_fingerprint`）
- `runtime_fingerprint` 记录但不影响 replay（规格 §7.6）
- 版本标记正确（`core_rule_version` / `pivot_detection_rule_version`）

**交付物**: `docs/t5_replay_test_design.md`

**状态**: ⏭️ 待开始

---

#### S5-T3-2: 写 replay 测试（TDD RED）

**任务**: 创建 `tests/test_replay_determinism.py`

**测试场景**:
1. `test_replay_same_fixture_twice` — 同一 fixture 跑两遍，比对所有 snapshot
2. `test_replay_cross_session` — 两个独立 engine 实例，相同输入，比对结果
3. `test_runtime_fingerprint_isolation` — 验证 `runtime_fingerprint` 不同但其他字段相同

**断言内容**:
- 除 `runtime_fingerprint` 外，所有字段逐字节相同
- `runtime_fingerprint` 格式正确（`py3.10.19|win32|CPython`）
- 版本字段非空且格式正确

**预期结果**: 测试 PASSED（如果现有实现已确定性）或 FAILED（发现非确定性问题）

**状态**: ⏭️ 待开始

---

#### S5-T3-3: 修复非确定性问题（如果发现）

**任务**: 如果测试 FAILED，定位并修复非确定性来源

**可能问题**:
- dict 迭代顺序（Python 3.7+ 应该不存在）
- 时间戳泄漏（除 runtime_fingerprint 外）
- 浮点精度问题（int_fixed 应该已避免）

**状态**: ⏭️ 待开始（conditional）

---

#### S5-T3-4: 回归测试

**任务**: 运行全部测试

**预期**: 38 + 3 = 41 passed, 1 skipped

**状态**: ⏭️ 待开始

---

### 完成标志

Task 3 done = S5-T3-2 测试实现 + S5-T3-3 修复（如需） + S5-T3-4 全绿

---

## 第五刀总体验收标准

第五刀完成 = 以下全部达标：

1. ✅ D9 守护唯一性铁律有专门测试验证（4 个测试）
2. ✅ Wave bar_count 字段实现并通过测试
3. ✅ O8 至少 1 条 replay 确定性测试通过（3 个测试）
4. ✅ 所有测试通过：预计 41 passed, 1 skipped
5. ✅ BUILD-PLAN.md 更新，标记第五刀完成

---

## 执行顺序

按以下顺序执行，每完成一个 Task 运行全部测试：

1. **Task 1: Guard 更新逻辑** — 补上最大的功能缺口
2. **Task 2: Wave bar_count** — 小而独立，可快速完成
3. **Task 3: Replay 测试** — 验证 O8 铁律

---

**创建日期**: 2026-07-26  
**预计时间**: 2-3 天  
**原则**: TDD 严格，文档先行，测试驱动
