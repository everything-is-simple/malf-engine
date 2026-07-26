# MALF v2.0 引擎实现合同 / 勘误补丁

> **重要更新（2026-07-26）**：本补丁的第 1-3 层（21 条）已全部回写入 **MALF v2.1 Definitive** 正文。  
> **新实现请直接参考 v2.1 正文**，本文档保留作为历史记录和第 4A/4B 层立法参考。
> 
> **v2.1 权威文档**：`I:\asteria-riskbench-Definitive-validated\MALF_Definitive_v2_1-deepseek-20260726\`  
> **本地引用**：`MALF_V2_1_AUTHORITY_REFERENCE.md`
>
> ---
>
> **性质**：本文档是对 Definitive v2.0 五份规格文档的实现层勘误与补充，**不替代**也**不修改**已验证正文。  
> **作用**：闭合 deepseek 审计发现的 43 条缺口，供 TDD 实现前参考。  
> **分层原则**：勘误（零风险）→ 还原（考据）→ 消歧（影响正确性）→ 立法（需拍板）。
>
> **第 1-3 层状态**：✅ 已全部回写入 v2.1 正文，新实现直接参考 v2.1。  
> **第 4A 层状态**：✅ 5 条高优先级立法已全部拍板并回写入 v2.1（见 v2.1 相应章节）。  
> **第 4B 层状态**：⏸ 13 条边实现边定，发布前闭合即可。

---

## 第 0 层 · 审计来源

本补丁响应 deepseek 的两份审计文档：
- `malf2.0-引擎.md`（主文档）
- `malf2.0-引擎-严谨性补丁.md`（43 条缺口清单）

deepseek 审计结论：**专家级、事实基础扎实、但"还原"与"立法"混在一起**。本合同将两者严格分层。

---

## 第 1 层 · 勘误（立即生效，零风险）

### R-03 · Range §5 过期修正标注

**问题**：Range v2.0 §5 第 128 行仍保留 `"⚠️ 修正：此处旧版描述错误，见 §6 最终定义表"`，但错误描述已删除。

**修正**：删除该标注，或改为 `"历史勘误已闭合，本段为定稿"`。

---

### X-01 · 实现路径引用历史系统

**问题**：Core v2.0 多处引用 `src/asteria/malf/pivot.py`、`core.py::CoreEngine`，这些是旧 Asteria 代码库路径，RiskBench 仓库中不存在。

**澄清**：这些路径指向**历史系统参考实现**，非当前实现要求。RiskBench 实现路径为：
- `src/malf/` （malf-engine 独立包，实验目录 `RB-FX-008`）
- 五层验证通过后迁移至主仓库 `src/riskbench/malf/`

**操作**：在 Core v2.0 实现路径首次出现处加脚注：`"此路径指向历史 Asteria 系统，RiskBench 重新实现于 src/malf/"`。

---

## 第 2 层 · 还原（考据，低风险）

以下编号与定义均来自 **v1.4 权威文档**，非新创，直接还原。

### C-01 · D3/D6/D7 编号还原

**deepseek 原说法**：`"D3/D6/D7 已合并至 D4/D8/D9，v1.4 收紧时删除"`  
**核实结果**：❌ **此说法错误**。v1.4 `core-definitions.md` 完整保留：
- **D3** = 结构上下文（Context）
- **D6** = 上涨结构（Upward Structure）
- **D7** = 下跌结构（Downward Structure）

**真实情况**：v2.0 Core §2 基础对象表未重列这三条，但 §11 编号声明明确写 `"D1–D17 / T1–T8 / O1–O8 编号不变"`。这三条从未删除，只是未在表中显式列出。

**还原操作**：在 Core v2.0 §2 基础对象表后补充说明：

> **编号连续性说明（v1.4 沿用）**：  
> - **D3** = 结构上下文（Context）：波段确认所需的 pivot 序列与时序条件  
> - **D6** = 上涨结构（Upward Structure）：`H0 → L1 → H2, H2 > H0`  
> - **D7** = 下跌结构（Downward Structure）：`L0 → H1 → L2, L2 < L0`  
> 
> 这三条定义在 v1.4 Core 中完整保留，v2.0 未删除仅未重列于基础对象表。

---

### C-03 · D16 Progress Confirmation 还原

**v1.4 定义**（`core-definitions.md`）：

> **D16 Progress Confirmation（进展确认）**：  
> 波段方向的新 pivot 确认后，若该 pivot 在波段方向上优于当前 progress_extreme，则更新 progress。  
> - Up 波段：新 H pivot 且 price > progress_extreme_price → 更新  
> - Down 波段：新 L pivot 且 price < progress_extreme_price → 更新

**v2.0 现状**：Core §2.5、§2.6 描述了 progress 更新逻辑，但未给 D16 编号。

**还原操作**：在 Core v2.0 §2.6 结尾补充：

> 上述逻辑对应 **D16 Progress Confirmation（进展确认）**。

---

### C-04 · D17 New Wave 还原

**v1.4 定义**：

> **D17 New Wave（新波创建）**：  
> 当前波段被 break 后，系统进入 transition。若在 transition 期间确认了**与前波相反方向**的初始化序列（D6 或 D7），则创建新波段。

**v2.0 现状**：Core §2.8 描述了 break 后创建新波的流程，但未给 D17 编号。

**还原操作**：在 Core v2.0 §2.8 末尾补充：

> 上述创建新波段的条件对应 **D17 New Wave（新波创建）**。

---

### C-16 · T1/T2/T7/T8 转换规则还原

**v1.4 定义**（`core-definitions.md` 转换表）：

| 编号 | 转换 | 触发条件 |
|------|------|---------|
| **T1** | uninitialized → up_alive | 确认上涨初始化序列 (D6) |
| **T2** | uninitialized → down_alive | 确认下跌初始化序列 (D7) |
| **T7** | transition → up_alive / down_alive | transition 期间确认新方向初始化序列 (D17) |
| **T8** | (stay in) transition | break 后未能在合理时间内确认新波段 |

**v2.0 现状**：Core §2 事件序列表 (S1-S9) 未显式给 T 编号。

**还原操作**：在 Core v2.0 §2.9 转换小节补充：

> 本节转换对应 v1.4 转换规则编号：  
> - **T1** = S9（uninitialized → up_alive）  
> - **T2** = 下跌方向对称转换（待第二刀实现）  
> - **T7** = break 后创建新波段的转换  
> - **T8** = transition 状态保持（非波段状态）

---

### O5 · Transition Primitive Context 还原

**v1.4 定义**（`boundary-rules.md`）：

> **O5 Transition Primitive Context（过渡期原语上下文）**：  
> transition 状态下，系统保持最后一个 terminated 波段的 guard 作为参考，但不发布波段级输出。  
> Transition 是**非波段状态**——没有 active_wave_id，没有 direction，只有 system_state = transition。

**v2.0 现状**：Core §2.8 描述了 transition 的行为，但未给 O5 编号。

**还原操作**：在 Core v2.0 §2.8 transition 段落末尾补充：

> Transition 期间的状态保持规则对应 **O5 Transition Primitive Context（过渡期原语上下文）**。

---

### O1/O8 完整性还原

**v1.4 定义**（`boundary-rules.md`）：

> **O1 Uninitialized No Output（未初始化无输出）**：  
> system_state = uninitialized 期间，wave 相关字段全部为 None，不发布波段输出。

> **O8 Replay Determinism（重放确定性）**：  
> 相同输入序列 + 相同 rule_versions → 逐字节相同的 snapshot 输出与 lineage_hash。

**v2.0 现状**：Core §2.10 不变量表未列出这两条。

**还原操作**：在 Core v2.10 不变量表补充：

| 编号 | 不变量 |
|------|--------|
| **O1** | Uninitialized 期间无波段输出（wave 字段全 None） |
| **O8** | Replay 确定性（相同输入+版本 → 相同输出） |

---

## 第 3 层 · 消歧（影响状态机正确性，TDD 前必须钉死）

以下消歧基于 v1.4 语义与 v2.0 上下文推导，已标注依据。

### C-02 · D16 "之后" 的时序语义

**原文**：Core v2.0 §2.6 `"在该 pivot **之后**确认的新 pivot..."`

**歧义**：是指 bar_dt 更晚，还是 pivot 序列中的后续位置？

**消歧（基于 v1.4 §2.4 时序不对称）**：  
**"之后" = 严格 bar_dt 更晚**（按 confirm_bar_dt 比较）。  
Pivot 按 confirm_bar_dt 排序，状态机逐 bar 推进，"之后"指时间上更晚确认的 pivot。

**影响**：影响 progress 更新的时序判定逻辑。

---

### C-05 · Break bar 自身的 low 是否作为 guard 候选

**原文**：Core v2.0 §2.7 `"break bar 的 low 成为下一个 guard 候选"`

**歧义**：这里的"候选"是指：
1. break bar 的 low 直接成为 guard_price（即时生效）
2. break bar 的 low 只是候选，需等该 bar 被确认为 L pivot 后才生效

**消歧（基于 v1.4 guard 延迟确认语义）**：  
**选项 2**：break bar 的 low 不会**当场**成为 guard，需等该 bar 被确认为 L pivot（k 根延迟后）才进入 guard。

**理由**：guard 必须是**确认的 pivot**（D2），不能是未确认的 bar low。§2.4 时序不对称规则适用于所有 pivot，包括 break 后的 guard 候选。

**影响**：影响 break 后 transition 期间的 guard 更新逻辑。

---

### C-17 · Bar 归属：wave 内 vs. range 内

**原文**：Range v2.0 §3 `"一个 bar 可以同时属于 wave 和 range"`

**歧义**：
- break bar 本身算在被 break 的 wave 里吗？
- break bar 算在新 range 的第一根吗？

**消歧（基于 Range v2.0 §6 边界定义表）**：
- **Break bar 本身仍属于被 break 的 wave**（wave 在 break bar 处 terminated）
- **Break bar 同时是 range 的第一根**（range_start_bar_dt = break_bar_dt）

**影响**：影响 wave 的 bar_count、range 的 bar_count 计算。

---

### C-18 · 新波段创建时，confirmation bar 归属

**原文**：Core v2.0 §2.8 `"H2 确认时创建新 up 波段"`

**歧义**：H2 的 confirm_bar 算在新波段的第一根吗，还是新波段从 H2 的 extreme_bar 起算？

**消歧（基于 v1.4 wave 边界规则）**：  
**Wave 从 confirmation 事件发生的 bar 起算**。  
- 新 up 波段：wave_start_bar_dt = H2 的 confirm_bar_dt  
- 新 down 波段：wave_start_bar_dt = L2 的 confirm_bar_dt

**理由**：状态机在 confirm_bar_dt 时刻"看见"了 H2/L2，此时波段才存在。Extreme_bar_dt 是回溯信息，不是状态机的决策时刻。

**影响**：影响 wave_start_bar_dt、bar_count、duration 计算。

---

### R-05 · Boundary 演化在 §6 后 §7 前

**原文**：Range v2.0 §6 定义了 initial boundary，§7 定义了 break 事件，但未说明 boundary 何时演化。

**歧义**：Boundary 是在每个新 pivot 确认时立刻更新，还是在特定事件（如 progress 更新）时更新？

**消歧（基于 Range v2.0 §1 boundary 定义）**：  
**Boundary 在每个波段方向的 progress 更新时演化**。  
- Up 波段：新 H pivot 确认且 price > current boundary high → 更新 boundary high  
- Down 波段：新 L pivot 确认且 price < current boundary low → 更新 boundary low

**时机**：在 Core 的 D16 Progress Confirmation 触发后、Range 层同步更新 boundary。

**影响**：影响 Range §6-§7 的状态演化逻辑。

---

## 第 4 层 · 立法（需拍板，锁 replay 契约）

以下条目为 **本合同新定义**，非历史还原。Deepseek 提供的默认值作为提案基线，每条需最终裁决。

### 4A · 高优先级立法（replay 校验前置依赖）

| 编号 | 缺口 | deepseek 提案 | 裁决 |
|------|------|--------------|------|
| **L4-1** | wave_id / range_id 生成规则 | `wave_id = "{symbol}_{timeframe}_w_{seq}"`<br>`range_id = "{symbol}_{timeframe}_r_{seq}"` | ✅ 采纳（2026-07-27）<br>**依据**：Range §1 明确 `range_id` 由 `open_transition_id` 一一对应，该格式符合跨层对齐要求。Seq 单调递增保证唯一性。 |
| **L4-2** | wave_start_price 定义 | `wave_start_price = confirmation_price`<br>（initial wave: H2 for up, L2 for down） | ✅ 采纳（2026-07-27）<br>**依据**：C-18 消歧已确认 wave 从 confirmation 事件起算，start_price 对齐 confirmation_price 保证时序一致性。Initial up wave = H2 price，down wave = L2 price。 |
| **L4-3** | percentile_rank 公式 | Mid-rank：`(count_below + 0.5 * count_equal) / total` | ⚠️ 改为（2026-07-27）<br>**公式**：`(count_below + 0.5 * count_equal) / total`，`total` 包含自身<br>**边界**：`total = 0` 时返回 `None`（无法排名）<br>**精度**：结果 round 到 4 位小数（0.0000 - 1.0000）<br>**依据**：Mid-rank 是标准分位算法，但需钉死 total=0 边界与输出精度以保证 replay 一致性。 |
| **L4-4** | lineage_hash 计算方法 | SHA-256(规范化 JSON) | ⚠️ 改为（2026-07-27）<br>**算法**：SHA-256(规范化 JSON)<br>**规范化规则**：<br>1. 字段按字母序排序<br>2. Float 保留 2 位小数（与 price normalization 对齐）<br>3. None 序列化为 `null`<br>4. Datetime 序列化为 ISO 8601 字符串（UTC）<br>5. 无空格、紧凑格式<br>**依据**：Service §7 列了字段但未给算法，必须钉死序列化规则才能保证 O8 replay 确定性。 |
| **L4-5** | 精度策略参数化 | `price_normalization_policy ∈ {round_2, integer_fixed_point_v0_1}` | ✅ 采纳（2026-07-27）<br>**默认策略**：`round_2`（Definitive 标准）<br>**依据**：Definitive 用 round(2)，RiskBench variant 可能用 int_fixed，参数化允许两种策略共存。Replay 校验时必须指定相同策略。 |

**说明**：  
- **L4-1**：涉及跨层引用（Range §1 已用 range_id，需对齐）  
- **L4-2**：Lifespan §2 旁注暗示用 confirmation_price，但未成文  
- **L4-3**：影响 Lifespan 所有分位计算的 replay 一致性  
- **L4-4**：Service §7 只列字段名，未给算法  
- **L4-5**：Definitive 用 round(2)，RiskBench variant 用 int_fixed，需参数化

---

### 4B · 中优先级立法（发布前闭合）

| 编号 | 缺口 | deepseek 提案 | 裁决 |
|------|------|--------------|------|
| **L4-6** | reason_code 枚举 | `{initial_wave, same_direction_break, opposite_direction_break, ...}` | ⬜ 待填 |
| **P-02** | lifespan 起算点 | `= wave_start_bar_dt`（与 C-18 对齐） | ⬜ 待填 |
| **P-03** | peer_sample 的"同方向"定义 | 仅 direction 相同（不区分 same/opposite break） | ⬜ 待填 |
| **P-04** | count 截断规则 | 活波达到 max_bar_count → 不再计入统计 | ⬜ 待填 |
| **S-02** | API 错误码体系 | HTTP 标准码 + 自定义 4xx/5xx | ⬜ 待填 |
| **S-03** | 批量查询 pagination | cursor-based（避免 offset 飘移） | ⬜ 待填 |
| **S-04** | snapshot 压缩策略 | 活波全量 + 历史波段仅 metadata | ⬜ 待填 |
| **S-05** | 多 symbol 并发隔离 | 每个 (symbol, timeframe) 独立状态机实例 | ⬜ 待填 |
| **C-19** | pivot_id 生成 | `"{symbol}_{timeframe}_{H|L}_{extreme_bar_dt}_{seq}"` | ⬜ 待填 |
| **R-06** | range_id 与 transition_id 关系 | `range_id` 直接绑定 `transition_id`（1:1） | ⬜ 待填 |
| **L-05** | duration 单位 | 秒（timestamp 差值） | ⬜ 待填 |
| **X-02** | replay 测试覆盖率 | 每条转换路径 ≥1 replay fixture | ⬜ 待填 |
| **X-03** | 版本兼容性策略 | 同 major 版本保证 replay 一致 | ⬜ 待填 |

---

## 裁决流程

1. **第 1-3 层**：直接采纳，零风险，立即写入 TDD fixture  
2. **第 4A 层**：逐条拍板（5 条），完成后即可进 TDD RED  
3. **第 4B 层**：边实现边定（13 条），发布前闭合即可

---

## 修订记录

| 日期 | 操作 | 说明 |
|------|------|------|
| 2026-07-26 | 初稿 | 响应 deepseek 审计，分层闭合 43 条缺口 |
| 2026-07-27 | 第 4A 层裁决 | 5 条高优先级立法全部拍板，replay 契约锁定 |
