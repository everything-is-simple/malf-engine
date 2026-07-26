# T6 第六刀 Range 层 - Day 2 任务提示

**日期**: 2026-07-26  
**任务**: 扩展测试覆盖 - P1 边界场景  
**前置**: Day 1 完成（4 个 P0 测试通过）

---

## 📋 任务目标

补充 Range 层的边界场景测试，验证实现在复杂情况下的正确性：

- **R5**: Boundary Evolution - 多次演化场景
- **R6**: Long-lived Range - 长期未 resolve 场景

---

## 🎯 Day 2 任务分解

### S7-1: 设计 R5 fixture（多次演化）
**目标**: 验证 boundary 演化逻辑的累加正确性

**场景设计**:
- TRANSITION 期间出现 3-4 次 boundary 演化
- 包含 H 和 L pivot 交替演化
- 最终 resolve（continuation 或 reversal 均可）

**验证点**:
- ✅ `evolution_count` 正确累加（应为 3 或 4）
- ✅ `boundary_now_high` 单调递增（对于 H pivot）
- ✅ `boundary_now_low` 单调递减（对于 L pivot）
- ✅ `boundary_init` 保持冻结（不受演化影响）
- ✅ Resolution 判定基于 `boundary_init`（非 `boundary_now`）

### S7-2: 设计 R6 fixture（长期未 resolve）
**目标**: 验证长期 TRANSITION 状态的稳定性

**场景设计**:
- TRANSITION 持续 10+ bars
- 包含多个 pivot 但都不符合 resolution 条件
- 可能包含 1-2 次 boundary 演化
- 最终在 fixture 结束时仍处于 TRANSITION

**验证点**:
- ✅ 状态稳定保持 TRANSITION
- ✅ Range 字段持续有效（不被清空）
- ✅ Candidate 逻辑正常工作（可能多次更新）
- ✅ 无内存泄漏或状态污染

### S7-3: 实现测试并验证
- 创建 R5/R6 的 JSON fixture
- 添加测试函数到 `test_range_layer.py`
- 运行测试确保 6/6 通过
- 更新 Day 2 报告

---

## 📐 Fixture 设计参考

### R5 示例结构（多次演化）

```
初始状态: DOWN wave alive
d10: guard break → TRANSITION (Range 诞生)
     boundary_init = [H:100, L:80]
     boundary_now = [H:100, L:80]

d12: L pivot @ 75 confirmed → evolution #1
     boundary_now = [H:100, L:75]

d14: H pivot @ 105 confirmed → evolution #2
     boundary_now = [H:105, L:75]

d16: L pivot @ 70 confirmed → evolution #3
     boundary_now = [H:105, L:70]

d18: L pivot @ 65 breaks boundary_init.low=80 → resolve (continuation)
     resolution_type = "continuation"
     evolution_count = 3
     boundary_init 仍为 [H:100, L:80]（用于判定）
```

**关键验证**:
- Resolution 判定使用 `boundary_init.low=80`（非 `boundary_now.low=70`）
- Evolution count = 3（不包含 resolution pivot）

### R6 示例结构（长期未 resolve）

```
初始状态: UP wave alive
d10: guard break → TRANSITION (Range 诞生)
     boundary_init = [H:120, L:100]
     boundary_now = [H:120, L:100]

d12-d20: 多个 pivot 在 boundary 内部震荡
     例如: L@105, H@115, L@102, H@118...
     可能触发 1-2 次 boundary 演化（边界扩张）
     但所有 pivot 都未突破 boundary_init

d22: fixture 结束，仍处于 TRANSITION
     system_state = TRANSITION
     range_resolution_type = None
     evolution_count = 1 或 2（取决于是否有演化）
```

**关键验证**:
- `system_state == TRANSITION`（未 resolve）
- `range_resolution_bar_dt == None`
- `range_resolution_type == None`
- Range 其他字段仍有效（birth, boundary 等）

---

## 🔍 实现提示

### Fixture 文件位置
```
tests/fixtures/range/
├── R5_multi_evolution.json          # 多次演化
└── R6_long_lived_unresolved.json    # 长期未 resolve
```

### 测试函数模板

```python
def test_r5_multi_evolution():
    """R5: 多次 boundary 演化场景"""
    fixture = load_fixture("R5_multi_evolution")
    bars = bars_from_fixture(fixture)
    engine = CoreEngine()
    
    snapshots = {}
    for bar in bars:
        snapshot = engine.process_bar(bar)
        if snapshot.bar_dt in fixture["check_points"]:
            snapshots[snapshot.bar_dt] = snapshot
    
    # 检查演化中间状态
    mid_snapshot = snapshots["d14"]  # 假设 d14 为中间演化点
    assert mid_snapshot.system_state == SystemState.TRANSITION
    assert mid_snapshot.range_evolution_count == 2
    assert mid_snapshot.range_boundary_now_high > mid_snapshot.range_boundary_init_high
    
    # 检查最终 resolve
    final_snapshot = snapshots["d18"]
    assert final_snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]
    assert final_snapshot.range_resolution_type in ["continuation", "reversal"]
    assert final_snapshot.range_evolution_count == 3

def test_r6_long_lived_unresolved():
    """R6: 长期未 resolve 场景"""
    fixture = load_fixture("R6_long_lived_unresolved")
    bars = bars_from_fixture(fixture)
    engine = CoreEngine()
    
    snapshots = {}
    for bar in bars:
        snapshot = engine.process_bar(bar)
        if snapshot.bar_dt in fixture["check_points"]:
            snapshots[snapshot.bar_dt] = snapshot
    
    # 检查最终状态
    final_snapshot = snapshots[fixture["check_points"][-1]]
    assert final_snapshot.system_state == SystemState.TRANSITION
    assert final_snapshot.range_resolution_bar_dt is None
    assert final_snapshot.range_resolution_type is None
    
    # 验证 Range 字段仍有效
    assert final_snapshot.range_birth_bar_dt is not None
    assert final_snapshot.range_boundary_init_high is not None
    assert final_snapshot.range_boundary_init_low is not None
```

---

## 🧪 验证流程

### Step 1: 手工推导 R5 fixture
1. 设计波段结构（选择 UP 或 DOWN 起始）
2. 设计 guard break 触发点
3. 设计 3-4 个演化 pivot（注意 R2 不变量）
4. 设计 resolution pivot（突破 boundary_init）
5. 计算所有 check_points 的预期状态

### Step 2: 手工推导 R6 fixture
1. 设计波段结构
2. 设计 guard break 触发点
3. 设计多个内部震荡 pivot（不突破 boundary_init）
4. 可选：设计 1-2 次边界扩张（但不 resolve）
5. 确保最终仍处于 TRANSITION

### Step 3: 创建 JSON fixture
- 使用 Day 0 的 fixture 模板
- 填充 bars 和 pivots 数据
- 填充 check_points 预期快照

### Step 4: 运行测试
```bash
pytest tests/test_range_layer.py::test_r5_multi_evolution -v
pytest tests/test_range_layer.py::test_r6_long_lived_unresolved -v
pytest tests/test_range_layer.py -v  # 运行全部 6 个测试
```

### Step 5: 回归测试
```bash
pytest tests/ -v  # 确保 Core 层未受影响
```

---

## 📊 成功标准

- ✅ R5 测试通过（验证多次演化）
- ✅ R6 测试通过（验证长期未 resolve）
- ✅ 全部 6 个 Range 测试通过
- ✅ 全部 47 个 Core 测试保持通过
- ✅ 无新的技术债务引入

---

## 💡 设计考虑

### R5 的复杂度选择
- **最小复杂度**: 3 次演化（验证累加逻辑）
- **推荐复杂度**: 3-4 次演化（覆盖 H/L 交替）
- **避免过度**: 不要超过 5 次（测试应聚焦验证点）

### R6 的持续时间选择
- **最小持续**: 10 bars（验证状态稳定性）
- **推荐持续**: 12-15 bars（包含多个 pivot）
- **避免过长**: 不要超过 20 bars（fixture 应保持可读）

### 对称性考虑
- R5 建议选择 DOWN wave 起始（与 R1/R2 对称）
- R6 建议选择 UP wave 起始（与 R3/R4 对称）
- 覆盖所有方向组合

---

## 📚 参考文档

- **Day 0 完成报告**: docs/T6-DAY-0-COMPLETION.md
- **Day 1 实现报告**: docs/T6-DAY-1-REPORT.md
- **Range 规范**: docs/v2.1-Range-specification.md（如有）
- **现有测试**: tests/test_range_layer.py

---

## 🚀 开始执行

Day 2 的工作量相对较小，预计 1-2 小时完成。重点在于：
1. Fixture 设计的合理性（符合真实市场逻辑）
2. 验证点的全面性（覆盖关键不变量）
3. 测试的可读性（清晰的断言和注释）

准备好后，开始 S7-1！🎯
