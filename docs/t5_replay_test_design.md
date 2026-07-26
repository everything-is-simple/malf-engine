# T5 Replay 确定性测试设计（O8 铁律验证）

**设计日期**: 2026-07-26  
**规格依据**: 规格 §7 / O8 Replay 确定性  
**设计人**: Claude Opus 4.8

---

## 规格原文

**O8 Replay 确定性**：
> 相同 source facts + source_run_id + core_rule_version + pivot_detection_rule_version + core_event_ordering_version + price_policy ⇒ 相同 pivots/structures/waves/breaks/transitions/candidates/snapshots。
>
> 重放差异必须归因到某个已登记版本，禁止解释为「正常浮动」。

**§7.6 runtime_fingerprint**：
> `runtime_fingerprint` 记录但不进 lineage_hash（审计元数据）。
> 格式：`py{version}|{platform}|{implementation}`
> 例如：`py3.10.19|win32|CPython`

---

## 测试目标

验证 MALF 引擎的确定性：相同输入 → 相同输出（除了不参与 replay 的审计元数据）。

### 核心验证点

1. **基础 replay**：同一 fixture，跑两遍，所有 snapshot 逐字段比对
2. **跨 session replay**：两个独立 engine 实例，相同输入，结果一致
3. **runtime_fingerprint 隔离**：`runtime_fingerprint` 不同但其他字段相同

---

## 测试场景设计

### 场景 A: 基础 Replay（同一 engine 两次运行）

**输入**: 使用 `uninitialized_to_up_alive.json` fixture（12 根 bars，已验证）

**流程**:
1. 创建 engine1，喂入 12 根 bars，记录所有 snapshots → run1_snapshots
2. 创建 engine2，喂入相同 12 根 bars，记录所有 snapshots → run2_snapshots
3. 逐 snapshot 比对 run1_snapshots 和 run2_snapshots

**比对规则**:
- 除 `runtime_fingerprint` 外，所有字段必须完全相同
- `runtime_fingerprint` 允许不同（审计元数据，不参与 replay）
- 使用 `dataclass.replace()` 排除 `runtime_fingerprint` 后比对

**预期结果**: 
- 所有 snapshot 完全一致（除 runtime_fingerprint）
- 如果有差异 → 发现非确定性问题，需要修复

---

### 场景 B: 跨 Session Replay（重置 engine）

**输入**: 同样使用 `uninitialized_to_up_alive.json`

**流程**:
1. 创建 engine，喂入前 6 根 bars，记录 snapshots → partial_run
2. 销毁 engine（模拟 session 结束）
3. 创建新 engine，喂入全部 12 根 bars，记录 snapshots → full_run
4. 比对 partial_run 的前 6 个 snapshot 与 full_run 的前 6 个

**预期结果**:
- 前 6 个 snapshot 完全一致
- 验证「中断后重新运行」不影响确定性

---

### 场景 C: runtime_fingerprint 格式验证

**输入**: 任意 snapshot

**验证点**:
1. `runtime_fingerprint` 格式正确：`py{version}|{platform}|{implementation}`
2. 包含 Python 版本（如 `py3.10.19`）
3. 包含平台（如 `win32` 或 `linux`）
4. 包含实现（如 `CPython`）

**预期结果**:
- 格式符合规格 §7.6
- 不为空字符串

---

### 场景 D: 版本标记验证

**输入**: 任意 snapshot

**验证点**:
1. `core_rule_version` 非空且格式正确（如 `core-v0.0.1`）
2. `pivot_detection_rule_version` 非空且格式正确（如 `fractal-k2-v1`）
3. `price_policy` 非空且为有效值（如 `int_fixed`）
4. `schema_version` 非空且格式正确（如 `malf-core-snapshot-v0`）

**预期结果**:
- 所有版本字段都有值
- 格式符合约定

---

## 测试用例设计

基于以上场景，设计 4 个单元测试：

### Test 1: `test_replay_same_fixture_twice`
- **场景**: 场景 A
- **验证**: 两次运行产生相同 snapshots（除 runtime_fingerprint）

### Test 2: `test_replay_cross_session`
- **场景**: 场景 B
- **验证**: 重启 engine 不影响 replay 确定性

### Test 3: `test_runtime_fingerprint_isolation`
- **场景**: 场景 C
- **验证**: `runtime_fingerprint` 格式正确且不影响 replay

### Test 4: `test_version_fields_present`
- **场景**: 场景 D
- **验证**: 所有版本字段非空且格式正确

---

## 实现要点

### 比对辅助函数

```python
def snapshots_equal_except_fingerprint(s1: CoreStateSnapshot, s2: CoreStateSnapshot) -> bool:
    """比对两个 snapshot，忽略 runtime_fingerprint。"""
    s1_normalized = dataclasses.replace(s1, runtime_fingerprint="", note="")
    s2_normalized = dataclasses.replace(s2, runtime_fingerprint="", note="")
    return s1_normalized == s2_normalized
```

### Fixture 加载

```python
def load_golden_fixture():
    """加载 uninitialized_to_up_alive.json fixture。"""
    fixture_path = Path(__file__).parent / "fixtures" / "uninitialized_to_up_alive.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)
```

---

## 可能发现的问题

### 问题 1: dict 迭代顺序
- **症状**: 相同输入但 snapshot 字段顺序不同
- **原因**: Python 3.7+ dict 保序，应该不存在
- **修复**: 检查是否有未排序的集合操作

### 问题 2: 时间戳泄漏
- **症状**: `bar_dt` 或其他字段包含当前时间
- **原因**: 误用 `datetime.now()` 而非输入数据的时间
- **修复**: 确保所有时间字段来自 PriceBar 输入

### 问题 3: 浮点精度
- **症状**: 价格字段微小差异
- **原因**: float 精度问题
- **修复**: 确认 `int_fixed` 策略正确应用

### 问题 4: 随机性
- **症状**: 字段值随机变化
- **原因**: 使用了 `random` 模块或系统随机源
- **修复**: 移除所有随机性

---

## 测试实现计划

### Step 1: 写测试（TDD RED）
- 实现 4 个测试用例
- 预期可能全部 PASS（如果现有实现已确定性）
- 或者 FAIL（发现非确定性问题）

### Step 2: 修复问题（如需）
- 如果测试 FAIL，分析根本原因
- 修复非确定性来源
- 重新运行测试直到全部 PASS

### Step 3: 回归测试
- 运行全部测试
- 确保修复没有破坏现有功能

---

## 验收标准

Task 3 完成 = 以下全部达标：

1. ✅ 至少 3 条 replay 确定性测试实现
2. ✅ 所有 replay 测试 PASSED
3. ✅ runtime_fingerprint 格式验证通过
4. ✅ 版本字段验证通过
5. ✅ 全部测试通过（预计 46+ passed, 1 skipped）

---

**设计完成日期**: 2026-07-26  
**下一步**: S5-T3-2 写 replay 测试（TDD RED）
