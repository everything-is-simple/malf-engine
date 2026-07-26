# MALF v2.1 Definitive — malf-engine 权威指导文档

> **发布日期：** 2026-07-26  
> **状态：** 权威定稿  
> **起草者：** DeepSeek  
> **审核者：** Claude (Anthropic)  
> **认定者：** 东西南北中（2026-07-26 已签署）

---

## 文档定位

**本文档是 malf-engine 项目的唯一权威规格指导。**

- **权威定义文档：** `I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`
- **本地引用副本：** malf-engine 项目通过本文档引用权威定义，不复制全文（避免两处真相源）
- **与 v2.0 的关系：** v2.1 与 v2.0 语义等价，是"清晰表达版本"，不是"新版本"

---

## 权威文件清单

| 文件 | 层 | 用途 | SHA-256 |
|------|-----|------|---------|
| MALF_00_Bridge_v2_1-deepseek-20260726.md | Bridge | 变更说明与入口 | 3F81C52... |
| MALF_01_Core_v2_1-deepseek-20260726.md | Core | 结构状态机（D1-D18/T1-T10/O1-O8） | B6F915C... |
| MALF_02_Range_v2_1-deepseek-20260726.md | Range | 震荡区间一等公民 | AB2F60C... |
| MALF_03_Lifespan_v2_1-deepseek-20260726.md | Lifespan | 双轨户口与排名 | B5A9072... |
| MALF_04_Structural_Position_v2_1-deepseek-20260726.md | Structural Position | 结构位置（原Probability） | D589968... |
| MALF_05_Service_v2_1-deepseek-20260726.md | Service | 对外接口与铁律 | 8752D31... |
| AUTHORITY.md | - | 权威声明 | - |

**完整哈希见：** `MANIFEST-deepseek-20260726.json`

---

## v2.0 → v2.1 关键变更

### 1. 命名修正（最重要）

| v2.0 | v2.1 | 理由 |
|------|------|------|
| Probability 层 | Structural Position 层 | 不输出概率，输出结构位置 |
| WaveProbabilitySnapshot | WaveStructuralSnapshot | 快照类型名与层名对齐 |

**对 malf-engine 的影响：**
- 类型名需要重命名（可在第六刀统一处理）
- 代码逻辑零变更

### 2. 补丁回写（21条）

IMPLEMENTATION-CONTRACT-PATCH 的第 1-3 层（21条）已全部回写入 v2.1 正文，包括：
- percentile_rank 公式明确
- wave_id 生成规则明确
- wave_start_price 取值明确
- resolution_distance_pct 公式明确
- 等等...

**对 malf-engine 的影响：**
- IMPLEMENTATION-CONTRACT-PATCH 仍保留作为历史记录
- 新的实现直接参考 v2.1 正文

### 3. 歧义闭合（3处）

- R5 resolution_distance_pct 公式：`|confirmation_pivot.extreme_price - range.birth_break_price| / |boundary_high_init - boundary_low_init|`
- R6 continuation_range 命名陷阱：延续的是 break 方向，不是旧 wave 方向
- 两层边界明确：Core 用 init，Range 统计用 now

**对 malf-engine 的影响：**
- Range 层实现时参考 v2.1 §2 Range 的完整说明

### 4. 补充完整（Claude审查14条）

- Structural Position 补充完整计算公式（§2-§6）
- Service 补充失败模式章节（§8，8种场景）
- 各层补充测试覆盖要求（§N）
- Bridge 补充实现状态对照（§6）、性能基准（§7）、版本治理（§8）

**对 malf-engine 的影响：**
- 实现时参考更详细的边界情况处理
- 测试覆盖有明确的最低要求

---

## 当前实施状态（基于 BUILD-PLAN.md）

| 刀数 | 目标 | v2.1 章节 | 状态 | 测试 |
|------|------|-----------|------|------|
| 第一刀 | uninitialized → up_alive | Core §2-§4 | ✅ 完成 | 16 passed |
| 第二刀 | uninitialized → down_alive | Core §2-§4 | ✅ 完成 | 集成入第一刀 |
| 第三刀 | Same-direction Break | Core §5-§7 | ✅ 完成 | 31 passed |
| 第四刀 | Transition Candidate 演化 | Core §7-§9 | ✅ 完成 | 31 passed |
| 第五刀 | Guard 更新 + bar_count + Replay | Core §2.9/O8 | ✅ 完成 | 47 passed, 1 skipped |
| **第六刀** | **Range 层** | **Range §1-§8** | **⏸ 待开始** | **-** |
| 第七刀 | Lifespan 双轨 | Lifespan §1-§7 | ⏸ 未开始 | - |
| 第八刀 | Structural Position | Structural Position §1-§9 | ⏸ 未开始 | - |
| 第九刀 | Service 集成 | Service §1-§8 | ⏸ 部分（快照结构） | - |

**总结：Core 层已完成 5 刀，47 个测试通过。下一步：Range 层第六刀。**

---

## 实施指导：各层对应关系

### Core 层（已完成）

| malf-engine 模块 | v2.1 定义章节 | 对应关系 |
|-----------------|--------------|---------|
| `src/malf/types.py::CoreStateSnapshot` | Core §9 快照结构 | ✓ 完全对齐 |
| `src/malf/pivot_detection.py` | Core §2.4 Pivot 检测 | ✓ 完全对齐（fractal k=2） |
| `src/malf/initialization.py` | Core §3 初始化 | ✓ 完全对齐（D18/O6） |
| `src/malf/core_engine.py` | Core §2.6-§9 状态机 | ✓ 完全对齐（9步顺序/O2） |
| `src/malf/fingerprint.py` | Core §9 runtime_fingerprint | ✓ 完全对齐（L4-6） |

**验证状态：** 47 passed, 1 skipped（真实数据冒烟在 Windows 上 SKIPPED）

### Range 层（待实现）

| 待实现模块 | v2.1 定义章节 | 关键内容 |
|-----------|--------------|---------|
| `src/malf/range.py` | Range §1-§8 | Range 对象、boundary 演化、resolution 判定 |
| Range 测试 | Range §9 测试覆盖 | 不变量 R1-R5、边界情况、命名陷阱 |

**关键设计点（v2.1 明确）：**
1. **两层边界模型（§3）**：
   - `boundary_init`（Core 用）：从 transition 冻结，不变
   - `boundary_now`（Range 用）：基于 init 演化，用已确认 pivot

2. **Boundary 使用场景对照表（§3）**：
   | 使用场景 | 使用边界 | 理由 |
   |---------|---------|------|
   | Core new wave 判定 | init | 状态机稳定性 |
   | Range resolution_distance_pct | now | 反映真实震荡范围 |
   | Lifespan 统计 | now | 统计真实特征 |

3. **Continuation 命名陷阱（§6 警告框）**：
   - continuation_range：延续的是 **break 方向**，不是旧 wave 方向
   - 旧 UP wave 向下 break → 最终向下突破 = continuation（延续 break 的下行）
   - 旧 UP wave 向下 break → 最终向上突破 = reversal（反转 break 的下行）

### Lifespan 层（待实现）

| 待实现模块 | v2.1 定义章节 | 关键内容 |
|-----------|--------------|---------|
| `src/malf/lifespan.py` | Lifespan §1-§7 | 双轨系统、peer_sample、percentile_rank |

**关键设计点（v2.1 明确）：**
1. **双轨不混池（§2）**：
   - WaveLifespan：同方向已终止 Wave
   - RangeLifespan：continuation/reversal/unresolved 三池分开

2. **percentile_rank 边界情况（§4）**：
   ```python
   # 严格 < 比较
   rank = count(peer_value < current_value) / N
   
   # 边界情况：
   # - x = max(sample) → rank = (N-1)/N ≈ 1 但不等于 1
   # - x = min(sample) → rank = 0
   # - 多个 x_i = x → 都不计入 count
   # - 返回值范围：[0, 1)，不含 1
   ```

3. **WaveLifespan 完整指标集（§3，v2.1 恢复）**：
   - new_count（新高/低次数）
   - no_new_span（停滞 bars）
   - wave_span_total（总持续 bars）
   - progress_pct（推进百分比）
   - 以及对应的 4 个 rank

### Structural Position 层（待实现）

| 待实现模块 | v2.1 定义章节 | 关键内容 |
|-----------|--------------|---------|
| `src/malf/structural_position.py` | Structural Position §1-§9 | P1-P4 四视图计算 |

**关键设计点（v2.1 明确）：**
1. **Wave 编号约定（§2 新增）**：
   ```
   W0 = 当前 alive wave
   W-1 = 最近已终止 wave（与 W0 方向可能相同或相反）
   W-2 = 倒数第二已终止 wave
   ...
   ```

2. **P2 同向对照完整公式（§4 新增）**：
   ```python
   # 1. 选择同向波
   peer_waves = [W-1, W-2, W-3] 中方向与 W0 相同的波（取最近 1-3 个）
   
   # 2. 计算 momentum（4 维向量差）
   same_dir_span_momentum = W0.span_rank - mean(peer_waves[].span_rank)
   same_dir_update_momentum = W0.update_rank - mean(peer_waves[].update_rank)
   # ... progress, stagnation 同理
   
   # 3. 阈值判定标签
   if same_dir_span_momentum > same_dir_threshold:
       label = "accelerating"
   elif same_dir_span_momentum < -same_dir_threshold:
       label = "decelerating"
   else:
       label = "flat"
   ```

3. **不输出概率警告（每个视图开头，§3-§6 警告框）**：
   ```
   ⚠️ 本视图不输出概率或预测。momentum 和 label 是历史位置的比较标签，
   不是"未来会加速"的预测。rank 值是当前在历史中的分位，不是"胜率"。
   ```

### Service 层（部分完成）

| 模块 | v2.1 定义章节 | 状态 |
|------|--------------|------|
| `src/malf/types.py::WaveProbabilitySnapshot` | Service §2-§3 | 🔄 需重命名为 WaveStructuralSnapshot |
| Service 组装逻辑 | Service §4-§8 | ⏸ 待第九刀完成 |

**需要补充（v2.1 明确）：**
1. **usage 字段判定规则（§3）**：
   | usage | 触发条件 | 下游是否可消费 |
   |-------|---------|---------------|
   | research_only | peer_sample<30 或数据不完整 | 仅研究，不进 Signal |
   | verification_only | 回测验证模式 | 仅验证，不进实盘 |
   | rejected | 输入完整性失败 | 不可消费 |
   | operational | （v0.1 禁用） | 可进实盘 |

2. **失败模式章节（§8，8 种场景）**：
   - Core uninitialized → 全 None + reason_codes
   - Range alive 无新 wave → range_state=alive
   - 同向对照不足 → P2 全 None
   - 反向对照不足 → P3 全 None
   - W-1 不存在 → P4 全 None
   - peer_sample<30 → rank 字段 None
   - 等等...

---

## 需要修订的地方（按优先级）

### P0：类型名重命名（第六刀统一处理）

**问题：** 当前代码使用 v2.0 命名
```python
# src/malf/types.py
@dataclass
class WaveProbabilitySnapshot:  # ← 需要改名
    ...
```

**修订：** 第六刀开始前统一重命名
```python
@dataclass
class WaveStructuralSnapshot:  # ✓ v2.1 命名
    ...
```

**影响范围：**
- `src/malf/types.py`：类型定义
- `src/malf/core_engine.py`：类型引用
- `tests/` 所有测试文件：类型引用
- `docs/`：文档引用

**执行时机：** 第六刀开工前（避免中途改名影响调试）

### P1：文档引用更新（立即执行）

**问题：** 当前文档引用 v2.0
- README.md 第 11 行：`../../asteria-riskbench/new-docs/MALF_v2.0_引擎规格_定稿.md`
- BUILD-CONTRACT.md 第 6 行：同上

**修订：** 更新引用到 v2.1
```markdown
# README.md / BUILD-CONTRACT.md
规格权威：`I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`
权威声明：参见 `docs/MALF_V2_1_AUTHORITY_REFERENCE.md`
```

### P2：IMPLEMENTATION-CONTRACT-PATCH 标注（立即执行）

**问题：** IMPLEMENTATION-CONTRACT-PATCH 的第 1-3 层已回写入 v2.1，但文档未标注

**修订：** 在文档开头增加标注
```markdown
# MALF v2.0 引擎实现合同 / 勘误补丁

> **重要更新（2026-07-26）**：本补丁的第 1-3 层（21 条）已全部回写入 MALF v2.1 Definitive 正文。
> **新实现请直接参考 v2.1 正文**，本文档保留作为历史记录和第 4A/4B 层立法参考。
> 
> v2.1 权威文档：`I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`
```

### P3：Range 层实施准备文档（第六刀前）

**需要创建：** `docs/T6-RANGE-IMPLEMENTATION-GUIDE.md`

**内容：**
1. Range §1-§8 的关键设计点摘要
2. 两层边界模型的实现策略
3. Continuation 命名陷阱的测试覆盖
4. Fixture 设计要点（基于 §9 测试覆盖要求）

### P4：性能基准文档（长期）

**需要创建：** `docs/PERFORMANCE-BENCHMARKS.md`

**内容：** 基于 v2.1 Bridge §7
- 单 symbol 单 bar 处理时间：< 10ms
- 内存消耗：peer_sample N=1000 时约 XXX MB
- 存储增长：每 symbol 每年约 XXX MB

---

## 测试覆盖对照（v2.1 新增要求）

| 层 | v2.1 要求（§N 测试覆盖） | 当前状态 | 缺口 |
|----|------------------------|---------|------|
| Core | 不变量 T1-T10、边界情况、失败模式、Replay | ✓ 47 个测试 | 无 |
| Range | 不变量 R1-R5、boundary 演化、continuation 陷阱 | ⏸ 未开始 | 第六刀补充 |
| Lifespan | peer_sample 不足、percentile_rank 边界、双轨分池 | ⏸ 未开始 | 第七刀补充 |
| Structural Position | P1-P4 计算、阈值敏感性、退化处理 | ⏸ 未开始 | 第八刀补充 |
| Service | usage 判定、失败模式 8 种、reason_codes 完整性 | ⏸ 部分 | 第九刀补充 |

---

## 版本治理（v2.1 Bridge §8）

### 变更流程

1. **提案：** 在 malf-engine Issue 中提出变更提案
2. **评审：** 项目负责人和核心贡献者评审
3. **裁决：** 明确是勘误、补充说明还是语义变更
4. **版本号：**
   - 勘误（typo/格式）→ v2.1.1（无需重新审核）
   - 补充说明（不改语义）→ v2.1.1（需审核确认）
   - 语义变更 → v2.2 或 v3.0（需完整审核流程）

### 禁止碎片化

**严禁未经审批的 v2.1 分支版本**（如 v2.1-modified）。

实验性变更应：
1. 在 malf-engine 建立实验分支
2. 文档明确标注"实验性，非权威"
3. 实验成功后提案合并

---

## 快速查找表

| 需要查找 | 参考 v2.1 章节 | 本地文件 |
|---------|--------------|---------|
| Pivot 检测规则 | Core §2.4 | `src/malf/pivot_detection.py` |
| 状态机 9 步顺序 | Core §2.6/O2 | `src/malf/core_engine.py` |
| Guard 更新规则 | Core §2.9/D9 | `src/malf/core_engine.py::_update_guard_if_valid()` |
| Break 判定 | Core §5/D10 | `src/malf/core_engine.py::_check_break()` |
| Transition 双边界 | Core §7/D12-D13 | `src/malf/core_engine.py::_calculate_boundaries()` |
| New wave 双条件 | Core §8/T6 | `src/malf/core_engine.py::_check_new_wave_confirmation()` |
| Range boundary 演化 | Range §3 | 待实现 |
| percentile_rank 公式 | Lifespan §4 | 待实现 |
| P2 同向对照公式 | Structural Position §4 | 待实现 |
| 失败模式处理 | Service §8 | 待实现 |

---

## 附录：v2.1 文件结构

```
I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\
├── AUTHORITY.md                                        # 权威声明（东西南北中已签署，2026-07-26）
├── MANIFEST-deepseek-20260726.json                     # 文件清单+哈希
├── MALF_00_Bridge_v2_1-deepseek-20260726.md           # 入口+变更说明
├── MALF_01_Core_v2_1-deepseek-20260726.md             # Core 层（510 行）
├── MALF_02_Range_v2_1-deepseek-20260726.md            # Range 层（181 行）
├── MALF_03_Lifespan_v2_1-deepseek-20260726.md         # Lifespan 层（214 行）
├── MALF_04_Structural_Position_v2_1-deepseek-20260726.md  # Structural Position 层（242 行）
└── MALF_05_Service_v2_1-deepseek-20260726.md          # Service 层（285 行）
```

**总计：** 1626 行权威定义（v2.0 为 1321 行，+23%）

---

**本文档最后更新：** 2026-07-26  
**下次更新：** 第六刀开工前（更新实施状态）
