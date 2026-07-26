# 第六刀 Day -1 准备工作完成报告

**日期：** 2026-07-26  
**任务：** P0-1 类型名重命名 + P1-2 数据结构补充 + P2-1 版本常量  
**状态：** ✅ 已完成

---

## 完成的任务

### ✅ P0-1：类型名重命名

**目标：** 将所有 `WaveProbabilitySnapshot` 重命名为 `WaveStructuralSnapshot`，对齐 MALF v2.1 命名规范。

**执行内容：**
- 全局搜索并替换所有文档中的 `WaveProbabilitySnapshot` → `WaveStructuralSnapshot`
- 影响文件：
  - `CLAUDE.md`
  - `README.md`
  - `docs/BUILD-CONTRACT.md`
  - `docs/FINAL-SUMMARY-20260726.md`
  - `docs/MALF_V2_1_AUTHORITY_REFERENCE.md`
  - `docs/REVISION-CHECKLIST.md`
  - `docs/T6-DAY-MINUS-2-COMPLETION.md`
  - `docs/T6-DAY-MINUS-3-COMPLETION.md`
  - `docs/T6-RANGE-IMPLEMENTATION-GUIDE.md`
  - `docs/TASK-COMPLETION-REPORT-20260726.md`
  - `docs/V2_1_ALIGNMENT_COMPLETION_REPORT.md`

**验证结果：** ✅ 所有文档已更新，残留的 `WaveProbability` 仅在示例代码中（可接受）

---

### ✅ P1-2：Range 数据结构补充

**目标：** 在 `src/malf/types.py` 中添加 Range 层所需的数据结构。

**新增内容：**

#### 1. RangeState enum
```python
class RangeState(str, Enum):
    """Range 生命周期状态（v2.1 Range §4）。"""
    ALIVE = "alive"        # Range 活跃中（尚未 resolve）
    RESOLVED = "resolved"  # Range 已解决（new wave 确认）
```

#### 2. RangeResolutionType enum
```python
class RangeResolutionType(str, Enum):
    """Range resolution 分类（v2.1 Range §6）。
    
    命名陷阱警告（v2.1 Range §6.2）：
    - continuation: 延续 **break 方向**（不是旧 wave 方向）
    - reversal: 反转 **break 方向**
    """
    CONTINUATION = "continuation"  # 延续 break 方向
    REVERSAL = "reversal"          # 反转 break 方向
```

#### 3. RangeSnapshot dataclass
包含完整的 Range 层状态快照字段：
- **Identity**: symbol, timeframe, bar_dt, range_id
- **生命周期**: range_state, birth_bar_dt, resolution_bar_dt
- **两层边界**: boundary_init_high/low（冻结），boundary_now_high/low（演化）
- **Break 方向**: break_direction, old_wave_direction
- **Resolution 信息**: resolution_type, resolution_distance, confirmation_pivot_*
- **版本信息**: range_rule_version, schema_version

**关键设计说明：**
- **两层边界模型**（v2.1 Range §3）：
  - `boundary_init`: 冻结边界，Core 层用于 resolution 判定
  - `boundary_now`: 演化边界，Range 层用于统计
- **命名陷阱警告**（v2.1 Range §6）：
  - continuation = 延续 **break 方向**（不是旧 wave 方向）
  - reversal = 反转 **break 方向**

**验证结果：** ✅ 导入成功，数据类定义无语法错误

---

### ✅ P2-1：版本常量文件

**目标：** 创建统一的版本常量文件 `src/malf/version.py`。

**文件内容：**
- `CORE_RULE_VERSION = "core-v0.0.1"`
- `PIVOT_DETECTION_RULE_VERSION = "fractal-k2-v1"`
- `PRICE_POLICY = "int_fixed"`
- `RANGE_RULE_VERSION = "v2.1.0"`
- `CORE_SNAPSHOT_SCHEMA_VERSION = "malf-core-snapshot-v0"`
- `RANGE_SNAPSHOT_SCHEMA_VERSION = "malf-range-snapshot-v0"`

**验证结果：** ✅ 导入成功，版本常量正确输出

---

## 测试验证结果

```bash
/d/miniconda/py310/python.exe -m pytest -v
```

**结果：** ✅ **47 passed, 1 skipped, 1 warning in 0.14s**

**详情：**
- 47 个测试全部通过
- 1 个测试跳过（test_candidate_replacement_same_direction，预期行为）
- 1 个警告（pytest cache 权限，不影响功能）

**结论：** 所有修改完全兼容现有代码，测试套件全绿。

---

## 数据结构设计亮点

### RangeSnapshot 关键设计

#### 1. 两层边界模型（v2.1 Range §3 核心设计）

**问题：** 为什么需要两层边界？

**答案：** Core 层和 Range 层对边界的使用场景不同：
- **Core 层需要稳定的边界** 进行 resolution 判定（T6 定理）
- **Range 层需要演化的边界** 进行统计和分类（R2 不变量）

**实现：**
- `boundary_init`: 从 transition 诞生时冻结，**永不改变**，Core 层专用
- `boundary_now`: 基于 init 演化，逐 pivot 扩展，Range 层专用

**使用场景对照表：**

| 使用场景 | 使用边界 | 理由 |
|---------|---------|------|
| Resolution 判定（T6） | init | 状态机稳定性 |
| Resolution distance 计算 | init | 与判定一致 |
| Range 统计（width, evolution_count） | now | 反映真实震荡 |
| Range 分类（continuation/reversal） | break_direction | 语义清晰 |

**警告：** 混用 init/now 会导致状态机不稳定或统计失真。

#### 2. 命名陷阱（v2.1 Range §6.2）

**问题：** continuation/reversal 是相对于什么方向？

**错误理解：** 相对于**旧 wave 方向**
- UP wave → 下突破 = reversal ❌
- UP wave → 上突破 = continuation ❌

**正确理解：** 相对于 **break 方向**
- UP wave → 下 break（break_direction=DOWN）→ 下突破 = continuation ✅
- UP wave → 下 break（break_direction=DOWN）→ 上突破 = reversal ✅
- DOWN wave → 上 break（break_direction=UP）→ 上突破 = continuation ✅
- DOWN wave → 上 break（break_direction=UP）→ 下突破 = reversal ✅

**实现保护：**
- `RangeSnapshot` 同时记录 `break_direction` 和 `old_wave_direction`
- docstring 中明确警告命名陷阱
- 未来测试将覆盖所有 4 种组合

---

## 交付物清单

| 类别 | 文件 | 状态 |
|------|------|------|
| 类型重命名 | 11 个文档文件 | ✅ 已更新 |
| 数据结构 | `src/malf/types.py` | ✅ 新增 3 个类型 |
| 版本常量 | `src/malf/version.py` | ✅ 新增文件 |
| 完成报告 | `docs/T6-DAY-MINUS-1-COMPLETION.md` | ✅ 本文档 |

---

## 下一步：Day 0 任务

**目标：** 推 Range 层 fixture 预期输出

**任务内容：**
1. 使用 `debug_t6.py` 工具辅助人肉推导
2. 创建 6 个 Range fixture（含不同 resolution 场景）
3. 复核两大铁律：
   - 窗口填充 >= k（避免首 bar 无法确认）
   - 严格不等式（pivot 确认规则）

**预计工作量：** 2-3 小时（人肉推导 + 工具验证）

**参考文档：**
- `docs/T6-RANGE-IMPLEMENTATION-GUIDE.md`（34 KB 完整指南）
- `docs/BUILD-CONTRACT.md`（Fixture 设计铁律）
- MALF v2.1 Range 定义（`I:\asteria-riskbench-Definitive-validated\...\MALF_02_Range_v2_1-deepseek-20260726.md`）

---

## 总结

✅ **Day -1 准备工作完成。**

- P0-1 类型名重命名：✅ 11 个文件已更新
- P1-2 Range 数据结构：✅ 3 个类型已添加
- P2-1 版本常量文件：✅ version.py 已创建
- 测试验证：✅ 47 passed, 1 skipped（与修改前一致）

**准备状态：** 已就绪，可以开始 Day 0（推 fixture）。

---

**Day -1 准备工作完成。准备进入 Day 0（推 fixture）。**
