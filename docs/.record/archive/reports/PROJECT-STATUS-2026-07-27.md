# malf-engine 项目状态报告

**报告日期**: 2026-07-27  
**报告人**: Claude (AI Assistant)

---

## 📊 总体进度

**项目目标**: MALF v2.1 完整引擎（5 层架构）  
**总体进度**: **8/20 刀完成（40%）**

---

## ✅ 已完成层（3 层）

### 1️⃣ Core 层（100% 完成）✅

**完成时间**: 2026-07-26  
**测试状态**: 58 passed, 1 skipped  
**真实数据验证**: ✅ sh600000 200 bars 通过

**完成内容**:
- ✅ T1: UP 初始化（H0→L1→H2）
- ✅ T2: DOWN 初始化（L0→H1→L2）
- ✅ T3: Guard Break（同向突破）
- ✅ T4: Candidate 演化（transition 期间）
- ✅ T5: Guard/Progress 更新
- ✅ C-07: 早期 Pivot 替换（H0/L0/L1/H1）

**代码文件**:
- `src/malf/pivot_detection.py` ✅
- `src/malf/initialization.py` ✅
- `src/malf/core_engine.py` ✅

**测试文件**:
- `tests/test_pivot_detection.py` ✅
- `tests/test_initialization.py` ✅
- `tests/test_core_uninitialized_to_up_alive.py` ✅
- `tests/test_t2_down_initialization.py` ✅
- `tests/test_guard_break.py` ✅
- `tests/test_transition_candidate.py` ✅
- `tests/test_guard_update.py` ✅
- `tests/test_progress_update.py` ✅
- `tests/test_c07_replacement.py` ✅
- `tests/test_bar_count.py` ✅
- `tests/test_replay_determinism.py` ✅

---

### 2️⃣ Range 层（100% 完成）✅

**完成时间**: 2026-07-26  
**测试状态**: 6 synthetic + 1 real data, all passed  
**真实数据验证**: ✅ sh600000 200 bars，3 Ranges，R2 不变量全部通过

**完成内容**:
- ✅ T6.1: Range 诞生（guard break 触发）
- ✅ T6.2: Boundary 演化（双边界系统）
- ✅ T6.3: Resolution 判定（T6 定理）
- ✅ T6.4: Range 分类（continuation/reversal）

**核心设计**:
- 两层边界模型：`boundary_init`（冻结）+ `boundary_now`（演化）
- Evolution 计数（R2 不变量）
- Resolution distance 计算（有符号整数）
- Continuation/Reversal 分类（避免命名陷阱）

**代码实现**:
- Range 字段已集成到 `CoreStateSnapshot`（types.py L133-146）
- Range 逻辑已集成到 `core_engine.py`（状态机内）
- `RangeSnapshot` 数据结构已定义（types.py L179-233）

**测试文件**:
- `tests/test_range_layer.py` ✅ (6 tests)
  - R1: Continuation (下 break → 下 resolve)
  - R2: Reversal (下 break → 上 resolve)
  - R3: Continuation (上 break → 上 resolve)
  - R4: Reversal (上 break → 下 resolve)
  - R5: Multi-evolution
  - R6: Long-lived unresolved
- `tests/test_real_data_smoke.py::test_sh600000_range_layer_smoke` ✅

---

### 3️⃣ Lifespan 层（部分完成，约 50%）⚠️

**当前状态**: T7.1 和 T7.2 已实现，T7.3 和 T7.4 待做

**已完成**:
- ✅ T7.1: WaveLifespan 指标计算
  - `src/malf/lifespan_engine.py` ✅
  - 7 个统计指标：span_bars, price_range, primitive_count, pivot_count, progress_pct, new_count, no_new_span
  - `tests/test_wave_lifespan.py` ✅
  
- ✅ T7.2: WaveLifespan peer_sample + rank
  - `src/malf/rank_engine.py` ✅
  - Percentile rank 计算（严格 < 公式）
  - UP/DOWN 分池逻辑
  - 样本不足退化（N < 30）
  - `tests/test_percentile_rank.py` ✅

**待完成**:
- ⏸ T7.3: RangeLifespan 指标计算（预计 2-3 天）
- ⏸ T7.4: RangeLifespan peer_sample + rank（预计 2-3 天）

---

## ⏸ 待完成层（2 层）

### 4️⃣ Structural Position 层（未开始）

**预计时间**: 8-12 天  
**任务清单**:
- ⏸ T8.1: P1 自身分位（2-3 天）
- ⏸ T8.2: P2 同向对照（2-3 天）
- ⏸ T8.3: P3 反向对照（2-3 天）
- ⏸ T8.4: P4 正反对照 + 最终集成（2-3 天）

---

### 5️⃣ Service 层（未开始）

**预计时间**: 3-5 天  
**任务清单**:
- ⏸ T9.1: Usage 判定 + 失败模式（1-2 天）
- ⏸ T9.2: 持久化 + 中断恢复（2-3 天）

---

## 🔍 文档一致性问题

**发现问题**: BUILD-PLAN.md 存在内部矛盾

### 矛盾点 1: Range 层状态
- **第 27 行**（表格）: `| **Range** | ... | ✅ 完成 | 6 测试通过 + 真实数据验证 |`
- **第 129 行**（详细部分）: `## ⏸ Range 层（待做 - 4 刀）` + `**当前状态**: 未开始`

### 矛盾点 2: Lifespan 层状态
- **第 28 行**（表格）: `| **Lifespan** | ... | ⏸ 进行中 | 4 刀（T7.1-T7.4） |`
- **第 322 行**（详细部分）: `## ⏸ Lifespan 层（待做 - 4 刀）` + `**当前状态**: 未开始`

### 实际状态（根据代码 + 测试）:
- ✅ Range 层：**100% 完成**（6 测试全部通过，真实数据验证通过）
- ⚠️ Lifespan 层：**50% 完成**（T7.1 + T7.2 完成，T7.3 + T7.4 待做）

---

## 🎯 下一步任务（明确）

### 立即任务: T7.3 RangeLifespan 指标计算

**目标**: 计算已终止 Range 的生命周期统计指标

**预计时间**: 2-3 天

**Step 清单**:
- [ ] S7.3-1: 推 2 个 fixture 预期输出
- [ ] S7.3-2: 预期输出定稿存 JSON
- [ ] S7.3-3: 实现 RangeLifespan 数据结构（types.py 已有部分定义）
- [ ] S7.3-4: 实现 `_calculate_range_metrics()` 方法
- [ ] S7.3-5: 写单元测试（2 个 fixture）
- [ ] S7.3-6: 端到端测试
- [ ] S7.3-7: 真实数据冒烟（记录指标分布）

**规格覆盖**: MALF_03_Lifespan_v2_1-deepseek-20260726.md §2 RangeLifespan

**核心指标**:
- `span_bars`: resolution_bar_dt - break_bar_dt
- `evolution_count`: 从 Range 对象提取
- `replacement_count`: 从 Range 对象提取
- `resolution_distance_pct`: 从 Range 对象提取
- `amplitude_pct`: (boundary_high_now - boundary_low_now) / boundary_low_now

---

## 📋 待修复的 P0 任务

### P0-1: 类型名重命名（30 分钟）
- 当前: `WaveProbabilitySnapshot`（v2.0）
- 目标: `WaveStructuralSnapshot`（v2.1）
- 影响: types.py + core_engine.py + tests/
- 状态: ⏸ 待执行

### P0-2: v2.1 文档引用说明（20 分钟）
- 在核心模块 docstring 中增加版本说明
- 明确 v2.0 → v2.1 语义等价
- 状态: ⏸ 待执行

---

## 📈 工作量估算

| 层 | 状态 | 剩余工作量 | 备注 |
|---|------|----------|------|
| Core | ✅ 完成 | 0 天 | - |
| Range | ✅ 完成 | 0 天 | - |
| Lifespan | ⚠️ 50% | 4-6 天 | T7.3 + T7.4 |
| Structural Position | ⏸ 未开始 | 8-12 天 | T8.1-T8.4 |
| Service | ⏸ 未开始 | 3-5 天 | T9.1-T9.2 |
| **总计** | **40%** | **15-23 天** | - |

---

## 🔧 开发环境

**Python 版本**: 3.10.19  
**测试框架**: pytest 9.1.1  
**测试命令**: 
```bash
# Windows（从项目根目录）
D:\miniconda\py310\python.exe -m pytest

# 详细输出
D:\miniconda\py310\python.exe -m pytest -v

# 运行特定测试
D:\miniconda\py310\python.exe -m pytest tests/test_range_layer.py
```

---

## 📝 建议行动

### 1. 立即更新 BUILD-PLAN.md

**修正矛盾**:
- 第 27 行：确认 Range 层 ✅ 完成
- 第 28 行：更新 Lifespan 层为 "⚠️ 50% 完成（T7.1-T7.2 ✅）"
- 第 129-321 行：Range 层章节标题改为 `## ✅ Range 层（已完成 - 6 刀）`
- 第 322-537 行：Lifespan 层章节更新进度，T7.1-T7.2 标记为 ✅

### 2. 执行 P0 任务（可选，不阻塞开发）

在开始 T7.3 前：
- P0-2: 补充 v2.1 文档引用说明（20 分钟）
- P0-1: 类型名重命名（30 分钟）

### 3. 开始 T7.3 实施

按照 BUILD-PLAN.md 中的 Step 清单执行 T7.3。

---

## ✅ 结论

**项目健康度**: 良好 ✅  
**实际进度**: 40%（8/20 刀）  
**文档问题**: 存在矛盾，需要更新 BUILD-PLAN.md  
**下一步**: T7.3 RangeLifespan 指标计算（预计 2-3 天）

**代码质量**:
- ✅ 测试覆盖充分（58 passed, 1 skipped）
- ✅ 真实数据验证通过
- ✅ TDD 工作流严格执行
- ✅ 零外部依赖（纯标准库）
- ✅ Replay 确定性保证

**当前阻塞**: 无阻塞，可以直接开始 T7.3
