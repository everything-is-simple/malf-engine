# malf-engine 建造计划（唯一活文档）

> **这是项目的唯一规划文档。** 所有任务、进度、待做功能全在这里。
> 
> **原则**：
> - 做完一个 step 勾一个
> - 只写当前这一刀的详细 step
> - 一个大功能由几大刀完成（比如 Core 有 6 刀，Range 有 4 刀）
> - 验收线见 BUILD-CONTRACT.md
> - 本文只管「下一步动手做什么」

**最后更新**: 2026-07-26

---

## 📍 项目全貌

**目标**: MALF v2.1 完整引擎（5 层）

**权威规格**: `I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`

### 5 层架构

| 层 | 职责 | 状态 | 刀数 |
|----|------|------|------|
| **Core** | 结构状态机（UP/DOWN/TRANSITION） | ✅ 完成 | 6 刀（T1-T5 + C-07） |
| **Range** | 震荡区间识别（一等公民对象） | ⏸ 待做 | 4 刀（T6.1-T6.4） |
| **Lifespan** | 波段生命周期排名 | ⏸ 待做 | 3 刀（T7.1-T7.3） |
| **Structural Position** | 结构位置视图（4 视图 + 标签） | ⏸ 待做 | 3 刀（T8.1-T8.3） |
| **Service** | 对外接口、失败模式、持久化 | ⏸ 待做 | 2 刀（T9.1-T9.2） |

**总计**: 6 + 4 + 3 + 3 + 2 = **18 刀**

**当前进度**: 6/18 刀完成（33%）

---

## ✅ Core 层（已完成 - 6 刀）

**规格**: MALF_01_Core_v2_1-deepseek-20260726.md  
**测试**: 58 passed  
**完成日期**: 2026-07-26

### T1: UP 初始化（✅ 完成）

**目标**: 从 UNINITIALIZED 走到 up_alive（H0→L1→H2>H0）

**完成内容**:
- ✅ Pivot 检测（k=2 延迟确认）
- ✅ UP 初始化判定（H2 > H0）
- ✅ Guard = L1, Progress = H2
- ✅ 8 个测试通过

**Fixture**: `uninitialized_to_up_alive.json`

---

### T2: DOWN 初始化（✅ 完成）

**目标**: 从 UNINITIALIZED 走到 down_alive（L0→H1→L2<L0）

**完成内容**:
- ✅ DOWN 初始化判定（L2 < L0）
- ✅ Guard = H1, Progress = L2
- ✅ 6 个测试通过

**Fixture**: `t2_down_initialization.json`

---

### T3: Guard Break（✅ 完成）

**目标**: 从 alive 走到 transition（同向突破）

**完成内容**:
- ✅ LH break（up_alive → transition，close < guard）
- ✅ HL break（down_alive → transition，close > guard）
- ✅ Boundary 初始化（boundary_init 冻结）
- ✅ 4 个测试通过

**Fixture**: `t3_same_direction_break_up.json`, `t3_same_direction_break_down.json`

---

### T4: Candidate 演化（✅ 完成）

**目标**: transition 期间 candidate 跟踪与替换

**完成内容**:
- ✅ Flip-flop 替换逻辑（更极端 → 替换）
- ✅ Candidate 初始化（第一个反向 pivot）
- ✅ 6 个测试通过

**Fixture**: `t4_candidate_flipflop_up.json`, `t4_candidate_flipflop_down.json`

---

### T5: Guard/Progress 更新（✅ 完成）

**目标**: new wave 确认后更新 guard 和 progress

**完成内容**:
- ✅ New wave 判定（pivot 超越 boundary_init）
- ✅ Guard 更新（回撤 pivot → guard）
- ✅ Progress Confirmation（HH/LL 推进）
- ✅ 5 个测试通过

**Fixture**: `t5_new_wave_up.json`, `t5_progress_update.json`

---

### C-07: Pivot 替换补丁（✅ 完成）

**目标**: 早期 pivot 替换逻辑（规格补丁）

**完成内容**:
- ✅ H0 替换（更高 H → 替换 H0）
- ✅ L0 替换（更低 L → 替换 L0）
- ✅ L1 替换（更低 L → 替换 L1）
- ✅ H1 替换（更高 H → 替换 H1）
- ✅ 4 个测试通过

**规则**: 见本文档「C-07 规则详解」章节

**Fixture**: `c07_*.json`（4 个）

---

## ⏸ Range 层（待做 - 4 刀）

**规格**: MALF_02_Range_v2_1-deepseek-20260726.md §1-§9  
**预计时间**: 8-12 天  
**当前状态**: 未开始

### T6.1: Range 诞生（⏸ 待做 - 下一刀）

**目标**: Guard break 触发 Range 诞生

**规格覆盖**: §2-§3
- §2: Range 对象定义
- §3: 两层边界模型（boundary_init / boundary_now）

**核心工作**:
1. Range 对象结构
   ```python
   @dataclass
   class RangeSnapshot:
       range_id: str
       break_bar_dt: datetime
       break_price: float
       old_wave_direction: Literal["UP", "DOWN"]
       
       # 两层边界 ⚠️ 核心设计
       boundary_high_init: float  # 从 transition 冻结
       boundary_low_init: float
       boundary_high_now: float   # 基于 init 演化
       boundary_low_now: float
       
       range_state: Literal["alive", "resolved_up", "resolved_down"]
       span_bars: int
   ```

2. Range 诞生逻辑
   - Guard break 时创建 Range 对象
   - boundary_init = boundary_now（初始相同）
   - range_state = "alive"

3. 测试覆盖
   - UP wave break → Range 诞生（LH break）
   - DOWN wave break → Range 诞生（HL break）
   - Boundary 初始化正确

**Fixture 设计**:
- `t6_1_range_birth_up.json`（UP wave → LH break）
- `t6_1_range_birth_down.json`（DOWN wave → HL break）

**Step 清单**:
- [ ] S6.1-1: 推 2 个 fixture 预期输出
- [ ] S6.1-2: 预期输出定稿存 JSON
- [ ] S6.1-3: 补充 RangeSnapshot 数据结构（types.py）
- [ ] S6.1-4: 实现 Range 诞生逻辑（range_engine.py）
- [ ] S6.1-5: 写单元测试（2 个 fixture）
- [ ] S6.1-6: 端到端测试（逐 bar 喂入，全等比对）
- [ ] S6.1-7: 真实数据冒烟（记录 Range 诞生频率）

**完成标志**: S6.1-6 绿 + S6.1-7 无崩溃

**预计时间**: 2-3 天

---

### T6.2: Boundary 演化（⏸ 待做）

**目标**: 新 pivot 确认后更新 boundary_now

**规格覆盖**: §3 两层边界模型

**核心工作**:
1. Boundary 演化规则
   - 新 H pivot → 更新 boundary_high_now（如果更高）
   - 新 L pivot → 更新 boundary_low_now（如果更低）
   - boundary_init 永不变（Core 状态机用）
   - evolution_count 计数

2. 测试覆盖
   - Boundary 演化 1 次
   - Boundary 演化 3 次
   - Boundary 不演化（pivot 未超越）

**Fixture 设计**:
- `t6_2_boundary_evolution.json`（演化 3 次）
- `t6_2_boundary_no_evolution.json`（无演化）

**Step 清单**:
- [ ] S6.2-1: 推 2 个 fixture 预期输出
- [ ] S6.2-2: 预期输出定稿存 JSON
- [ ] S6.2-3: 实现 _evolve_boundary() 方法
- [ ] S6.2-4: 写单元测试（2 个 fixture）
- [ ] S6.2-5: 端到端测试
- [ ] S6.2-6: 真实数据冒烟（记录 evolution_count 分布）

**完成标志**: S6.2-5 绿 + S6.2-6 无崩溃

**预计时间**: 1-2 天

---

### T6.3: Resolution 判定（⏸ 待做）

**目标**: New wave 确认后判定 Range resolution

**规格覆盖**: §4-§5
- §4: Resolution 判定（T6 定理）
- §5: resolution_distance_pct 公式

**核心工作**:
1. Resolution 判定（T6 定理）
   - New wave 向上 → resolved_up
   - New wave 向下 → resolved_down
   - 未 new wave → alive

2. resolution_distance_pct 公式
   ```python
   resolution_distance_pct = (
       abs(confirmation_pivot.extreme_price - range.break_price)
       / abs(boundary_high_init - boundary_low_init)
   )
   ```

3. 测试覆盖
   - resolved_up（向上突破）
   - resolved_down（向下突破）
   - alive（未 resolution）
   - distance_pct 极端情况（0.05 / 0.95）

**Fixture 设计**:
- `t6_3_resolution_up.json`
- `t6_3_resolution_down.json`
- `t6_3_resolution_distance_extreme.json`

**Step 清单**:
- [ ] S6.3-1: 推 3 个 fixture 预期输出
- [ ] S6.3-2: 预期输出定稿存 JSON
- [ ] S6.3-3: 实现 _check_resolution() 方法
- [ ] S6.3-4: 实现 resolution_distance_pct 计算
- [ ] S6.3-5: 写单元测试（3 个 fixture）
- [ ] S6.3-6: 端到端测试
- [ ] S6.3-7: 真实数据冒烟（记录 resolution 分布）

**完成标志**: S6.3-6 绿 + S6.3-7 无崩溃

**预计时间**: 2-3 天

---

### T6.4: Range 分类（⏸ 待做）

**目标**: continuation_range / reversal_range 分类

**规格覆盖**: §6 Range 分类 ⚠️ **命名陷阱**

**⚠️ 致命陷阱**: continuation 延续的是 **break 方向**，不是旧 wave 方向！

| 场景 | 旧 wave | Break 方向 | Resolution 方向 | Range 类型 |
|------|---------|-----------|----------------|-----------|
| 1 | UP | 向下 break | 向下 resolution | continuation（延续 break 下行） |
| 2 | UP | 向下 break | 向上 resolution | reversal（反转 break 下行） |
| 3 | DOWN | 向上 break | 向上 resolution | continuation（延续 break 上行） |
| 4 | DOWN | 向上 break | 向下 resolution | reversal（反转 break 上行） |

**核心工作**:
1. Range 分类逻辑
   - 判定 break 方向（LH / HL）
   - 判定 resolution 方向（UP / DOWN）
   - 分类：break 方向 == resolution 方向 → continuation，否则 reversal

2. 测试覆盖
   - 4 种场景各 1 个测试
   - 专门的 test_continuation_naming_trap()

**Fixture 设计**:
- `t6_4_continuation_scenario_1.json`（UP→下 break→下 resolution）
- `t6_4_reversal_scenario_2.json`（UP→下 break→上 resolution）
- `t6_4_continuation_scenario_3.json`（DOWN→上 break→上 resolution）
- `t6_4_reversal_scenario_4.json`（DOWN→上 break→下 resolution）

**Step 清单**:
- [ ] S6.4-1: 推 4 个 fixture 预期输出
- [ ] S6.4-2: 预期输出定稿存 JSON
- [ ] S6.4-3: 实现 _classify_range() 方法
- [ ] S6.4-4: 写单元测试（4 个 fixture + naming trap 测试）
- [ ] S6.4-5: 端到端测试
- [ ] S6.4-6: 真实数据冒烟（记录 continuation/reversal 比例）
- [ ] S6.4-7: 回补文档

**完成标志**: S6.4-5 绿 + S6.4-6 无崩溃 + S6.4-7 文档更新

**预计时间**: 2-3 天

---

## ⏸ Lifespan 层（待做 - 3 刀）

**规格**: MALF_03_Lifespan_v2_1-deepseek-20260726.md §1-§7  
**预计时间**: 6-9 天  
**当前状态**: 未开始

### T7.1: Wave 统计指标（⏸ 待做）

**目标**: 计算已终止 wave 的统计指标

**规格覆盖**: §2 统计指标

**核心工作**:
1. Wave 统计指标
   - new_count: 新高/低次数
   - no_new_span: 停滞 bars
   - wave_span_total: 总持续 bars
   - progress_pct: 推进百分比
   - price_range: 价格范围
   - primitive_count: primitive 数量
   - pivot_count: pivot 数量

2. 测试覆盖
   - 简单 wave（3 pivots）
   - 复杂 wave（10+ pivots，多次 HH/LL）
   - 边界情况（单 primitive wave）

**预计时间**: 2-3 天

---

### T7.2: 双轨 peer_sample（⏸ 待做）

**目标**: UP/DOWN 独立样本池

**规格覆盖**: §3-§4 双轨户口与排名

**核心工作**:
1. 双轨 peer_sample
   - UP 样本池（所有已终止 UP waves）
   - DOWN 样本池（所有已终止 DOWN waves）
   - 最小样本量（PEER_SAMPLE_MIN_N = 30）
   - 时间窗口（可选，默认全历史）

2. percentile_rank 计算
   ```python
   rank = count(peer < self) / len(peer_sample)
   ```
   - 严格小于（不含等于）
   - 范围 [0, 1)

3. 测试覆盖
   - peer_sample 不足（< 30）→ rank = None
   - peer_sample 充足（≥ 30）→ 计算 rank
   - 边界情况（自己是最小/最大）

**预计时间**: 2-3 天

---

### T7.3: Range Lifespan（⏸ 待做）

**目标**: Range 生命周期统计

**规格覆盖**: §5 Range Lifespan

**核心工作**:
1. Range 统计指标
   - span_bars: 持续 bars
   - evolution_count: boundary 演化次数
   - resolution_distance_pct: resolution 距离
   - amplitude_pct: boundary_now 范围

2. Rank 计算
   - span_bars_rank
   - evolution_count_rank
   - resolution_distance_pct_rank

3. 测试覆盖
   - 简单 range（未演化）
   - 复杂 range（演化 5 次）
   - peer_sample 不足（< 20）

**预计时间**: 1-2 天

---

## ⏸ Structural Position 层（待做 - 3 刀）

**规格**: MALF_04_Structural_Position_v2_1-deepseek-20260726.md §1-§9  
**预计时间**: 6-9 天  
**当前状态**: 未开始

### T8.1: Rank 视图（⏸ 待做）

**目标**: up_rank / down_rank 计算

**预计时间**: 2-3 天

---

### T8.2: Momentum 视图（⏸ 待做）

**目标**: momentum 计算（同向 - 反向）

**预计时间**: 2-3 天

---

### T8.3: Cross Compare + 标签（⏸ 待做）

**目标**: cross_compare 计算 + 标签规则

**预计时间**: 2-3 天

---

## ⏸ Service 层（待做 - 2 刀）

**规格**: MALF_05_Service_v2_1-deepseek-20260726.md §1-§8  
**预计时间**: 3-5 天  
**当前状态**: 部分完成（20%，仅 snapshot 结构）

### T9.1: Usage 判定 + 失败模式（⏸ 待做）

**目标**: usage 判定（normal/degraded/rejected）+ reason_codes

**预计时间**: 1-2 天

---

### T9.2: 持久化 + 中断恢复（⏸ 待做）

**目标**: 序列化支持 + 中断恢复

**预计时间**: 2-3 天

---

## 📋 C-07 规则详解（已实现）

### 规则名称
**C-07: 早期 Pivot 替换规则**

### 适用阶段
UNINITIALIZED 阶段，尚未确认初始波段（< 3 confirmed pivots）

### 核心原则
**选择"更极端"的 pivot**

替换的本质是：**在序列完整前，动态更新"最极端"的 pivot**

### 4 种替换场景

#### 场景 1: H0 替换
- **条件**: 已确认 H0，尚未确认 L1，新确认一个 H
- **判定**: 新 H > H0 → 替换；否则忽略
- **操作**: 用新 H 替换 H0，L1 候选范围重新开始

#### 场景 2: L0 替换
- **条件**: 已确认 L0，尚未确认 H1，新确认一个 L
- **判定**: 新 L < L0 → 替换；否则忽略
- **操作**: 用新 L 替换 L0，H1 候选范围重新开始

#### 场景 3: L1 替换
- **条件**: 已确认 H0 和 L1，尚未确认 H2，新确认一个 L
- **判定**: 新 L < L1 → 替换；否则忽略
- **操作**: 用新 L 替换 L1（更新 guard 候选）

#### 场景 4: H1 替换
- **条件**: 已确认 L0 和 H1，尚未确认 L2，新确认一个 H
- **判定**: 新 H > H1 → 替换；否则忽略
- **操作**: 用新 H 替换 H1（更新 guard 候选）

### 实现策略

```python
def should_replace(new_pivot: Pivot, old_pivot: Pivot) -> bool:
    """判断是否应该用 new_pivot 替换 old_pivot"""
    if new_pivot.pivot_type == PivotType.H:
        return new_pivot.price > old_pivot.price  # H: 更高则替换
    else:
        return new_pivot.price < old_pivot.price  # L: 更低则替换
```

### 边界情况

1. **多次替换**: H0 → H0' → H0''，每次选择更极端的
2. **替换后不满足条件**: L0_new 替换后，L2 可能仍 >= L0_new
3. **不替换**: 新 pivot 不够极端，忽略
4. **无替换**: 干净序列 H0 → L1 → H2

### 测试覆盖

- ✅ C07-1: L0 替换（DOWN 方向）
- ✅ C07-2: H0 替换（UP 方向）
- ✅ C07-3: L1 替换（UP 方向）
- ✅ C07-4: H1 替换（DOWN 方向）

---

## 🔧 工程化任务（v1.0 之后）

这些任务在 5 层完成后执行：

### 序列化支持
- JSON 导出/导入 snapshot
- 状态持久化
- **预计时间**: 4 小时

### CI/CD
- GitHub Actions 自动测试
- 代码覆盖率检查
- **预计时间**: 4 小时

### PyPI 发布
- 打包配置
- 版本管理
- **预计时间**: 4 小时

### 性能优化
- 基准测试
- 热路径优化
- **预计时间**: 8 小时

---

## 📝 修订清单（滚动记录）

### P0: 阻塞性修订

#### P0-1: 类型名重命名（T6.1 前）
- 当前: `WaveProbabilitySnapshot`（v2.0）
- 目标: `WaveStructuralSnapshot`（v2.1）
- 影响: types.py + core_engine.py + tests/
- 预计: 30 分钟
- 状态: ⏸ 待执行

#### P0-2: v2.1 文档引用说明（立即）
- 在核心模块 docstring 中增加版本说明
- 明确 v2.0 → v2.1 语义等价
- 预计: 20 分钟
- 状态: ⏸ 待执行

### P1: 高优先级修订

#### P1-1: Types.py 补充数据结构（T6.1）
- RangeSnapshot
- WaveLifespanSnapshot
- RangeLifespanSnapshot
- 预计: 1 小时
- 状态: ⏸ 待 T6.1

#### P1-2: WaveStructuralSnapshot 补充字段（T8.3 前）
- Range 层字段（T6.4）
- Lifespan 层字段（T7.3）
- Structural Position 层字段（T8.3）
- 预计: 每刀 30 分钟
- 状态: ⏸ 分三刀逐步补充

### P2: 中优先级修订

#### P2-1: 版本常量文件（T6.1）
- 创建 src/malf/version.py
- 定义所有 rule_version 字符串
- 预计: 15 分钟
- 状态: ⏸ 待 T6.1

#### P2-2: Reason codes 枚举（T8.1 前）
- 创建 src/malf/reason_codes.py
- 定义所有失败/退化原因码
- 预计: 20 分钟
- 状态: ⏸ 待 T8.1

### P3: 低优先级修订

#### P3-1: 性能基准文档（T9.2 后）
- 创建 docs/PERFORMANCE-BENCHMARKS.md
- 预计: 2 小时
- 状态: ⏸ v1.0 后

#### P3-2: 错误处理规范（T6.1 起）
- 创建 docs/ERROR-HANDLING-GUIDELINES.md
- 预计: 1 小时初稿 + 每刀 15 分钟完善
- 状态: ⏸ T6.1 起

#### P3-3: CI/CD 集成（T9.2 后）
- 创建 .github/workflows/test.yml
- 预计: 1 小时
- 状态: ⏸ v1.0 后

---

## 🎯 下一步行动

**立即任务**: T6.1 Range 诞生（2-3 天）

**准备工作**（T6.1 开工前）:
1. [ ] P0-2: 补充 v2.1 文档引用说明（20 分钟）
2. [ ] P0-1: 类型名重命名（30 分钟）
3. [ ] 阅读规格: MALF_02_Range_v2_1-deepseek-20260726.md §1-§3

**开工清单**:
1. [ ] S6.1-1: 推 2 个 fixture
2. [ ] S6.1-2: 预期输出存 JSON
3. [ ] S6.1-3: 补充 RangeSnapshot 数据结构
4. [ ] S6.1-4: 实现 Range 诞生逻辑
5. [ ] S6.1-5: 写单元测试
6. [ ] S6.1-6: 端到端测试
7. [ ] S6.1-7: 真实数据冒烟

---

## 📚 核心文档（只看 2 个）

1. **本文档** (BUILD-PLAN.md) - 唯一活文档，所有任务全在这里 ⭐
2. BUILD-CONTRACT.md - 验收标准、7 条铁律（稳定，几乎不变）

**其他文档**: 都是参考材料，不需要天天看。

---

## 🔧 开发命令速查

```bash
# 运行所有测试
/d/miniconda/py310/python.exe -m pytest

# 运行 Core 层测试
/d/miniconda/py310/python.exe -m pytest tests/test_core*.py tests/test_initialization.py tests/test_guard_break.py

# 详细输出
/d/miniconda/py310/python.exe -m pytest -v

# 真实数据验证
/d/miniconda/py310/python.exe tests/smoke/test_real_tdx_data.py
```

---

**维护规则**: 每完成一刀更新完成标志，每开新刀展开该刀的 Step 清单  
**负责人**: 项目所有者  
**最后更新**: 2026-07-26
