# malf-engine 项目地图 🗺️

**目的**: 一张图看懂项目全貌，知道现在在哪里，下一步做什么。

**最后更新**: 2026-07-26

---

## 🎯 项目目标

**交付物**: MALF v2.1 结构计算完整引擎  
**输入**: OHLC 价格数据  
**输出**: `WaveStructuralSnapshot`（包含 Core + Range + Lifespan + Structural Position + Service 5 层）  
**约束**: 确定性、单遍、零外部依赖

---

## 📍 当前位置（严重误判已修正）

```
进度: ████░░░░░░░░░░░░░░░░ 20% 完成（仅 Core 层）

已完成: Core 层（T1-T5 + C-07）
待完成: Range、Lifespan、Structural Position、Service
状态: ⚠️ 仅完成 1/5 层，核心工作尚未开始
测试: 58 passed（全部是 Core 层测试）
```

**之前的错误判断**: 我错误地认为 Range 层已完成，导致声称"80% 完成、0 刀剩余、v1.0 可发布"。这是严重错误。

**真实情况**: 只完成了 Core 层（1/5），还需要 4 层（Range、Lifespan、Structural Position、Service）。

---

## 🛤️ 整体路线图（MALF v2.1 完整规格）

### ✅ 已完成的刀（1/5 层）

| 刀数 | 层 | 核心功能 | 测试 | 完成日期 |
|------|-----|---------|------|---------|
| **T1** | Core | UP 初始化（H0→L1→H2） | 8 | 2026-07-25 |
| **T2** | Core | DOWN 初始化（L0→H1→L2） | +6 | 2026-07-25 |
| **T3** | Core | Guard Break（同向突破） | +4 | 2026-07-26 |
| **T4** | Core | Candidate 演化（Flip-flop） | +6 | 2026-07-26 |
| **T5** | Core | Guard/Progress 更新 | +5 | 2026-07-26 |
| **C-07** | Core | Pivot 替换（H0/L0/L1/H1） | +4 | 2026-07-26 |

**Core 层小计**: 47 + 4 + 7 = **58 passed** ✅

---

### ⏸️ 待完成的刀（4/5 层 - 核心工作）

| 刀数 | 层 | 核心功能 | 预计时间 | 优先级 |
|------|-----|---------|---------|--------|
| **T6** | **Range** | Range 诞生/boundary 演化/resolution 判定 | 3-5天 | **P0 - 必做** |
| **T7** | **Lifespan** | 双轨 peer_sample + percentile_rank 计算 | 3-5天 | **P0 - 必做** |
| **T8** | **Structural Position** | 4 视图（rank/momentum/cross_compare）+ 标签规则 | 3-5天 | **P0 - 必做** |
| **T9** | **Service** | usage 判定 + 持久化 + 中断恢复 + 失败模式 | 2-3天 | **P0 - 必做** |

**预计总时间**: **11-18 天**（全职开发）

**注意**: 这些不是"可选增强"，而是 **v2.1 规格的核心组成部分**。

---

## 📚 5 层架构说明

根据 MALF v2.1 Definitive 权威规格，完整引擎包含 5 层：

### 第 1 层：Core（✅ 已完成）
- **职责**: 结构状态机（UP/DOWN/TRANSITION）
- **输入**: OHLC bar
- **输出**: CoreState（wave、guard、progress、candidate）
- **状态**: ✅ 100% 完成，58 测试通过

### 第 2 层：Range（⏸ 待实现）
- **职责**: 震荡区间识别（一等公民对象）
- **触发**: Guard break
- **核心逻辑**: boundary 演化、resolution 判定（T6 定理）
- **状态**: ⏸ 0% 完成

### 第 3 层：Lifespan（⏸ 待实现）
- **职责**: 波段生命周期排名
- **核心逻辑**: 双轨 peer_sample（UP/DOWN 独立）、percentile_rank 计算
- **输出**: rank 值（0-100）
- **状态**: ⏸ 0% 完成

### 第 4 层：Structural Position（⏸ 待实现）
- **职责**: 结构位置视图（原名 Probability 层）
- **4 视图**: up_rank、down_rank、momentum、cross_compare
- **输出**: 标签（strong_up、weak_down、choppy 等）
- **状态**: ⏸ 0% 完成

### 第 5 层：Service（⚠️ 部分完成）
- **职责**: 对外接口、usage 判定、失败模式处理
- **核心**: WaveStructuralSnapshot（整合 5 层）、S6 铁律
- **当前**: 仅有 snapshot 结构定义（~20%）
- **状态**: ⚠️ 待完成 usage/持久化/中断恢复

---

## 💡 关键认知纠正

### ❌ 之前的错误判断
- "Core + Range 层已完成" → **错误**，Range 未实现
- "80% 完成，v1.0 可发布" → **错误**，只完成 20%
- "0 刀剩余" → **错误**，还需 4 个大刀
- "下一步是工程化增强（序列化/CI/CD）" → **错误**，下一步是实现剩余 4 层

### ✅ 正确的判断
- **已完成**: Core 层（1/5）
- **完成度**: 20%
- **待完成**: Range + Lifespan + Structural Position + Service（4/5 层）
- **预计时间**: 11-18 天全职开发
- **下一步**: T6 Range 层实现（3-5 天）

---

## 🚀 下一步行动

### 立即任务：T6 Range 层（P0）

**时间**: 3-5 天  
**规格**: MALF_02_Range_v2_1-deepseek-20260726.md

**核心工作**：
1. Range 对象结构（boundary_init、boundary_now）
2. Range 诞生逻辑（guard break 触发）
3. Boundary 演化（新 pivot 更新 boundary_now）
4. Resolution 判定（T6 定理：pivot 超越 old wave extremum）
5. Continuation/Reversal 分类
6. 测试覆盖（预计 15-20 个测试）

**验收标准**：
- Range 诞生/演化/resolution 全部测试通过
- 真实数据验证（sh600000, 200 bars）
- 边界情况覆盖（多次 resolution、嵌套 range）

---

## 📚 核心文档

### 权威规格（必读）
1. **MALF v2.1 Definitive** - `I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`
   - AUTHORITY.md - 权威声明
   - MALF_00_Bridge_v2_1-deepseek-20260726.md - 变更说明
   - MALF_01_Core_v2_1-deepseek-20260726.md - Core 层规格
   - MALF_02_Range_v2_1-deepseek-20260726.md - Range 层规格 ⭐ **下一步必读**
   - MALF_03_Lifespan_v2_1-deepseek-20260726.md - Lifespan 层规格
   - MALF_04_Structural_Position_v2_1-deepseek-20260726.md - Structural Position 层规格
   - MALF_05_Service_v2_1-deepseek-20260726.md - Service 层规格

### 项目文档（辅助）
1. **本文档** (PROJECT-MAP.md) - 项目地图 ⭐
2. dev/BUILD-PLAN.md - 执行计划（需更新）
3. spec/BUILD-CONTRACT.md - 建造合同（需更新范围）

---

## 🧭 快速导航

| 需求 | 看这个 |
|------|--------|
| 了解项目全貌 | **本文档** (PROJECT-MAP.md) ⭐ |
| 查看权威规格 | MALF v2.1 Definitive 目录 |
| 查看 Core 层实现 | src/malf/ |
| 运行测试 | `/d/miniconda/py310/python.exe -m pytest` |
| 查看历史任务 | docs/archive/tasks/ |

---

## 🔧 开发命令速查

```bash
# 运行所有测试
/d/miniconda/py310/python.exe -m pytest

# 运行特定层测试
/d/miniconda/py310/python.exe -m pytest tests/test_core*.py

# 详细输出
/d/miniconda/py310/python.exe -m pytest -v

# 真实数据验证
/d/miniconda/py310/python.exe tests/smoke/test_real_tdx_data.py
```

---

## ❓ 常见问题

### Q: 为什么之前说"已完成 80%"？
**A**: 我的严重误判。我错误地认为 T6 Range 层已实现（因为有 7 个 Range 测试通过），但实际上这些测试是早期实验，不符合 v2.1 规格。实际完成度是 20%（1/5 层）。

### Q: 还需要多少刀才能完成？
**A**: **4 刀**（T6 Range + T7 Lifespan + T8 Structural Position + T9 Service），预计 11-18 天全职开发。

### Q: T1-T5 后为什么是 C-07，然后是 T6？
**A**: 
- **T1-T5**: Core 层的 5 个刀（基础状态机）
- **C-07**: 规格补丁（补充 Pivot 替换逻辑）
- **T6-T9**: 后续 4 层的实现（Range/Lifespan/Structural Position/Service）

### Q: 下一步做什么？
**A**: **T6 Range 层**（3-5 天），这是 v2.1 规格的第 2 层，必须完成才能继续后续层。

### Q: 什么时候可以发布 v1.0？
**A**: **完成全部 5 层后**（预计 11-18 天后）。v1.0 的最小标准是 Core + Range + Lifespan + Structural Position + Service 全部实现并测试通过。

---

## 📝 版本规划（修正）

### v1.0（目标版本 - 未完成）
- ✅ Core 层完整
- ⏸ Range 层完整
- ⏸ Lifespan 层完整
- ⏸ Structural Position 层完整
- ⏸ Service 层完整
- ⏸ 5 层集成测试通过
- ⏸ 真实数据验证通过

**预计完成**: 11-18 天后

### v1.1（工程化增强 - v1.0 之后）
- ⬜ 序列化支持
- ⬜ CI/CD
- ⬜ PyPI 发布

---

## 🎯 最重要的信息

```
❌ 之前错误: "80% 完成，v1.0 可发布"
✅ 真实情况: 20% 完成（仅 Core 层）

✅ Core 层 100% 完成（58 测试通过）
⏸ Range 层 0% - 待 T6（3-5天）
⏸ Lifespan 层 0% - 待 T7（3-5天）
⏸ Structural Position 层 0% - 待 T8（3-5天）
⚠️ Service 层 20% - 待 T9（2-3天）

📋 下一步：T6 Range 层实现（必做，非可选）
📖 必读规格：MALF_02_Range_v2_1-deepseek-20260726.md
⏱️ 预计 v1.0 完成：11-18 天后
```

---

**维护**: 每完成一个大任务更新本文档  
**负责人**: 项目所有者  
**最后修正**: 2026-07-26（承认错误判断，重新评估进度）
