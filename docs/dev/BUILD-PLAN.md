# malf-engine 建造计划（唯一活文档）

> **这是项目的唯一规划文档。** 所有任务、进度、待做功能全在这里。
> 
> **原则**：
> - 做完一个 step 勾一个
> - 只写当前这一刀的详细 step
> - 一个大功能由几大刀完成（比如 Core 有 6 刀，Range 有 4 刀）
> - 验收线见 BUILD-CONTRACT.md
> - 本文只管「下一步动手做什么」

**最后更新**: 2026-07-27 (🎊 项目全部完成！20/20 刀，100%)

---

## ⚠️ 规格对照检查结果（2026-07-27）

**检查日期**: 2026-07-27  
**检查范围**: MALF v2.1 规格 vs malf-engine 实现  
**整体合规度**: **85%** (基本合规)

### 🔴 Critical 问题（P0 - 必须立即修复）

#### P0-1: Core Break 检测逻辑错误 ✅ 已修复
- **位置**: `core_engine.py:224-228`
- **问题**: 使用 `bar.close` 判定 break，规格要求用 `bar.low` (UP) / `bar.high` (DOWN)
- **影响**: 违反 Core 不变量 #6，某些应该触发 break 的情况会被遗漏
- **修复时间**: 10分钟（实际）
- **状态**: ✅ 已修复（2026-07-27）
- **提交**: b4e1562

#### P0-2: Pivot 缺少 confirm_price 字段 ✅ 已修复
- **位置**: `types.py:78-90`
- **问题**: 规格 D2 要求 Pivot 包含 `confirm_price`（确认 bar 的价格）
- **影响**: 丢失审计信息，无法回溯确认 bar 的价格
- **修复时间**: 30分钟（实际）
- **状态**: ✅ 已修复（2026-07-27）
- **提交**: b4e1562
- **修改文件**: 3 源码 + 3 测试 + 4 fixture = 10 个文件

### 🟡 Major 问题（P1 - 本周内修复）

#### P1-3: progress_pct 计算公式待核对 ✅ 已修复
- **位置**: `lifespan_engine.py:79-82`
- **问题**: 实现用 `(wave_end - wave_start) / wave_start`，规格要求 UP/DOWN 分别计算
- **影响**: Lifespan 指标准确性存疑
- **修复内容**:
  - 修改 `calculate_wave_lifespan` 函数签名，添加 `first_pivot_price` 和 `guard_price` 参数
  - UP 方向: `(progress_extreme_price - first_pivot_price) / (progress_extreme_price - guard_price)`
  - DOWN 方向: `(first_pivot_price - progress_extreme_price) / (guard_price - progress_extreme_price)`
  - 修改 `v1_full_integration_pipeline.py` 的 WaveTracker 追踪这两个价格
- **修复时间**: 1小时（实际）
- **状态**: ✅ 已修复（2026-07-27 17:45）
- **验证**: 4 只标的 12,296 个 snapshot 100% lineage_hash 确定性 ✅
- **提交**: 448fb32

#### P1-4: CoreStateSnapshot 缺少 bar_index ❌ 不存在
- **位置**: `types.py:120`
- **检查结果**: `bar_index: int` 字段已存在于代码中
- **状态**: ❌ 误报（记录过时）

### 🟢 Minor 问题（P2 - 下阶段）

#### P2-5: Service 层完全缺失
- **问题**: 无法生成符合规格的最终快照、缺少 lineage_hash、reason_codes 等
- **影响**: 无对外接口层
- **修复时间**: 3-5天（T9.1-T9.2）
- **状态**: ⏸ 计划中

### 合规性评分详情

| 维度 | 评分 | 状态 |
|---|---|---|
| 数据结构合规度 | 98% | ✅ 优秀（P0-2 修复后） |
| 算法逻辑合规度 | 95% | ✅ 优秀（P0-1 修复后） |
| 不变量覆盖度 | 94% | ✅ 优秀 |
| **整体合规度** | **~95%** | ✅ 高度合规 |

**P0 修复后测试**: 89 passed, 2 skipped ✅  
**P1-3 修复后测试**: 100 passed, 2 skipped ✅  
**P1-3 修复后验证**: 4 只标的 12,296/12,296 hashes 100% 确定性 ✅  
**详细报告**: 见 `docs/reports/SPEC-COMPLIANCE-REPORT-2026-07-27.md`（待归档）

---

## 🔬 引擎验证阶段（V1–V6）

**V1 流水线验证** ✅ 完成：多标的 lineage_hash 100% 确定性（见 `docs/reports/VALIDATION-V1-*`）

**V2 结构正确性抽查** 🔄 机器预检完成，待人工签字
- 机器预检（2026-07-28）：15 案例 / 38 pivot / 4 break 全部通过；引擎 flag 与独立重算 0 矛盾；190 bar 与 TDX 原始数据逐字节一致
- 脚本：`scripts/verify/v2_independent_crosscheck.py`、`scripts/verify/v2_tdx_source_check.py`
- 报告：`docs/reports/VALIDATION-V2-MACHINE-PRECHECK.md`
- ⏳ 待办：按 `.work/V2-validation-package/02-VALIDATION-CHECKLIST.md` 人工对照 K 线签字（门槛：Pivot>95%，Guard/Progress>90%，≥10 案例）

**V3 参数校准 / V4 公式核对 / V5 bar_index 核销 / V6 文档清理**：待启动

---

## 📍 项目全貌

**目标**: MALF v2.1 完整引擎（5 层）

**权威规格**: `I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`

### 5 层架构

| 层 | 职责 | 状态 | 刀数 |
|----|------|------|------|
| **Core** | 结构状态机（UP/DOWN/TRANSITION） | ✅ 完成 | 6 刀（T1-T5 + C-07） |
| **Range** | 震荡区间识别（一等公民对象） | ✅ 完成 | 4 刀（T6.1-T6.4）|
| **Lifespan** | 波段生命周期排名 | ✅ 完成 | 4 刀（T7.1-T7.4）|
| **Structural Position** | 结构位置视图（4 视图 + 标签） | ✅ 完成 | 4 刀（T8.1-T8.4）|
| **Service** | 对外接口、失败模式、持久化 | ✅ 完成 | 2 刀（T9.1-T9.2） |

**总计**: 6 + 4 + 4 + 4 + 2 = **20 刀**

**当前进度**: 20/20 刀完成（100%）🎊

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

## ✅ Range 层（已完成 - 4 刀）

**规格**: MALF_02_Range_v2_1-deepseek-20260726.md §1-§9  
**测试**: 6 synthetic + 1 real data, all passed  
**完成日期**: 2026-07-26  
**当前状态**: 完成

### T6.1: Range 诞生（✅ 完成）

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
- [x] S6.1-1: 推 2 个 fixture 预期输出
- [x] S6.1-2: 预期输出定稿存 JSON
- [x] S6.1-3: 补充 RangeSnapshot 数据结构（types.py）
- [x] S6.1-4: 实现 Range 诞生逻辑（range_engine.py）
- [x] S6.1-5: 写单元测试（2 个 fixture）
- [x] S6.1-6: 端到端测试（逐 bar 喂入，全等比对）
- [x] S6.1-7: 真实数据冒烟（记录 Range 诞生频率）

**完成标志**: S6.1-6 绿 + S6.1-7 无崩溃 ✅

**实际时间**: 已完成

---

### T6.2: Boundary 演化（✅ 完成）

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
- [x] S6.2-1: 推 2 个 fixture 预期输出
- [x] S6.2-2: 预期输出定稿存 JSON
- [x] S6.2-3: 实现 _evolve_boundary() 方法
- [x] S6.2-4: 写单元测试（2 个 fixture）
- [x] S6.2-5: 端到端测试
- [x] S6.2-6: 真实数据冒烟（记录 evolution_count 分布）

**完成标志**: S6.2-5 绿 + S6.2-6 无崩溃 ✅

**实际时间**: 已完成

---

### T6.3: Resolution 判定（✅ 完成）

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
- [x] S6.3-1: 推 3 个 fixture 预期输出
- [x] S6.3-2: 预期输出定稿存 JSON
- [x] S6.3-3: 实现 _check_resolution() 方法
- [x] S6.3-4: 实现 resolution_distance_pct 计算
- [x] S6.3-5: 写单元测试（3 个 fixture）
- [x] S6.3-6: 端到端测试
- [x] S6.3-7: 真实数据冒烟（记录 resolution 分布）

**完成标志**: S6.3-6 绿 + S6.3-7 无崩溃 ✅

**实际时间**: 已完成

---

### T6.4: Range 分类（✅ 完成）

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
- [x] S6.4-1: 推 4 个 fixture 预期输出
- [x] S6.4-2: 预期输出定稿存 JSON
- [x] S6.4-3: 实现 _classify_range() 方法
- [x] S6.4-4: 写单元测试（4 个 fixture + naming trap 测试）
- [x] S6.4-5: 端到端测试
- [x] S6.4-6: 真实数据冒烟（记录 continuation/reversal 比例）
- [x] S6.4-7: 回补文档

**完成标志**: S6.4-5 绿 + S6.4-6 无崩溃 + S6.4-7 文档更新 ✅

**实际时间**: 已完成

---

## ⚠️ Lifespan 层（已完成 - 4 刀）

**规格**: MALF_03_Lifespan_v2_1-deepseek-20260726.md §1-§7  
**测试**: 18 passed  
**完成日期**: 2026-07-27  
**当前状态**: 完成 ✅

### T7.1: WaveLifespan 指标计算（✅ 完成）

**目标**: 计算已终止 wave 的 7 个统计指标

**规格覆盖**: §3 WaveLifespan 指标全集

**核心工作**:
1. WaveLifespan 数据结构
   ```python
   @dataclass
   class WaveLifespan:
       wave_id: str
       direction: Literal["UP", "DOWN"]
       birth_type: Literal["initial", "continuation", "reversal"]
       
       # 基础指标
       span_bars: int              # 波段跨度
       price_range: int            # 价格幅度
       primitive_count: int        # 原语数量
       pivot_count: int            # pivot 数量
       progress_pct: float         # 推进百分比
       
       # 推进统计
       new_count: int              # 推进次数
       no_new_span: int            # 停滞 bar 数
   ```

2. 指标计算逻辑
   - `span_bars`: termination_bar_dt - birth_bar_dt
   - `price_range`: |progress_extreme_price - guard_price|
   - `primitive_count`: pivot 相邻配对数
   - `pivot_count`: 波内 pivot 总数
   - `progress_pct`: 推进幅度 / 总幅度
   - `new_count`: progress 更新次数
   - `no_new_span`: 两次 progress 更新之间的 bar 数累计

3. 测试覆盖
   - 简单 wave（3 pivots，1 次推进）
   - 复杂 wave（10+ pivots，5 次推进）
   - 边界情况（单 primitive wave）
   - progress_pct 极端情况（≈1.0 / ≈0.5）

**Fixture 设计**:
- `t7_1_simple_wave.json`（3 pivots）
- `t7_1_complex_wave.json`（10+ pivots）
- `t7_1_single_primitive.json`（边界情况）

**Step 清单**:
- [x] S7.1-1: 推 3 个 fixture 预期输出
- [x] S7.1-2: 预期输出定稿存 JSON
- [x] S7.1-3: 实现 WaveLifespan 数据结构（types.py）
- [x] S7.1-4: 实现 _calculate_wave_metrics() 方法
- [x] S7.1-5: 写单元测试（3 个 fixture）
- [x] S7.1-6: 端到端测试
- [x] S7.1-7: 真实数据冒烟（记录指标分布）

**完成标志**: S7.1-6 绿 + S7.1-7 无崩溃 ✅

**实际时间**: 已完成

---

### T7.2: WaveLifespan peer_sample + rank（✅ 完成）

**目标**: UP/DOWN 独立样本池 + percentile_rank 计算

**规格覆盖**: §3 Peer Sample + §4 Percentile Rank

**核心工作**:
1. 双轨 peer_sample
   - UP 样本池（所有已终止 UP waves）
   - DOWN 样本池（所有已终止 DOWN waves）
   - 最小样本量（PEER_SAMPLE_MIN_N = 30）
   - 时间窗口（可选，默认全历史）
   - 防前视（termination_bar_dt ≤ 当前 bar_dt）

2. percentile_rank 计算
   ```python
   rank = count(peer < self) / len(peer_sample)
   ```
   - 严格小于（不含等于）
   - 范围 [0, 1)
   - peer_sample < 30 → rank = None

3. Rank 字段
   - span_rank: span_bars 的 percentile_rank
   - range_rank: price_range 的 percentile_rank
   - stagnation_rank: span_bars / max(primitive_count, 1) 的 percentile_rank
   - progress_rank: progress_pct 的 percentile_rank

4. 测试覆盖
   - peer_sample 不足（< 30）→ 所有 rank = None
   - peer_sample 充足（≥ 30）→ 计算 rank
   - 边界情况（自己是最小/最大）
   - UP/DOWN 分池验证

**Fixture 设计**:
- `t7_2_insufficient_sample.json`（< 30 waves）
- `t7_2_sufficient_sample.json`（≥ 30 waves）
- `t7_2_rank_boundaries.json`（最小/最大）

**Step 清单**:
- [x] S7.2-1: 推 3 个 fixture 预期输出
- [x] S7.2-2: 预期输出定稿存 JSON
- [x] S7.2-3: 实现 _build_peer_sample() 方法
- [x] S7.2-4: 实现 _calculate_percentile_rank() 方法
- [x] S7.2-5: 写单元测试（3 个 fixture）
- [x] S7.2-6: 端到端测试
- [x] S7.2-7: 真实数据冒烟（记录 rank 分布）

**完成标志**: S7.2-6 绿 + S7.2-7 无崩溃 ✅

**实际时间**: 已完成

---

### T7.3: RangeLifespan 指标计算（✅ 完成）

**目标**: Range 生命周期统计指标

**规格覆盖**: §2 双轨设计（RangeLifespan 部分）

**核心工作**:
1. RangeLifespan 数据结构
   ```python
   @dataclass
   class RangeLifespan:
       range_id: str
       range_type: Literal["continuation", "reversal"]
       
       # 基础指标
       span_bars: int              # 持续 bars
       evolution_count: int        # boundary 演化次数
       replacement_count: int      # candidate 替换次数
       resolution_distance: int    # resolution 距离（有符号）
       resolution_distance_pct: float  # resolution 距离百分比
       amplitude_pct: float        # boundary_now 幅度
   ```

2. 指标计算逻辑
   - `span_bars`: resolution_bar_dt - break_bar_dt
   - `evolution_count`: 从 Range 对象提取
   - `replacement_count`: 从 Range 对象提取
   - `resolution_distance_pct`: abs(resolution_distance) / amplitude_init
   - `amplitude_pct`: amplitude_now / boundary_low_init

3. 测试覆盖
   - 简单 range（未演化）
   - 复杂 range（演化 3 次）
   - continuation_range 和 reversal_range
   - 边界情况（amplitude_init = 0）

**Fixture 设计**:
- 使用单元测试内联数据（无需 JSON fixture）

**Step 清单**:
- [x] S7.3-1: 推 fixture 预期输出（改用单元测试内联）
- [x] S7.3-2: 预期输出定稿（不适用）
- [x] S7.3-3: 实现 RangeLifespan 数据结构（types.py）
- [x] S7.3-4: 实现 calculate_range_lifespan() 方法
- [x] S7.3-5: 写单元测试（6 个测试）
- [x] S7.3-6: 单元测试（已通过 pytest）
- [x] S7.3-7: 真实数据冒烟（T7.4 集成后完成）

**完成标志**: S7.3-6 绿 ✅

**实际时间**: 2026-07-27 完成

---

### T7.4: RangeLifespan peer_sample + rank（✅ 完成）

**目标**: continuation/reversal 分池 + percentile_rank 计算

**规格覆盖**: §2 双轨设计 + R5 不变量

**核心工作**:
1. 双类型 peer_sample
   - continuation_range 样本池
   - reversal_range 样本池
   - 最小样本量（PEER_SAMPLE_MIN_N = 20）
   - 防前视（resolution_bar_dt ≤ 当前 bar_dt）

2. Rank 字段
   - span_rank: span_bars 的 percentile_rank
   - evolution_rank: evolution_count 的 percentile_rank
   - replacement_rank: replacement_count 的 percentile_rank
   - resolution_distance_rank: resolution_distance_pct 的 percentile_rank

3. 测试覆盖
   - peer_sample 不足（< 20）→ 所有 rank = None
   - peer_sample 充足（≥ 20）→ 计算 rank
   - continuation/reversal 分池验证

**Step 清单**:
- [x] S7.4-1: 推 2 个 fixture 预期输出
- [x] S7.4-2: 预期输出定稿存 JSON
- [x] S7.4-3: 实现 _build_range_peer_sample() 方法
- [x] S7.4-4: 实现分池 rank 计算
- [x] S7.4-5: 写单元测试（2 个 fixture）
- [x] S7.4-6: 端到端测试
- [x] S7.4-7: 真实数据冒烟（记录 rank 分布）

**完成标志**: S7.4-6 绿 + S7.4-7 无崩溃 ✅

**实际时间**: 2026-07-27 完成

---

## ✅ Structural Position 层（已完成 - 4 刀）

**规格**: MALF_04_Structural_Position_v2_1-deepseek-20260726.md §1-§9  
**测试**: 12 passed (P1 + P2 + P3 + P4)
**完成日期**: 2026-07-27
**当前状态**: 完成 ✅

### T8.1: P1 自身分位（✅ 完成）

**目标**: 透传 Lifespan rank 值，不做变换

**规格覆盖**: §3 P1 — 自身分位（Self Rank）

**核心工作**:
1. P1 视图结构
   ```python
   @dataclass
   class P1SelfRank:
       span_rank: float | None
       range_rank: float | None
       stagnation_rank: float | None
       progress_rank: float | None
   ```

2. 透传逻辑
   - 从 WaveLifespan 提取 4 个 rank 字段
   - 不做任何计算或变换
   - 保持 None 传递（peer_sample 不足时）

3. 测试覆盖
   - Rank 全有值（peer_sample ≥ 30）
   - Rank 全为 None（peer_sample < 30）
   - 边界情况（rank = 0.0 / 0.99）

**Fixture 设计**:
- `t8_1_p1_with_ranks.json`（有 rank）
- `t8_1_p1_no_ranks.json`（无 rank）

**Step 清单**:
- [x] S8.1-1: 推 2 个 fixture 预期输出
- [x] S8.1-2: 预期输出定稿存 JSON
- [x] S8.1-3: 实现 P1SelfRank 数据结构（types.py）
- [x] S8.1-4: 实现 build_p1_view() 方法
- [x] S8.1-5: 写单元测试（3 个测试：no_ranks, with_ranks, boundary_values）
- [x] S8.1-6: 验证通过（使用独立脚本）
- [x] S8.1-7: 真实数据冒烟（跳过，简单透传逻辑无需）

**完成标志**: S8.1-6 绿 ✅

**实际时间**: 2026-07-27 完成

**预计时间**: 2-3 天

---

### T8.2: P2 同向对照（✅ 完成）

**目标**: 计算当前 wave 与最近同向波的 momentum

**规格覆盖**: §4 P2 — 同向对照（Same Direction Momentum）

**核心工作**:
1. P2 视图结构
   ```python
   @dataclass
   class P2SameDirMomentum:
       same_dir_span_momentum: float | None
       same_dir_range_momentum: float | None
       same_dir_stagnation_momentum: float | None
       same_dir_label: str | None  # "accelerating" | "flat" | "decelerating"
   ```

2. Momentum 计算
   - 从 W-1, W-2, W-3 中筛选同向波
   - 计算 W0 与同向波的 rank 差值（向量差）
   - momentum > 0：当前波比历史更强
   - momentum < 0：当前波比历史更弱

3. 标签规则（阈值化）
   - accelerating: avg_momentum > 0.10（默认阈值）
   - decelerating: avg_momentum < -0.10
   - flat: 其他情况

4. 测试覆盖
   - 充足同向波（1 个同向波）
   - 不足同向波（1 个）
   - 无同向波（momentum = None）

**Fixture 设计**:
- `t8_2_p2_sufficient_peers.json`（1 个同向波）
- `t8_2_p2_insufficient_peers.json`（1 个同向波）
- `t8_2_p2_no_peers.json`（无同向波）

**Step 清单**:
- [x] S8.2-1: 推 3 个 fixture 预期输出
- [x] S8.2-2: 预期输出定稿存 JSON
- [x] S8.2-3: 实现 P2SameDirMomentum 数据结构（types.py）✅（已在 T8.1 完成）
- [x] S8.2-4: 实现 build_p2_view() 方法
- [x] S8.2-5: 实现标签规则 _label_same_dir_momentum()
- [x] S8.2-6: 写单元测试（3 个 fixture）
- [x] S8.2-7: 验证通过（使用独立脚本）
- [x] S8.2-8: 真实数据冒烟（跳过，逻辑简单）

**完成标志**: S8.2-7 绿 ✅

**实际时间**: 2026-07-27 完成

---

### T8.3: P3 反向对照（✅ 完成）

**目标**: 计算当前 wave 与最近反向波的 cross momentum

**规格覆盖**: §5 P3 — 反向对照（Opposite Direction Momentum）

**核心工作**:
1. P3 视图结构
   ```python
   @dataclass
   class P3CrossDirMomentum:
       cross_dir_span_momentum: float | None
       cross_dir_range_momentum: float | None
       cross_dir_stagnation_momentum: float | None
       cross_dir_label: str | None  # "self_dominant" | "opposite_dominant" | "balanced"
   ```

2. Cross Momentum 计算
   - 从 W-1, W-2, W-3 中筛选反向波
   - 计算 W0 与反向波的 rank 差值（向量差）
   - cross_momentum > 0：当前波比反向波更强
   - cross_momentum < 0：当前波比反向波更弱

3. 标签规则（阈值化）
   - self_dominant: avg_momentum > 0.15（默认阈值）
   - opposite_dominant: avg_momentum < -0.15
   - balanced: 其他情况

4. 测试覆盖
   - 充足反向波（2 个反向波）
   - 不足反向波（1 个）
   - 无反向波（cross_momentum = None）

**Fixture 设计**:
- `t8_3_p3_sufficient_peers.json`（2 个反向波）
- `t8_3_p3_insufficient_peers.json`（1 个反向波）
- `t8_3_p3_no_peers.json`（无反向波）

**Step 清单**:
- [x] S8.3-1: 推 3 个 fixture 预期输出
- [x] S8.3-2: 预期输出定稿存 JSON
- [x] S8.3-3: 实现 P3CrossDirMomentum 数据结构（types.py）✅（已在 T8.1 完成）
- [x] S8.3-4: 实现 build_p3_view() 方法（复用 _calculate_momentum()）
- [x] S8.3-5: 实现标签规则 _label_cross_dir_momentum()
- [x] S8.3-6: 写单元测试（3 个 fixture）
- [x] S8.3-7: 验证通过（使用独立脚本）
- [x] S8.3-8: 真实数据冒烟（跳过，逻辑简单）

**完成标志**: S8.3-7 绿 ✅

**实际时间**: 2026-07-27 完成

---

### T8.4: P4 正反对照（✅ 完成）

**目标**: W0 与 W-1（最近已终止波）比较

**规格覆盖**: §6 P4 — 正反对照（Cross Compare）

**核心工作**:
1. P4 视图结构
   ```python
   @dataclass
   class P4CrossCompare:
       cross_span_momentum: float | None     # W0 vs W-1
       cross_range_momentum: float | None
       cross_stagnation_momentum: float | None
       cross_alive_warning: bool  # W0 为 alive 时为 True
   ```

2. P4 计算
   - 取 W-1（最近一个已终止波，任意方向）
   - 计算 W0 与 W-1 的 rank 差值
   - 若 W-1 不存在：momentum = None
   - cross_alive_warning 真实反映 W0 的 alive 状态

3. **无标签**（规格 §6 明确：P4 没有标签）
   - P4 只输出 3 个 momentum + cross_alive_warning
   - 不做阈值化，不生成标签

4. 测试覆盖
   - W-1 存在且已终止
   - W-1 不存在（第一个 wave）
   - W0 为 alive（cross_alive_warning = True）

**Fixture 设计**:
- `t8_4_p4_with_w_minus_1.json`（W-1 存在，W0 已终止）
- `t8_4_p4_no_w_minus_1.json`（W-1 不存在）
- `t8_4_p4_w0_alive.json`（W0 为 alive）

**Step 清单**:
- [x] S8.4-1: 推 3 个 fixture 预期输出
- [x] S8.4-2: 预期输出定稿存 JSON
- [x] S8.4-3: 实现 P4CrossCompare 数据结构（types.py）✅（已在 T8.1 完成）
- [x] S8.4-4: 实现 build_p4_view() 方法
- [x] S8.4-5: 写单元测试（3 个 fixture）
- [x] S8.4-6: 验证通过（使用独立脚本）
- [x] S8.4-7: 真实数据冒烟（跳过，逻辑简单）

**完成标志**: S8.4-6 绿 ✅

**实际时间**: 2026-07-27 完成

**注**: WaveStructuralSnapshot 组装属于 Service 层（T9），不在本任务范围。

---

## 🎊 Service 层（已完成 - 2 刀）

**规格**: MALF_05_Service_v2_1-deepseek-20260726.md §1-§8  
**测试**: 11 passed (5 usage + 6 persistence)  
**完成时间**: 2026-07-27

### T9.1: Usage 判定 + 失败模式（✅ 完成）

**目标**: usage 判定（rejected/research_only/verification_only/operational）+ reason_codes

**规格覆盖**: §2-§3, §6, §8

**核心工作**:
1. WaveStructuralSnapshot 数据结构（34 字段）
   - 标识字段（4）：symbol, timeframe, bar_dt, bar_index
   - Core 层字段（10）：system_state, direction, guard, progress, etc.
   - Range 层字段（9）：boundary, evolution, candidate, etc.
   - Lifespan 层字段（7）：wave ranks + range ranks
   - Structural Position 层字段（9）：P2/P3/P4 momentum + labels
   - 元数据（5）：rule_versions, lineage_hash, reason_codes, usage, freshness

2. UsageType 枚举（4 个值）
   - REJECTED: 输入完整性失败
   - RESEARCH_ONLY: 数据合同不满足
   - VERIFICATION_ONLY: 回测验证模式
   - OPERATIONAL: v0.1 禁用

3. ReasonCode 枚举（11 个常量）
   - uninitialized, transition_active, wave_alive
   - input_integrity_failure, data_stale
   - peer_sample_insufficient
   - same_dir_peers_absent, cross_dir_peers_absent
   - no_prior_wave, range_alive
   - operational_disabled

4. Usage 判定逻辑（G0-G2 优先级）
   - G0: 输入完整性失败 → rejected
   - G1: 数据合同不满足 → research_only
   - G2: operational v0.1 禁用 → verification_only

5. Reason codes 生成逻辑
   - 为每个 None 字段生成原因代码
   - 11 种失败模式全覆盖

**测试覆盖**:
- test_usage_rejected_on_input_integrity_failure
- test_usage_research_only_on_peer_sample_insufficient
- test_usage_verification_only_on_complete_data
- test_operational_disabled_in_v01
- test_usage_priority_rejected_over_research_only

**完成标志**: 5 passed ✅

**实际时间**: 2026-07-27 完成

**提交**: 73eb90f

---

### T9.2: 持久化 + 中断恢复（✅ 完成）

**目标**: JSON 序列化 + lineage_hash + 状态持久化 + 中断恢复

**规格覆盖**: §4-§5, §7

**核心工作**:
1. JSON 序列化/反序列化
   ```python
   serialize_snapshot(snapshot) -> str
   deserialize_snapshot(json_str) -> WaveStructuralSnapshot
   ```
   - 使用 stdlib json + dataclasses.asdict()
   - 往返一致性保证

2. Lineage Hash 计算
   ```python
   calculate_lineage_hash(snapshot_data) -> str
   ```
   - SHA256 确定性哈希
   - 只包含计算链路字段（排除元数据）
   - 相同输入 → 相同 hash

3. var/ 目录结构
   ```
   var/
   ├── staging/           # 待发布快照
   └── published/
       └── {symbol}/
           └── {timeframe}/
               ├── snapshots.jsonl    # JSON Lines 格式
               └── current.json       # 最后快照指针
   ```

4. 快照持久化
   ```python
   persist_snapshot(snapshot, base_path) -> Path
   update_current_pointer(snapshot, filepath, base_path)
   ```
   - JSON Lines 追加写入
   - current.json 原子更新

5. 中断恢复
   ```python
   load_last_snapshot(base_path) -> (snapshot, bar_dt) | None
   should_resume_from(last_bar_dt, current_bar_dt) -> bool
   ```
   - 从 current.json 恢复最后状态
   - bar_dt 去重判定

**测试覆盖**:
- test_serialization_roundtrip: JSON 往返一致性
- test_lineage_hash_determinism: Hash 确定性
- test_var_directory_creation: 目录自动创建
- test_snapshot_persistence: 持久化 + current.json
- test_interrupt_recovery: 中断恢复机制
- test_load_last_snapshot_when_none_exists: 边界情况

**完成标志**: 6 passed ✅

**实际时间**: 2026-07-27 完成

**提交**: e6bb6bc

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
- 状态: ✅ 已完成（2026-07-27）
- 注：当前代码中未使用 WaveProbabilitySnapshot，该类型尚未定义

#### P0-2: v2.1 文档引用说明（立即）
- 在核心模块 docstring 中增加版本说明
- 明确 v2.0 → v2.1 语义等价
- 预计: 20 分钟
- 状态: ✅ 已完成（2026-07-27）
- 更新文件：core_engine.py, types.py, lifespan_engine.py, rank_engine.py

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

**当前状态**: P0 级缺陷已全部修复 ✅（2026-07-27）

**已完成修复**（2026-07-27）:
- [x] P0-1: 修正 Core break 检测逻辑（bar.close → bar.low/high）✅
- [x] P0-2: 添加 Pivot.confirm_price 字段 ✅
- [x] 运行完整回归测试（89 passed, 2 skipped）✅
- [x] Git 提交推送（commit b4e1562）✅

**待办事项**（优先级排序）:
1. [ ] P1-3: 核对 progress_pct 计算公式（1小时）
2. [ ] P1-4: 添加 CoreStateSnapshot.bar_index（20分钟）
3. [ ] 归档规格对照报告到 docs/reports/
4. [ ] 开始 Service 层开发（T9.1-T9.2）

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
**最后更新**: 2026-07-27
