# malf-engine 建造计划（活文档）

> **活的。** 做完一个 step 勾一个。**只写当前这一刀**——五层的详细 step 不提前排（提前排 = 纸上幻想，前一层通了自然知道下一层怎么切）。
> 验收线见 BUILD-CONTRACT.md；规则见规格。本文只管「下一步动手做什么」。

---

## 第一刀：Core `uninitialized → up_alive`

**目标**：从「无状态」走到「第一个上涨波段确认」，跑通 TDD RED→GREEN 当样板。
**覆盖**（规格 §2）：S1→S9 事件顺序、pivot k=2 延迟确认、first guard = L1、initial wave 创建（`H0→L1→H2>H0`）。

### Step 清单

- [x] S0-1 建目录结构 + pytest 空壳（能跑 `pytest`，占位测试 RED/skip 清晰）
- [x] S0-2 建造合同 + 建造计划两份薄文档
- [x] **S1 推 fixture 预期输出**：按规格 §2 逐根推导 `H0→L1→H2>H0` 的每根 snapshot；复核 §2.4 窗口/时序、双时间戳标注、无计划外 pivot（已确认序列干净）
- [x] S2 预期输出定稿存 `tests/fixtures/uninitialized_to_up_alive.json`（12根，JSON 自检通过）
- [x] S3 定义最小数据结构：PriceBar(D1)/Pivot(D2 双时间戳)/CoreStateSnapshot(§2.9) dataclass + runtime_fingerprint 模块。**L4-6 形态定：记录但不进 lineage_hash（审计元数据）**。fixture 承载测试全过。
- [x] S4 写 pivot 检测（分形 k=2 延迟确认，规格 §2.4）：`src/malf/pivot_detection.py::detect_pivots`。在 golden fixture 上精确复现 H0/L1/H2（含双时间戳），窗口不足返回空列表不崩，k<=0 拒绝。
- [x] S5 写初始化判定（D18/O6，up 方向干净序列）：`src/malf/initialization.py::find_initial_wave`。golden fixture 精确复现 up_alive 确认时刻+guard+progress。down 方向 / H0 替换（C-07）/ L1 替换 三处显式 NotImplementedError，不猜，见下方「已发现待处理」。
- [x] S6 填实 `test_core_uninitialized_to_up_alive.py`：端到端测试，逐 bar 喂入 12 根，每根产出 CoreStateSnapshot 与 fixture 预期全等比对。串起 pivot_detection + initialization，覆盖完整的 uninitialized→up_alive 流程。
- [x] S7 真实数据冒烟：浦发银行 (sh600000) 前 200 根日线，`detect_pivots` 检出 48 个 pivot，无崩溃。`find_initial_wave` 碰到预期的 down 方向 NotImplementedError（说明真实数据确实会走到那条分支），pivot 检测层稳定，未因真实 OHLC 数据特性而崩溃。
- [x] S8 回补规格：L4-6 (runtime_fingerprint) 与 L4-7 (schema_version) 的代码验证形态写入规格 §7.6 定稿。两条挂起项全部闭合。

### 完成标志

第一刀 done = S6 绿 + S7 无意外崩溃。达标后，才排第二刀（同向/反向 break、transition、new wave 的下一条 fixture）。

---

---

## 第二刀：Core `uninitialized → down_alive`（T2 转换）

**目标**：从「无状态」走到「第一个下跌波段确认」，对称实现 up 方向逻辑。
**覆盖**（规格 Core §2，v1.4 T2 定义）：down 方向 3-pivot 序列（`L0→H1→L2, L2<L0`）、初始 guard=H1、progress=L2、对称 up 方向逻辑。

### Step 清单

- [x] **S2-1 推 fixture 预期输出**：按规格 §2 逐根推导 `L0(100)→H1(115)→L2(95), L2<L0` 的每根 snapshot。复核 §2.4 窗口/时序、双时间戳标注、无计划外 pivot。关键验证：
  - k=2 窗口：L0 需要左右各 k 根 bars（添加 2 根窗口填充 bars，对齐第一刀模式）
  - 双时间戳标注：extreme_bar_dt（极值发生）+ confirm_bar_dt（延迟确认）
  - L2 < L0（95 < 100）触发初始化（对称 H2 > H0）
  - `wave_start_price = L2.confirmation_price = 95`（对齐 L4-2 裁决）
  - `wave_start_bar_dt = L2.confirm_bar_dt`（对齐 C-18 消歧）
  - `guard_price = H1.confirmation_price = 115`（对称 up 方向的 L1）
  - `progress_extreme = L2`（首个 progress）
- [x] S2-2 预期输出定稿存 `tests/fixtures/t2_down_initialization.json`（10根，含 2 根窗口填充 bars，JSON 自检通过）
- [x] S2-3 写单元测试：`tests/test_initialization.py::test_find_initial_wave_down_direction_implemented`。验证 L0→H1→L2 序列返回 confirmed=True, direction=DOWN, guard=H1, progress=L2
- [x] S2-4 实现 down 初始化：`src/malf/initialization.py::find_initial_wave` 补全 down 分支（对称 up 逻辑，不等号反向：L2 < L0 vs H2 > H0）。删除 down 方向的 `NotImplementedError`。H0/L0 替换、L1/H1 替换仍保持 NotImplementedError（规格缺口）
- [x] S2-5 填实 `tests/test_t2_down_initialization.py`：端到端测试，逐 bar 喂入 10 根，每根产出 CoreStateSnapshot 与 fixture 预期全等比对。串起 pivot_detection + initialization，覆盖完整的 uninitialized→down_alive 流程
- [x] **S2-6 真实数据冒烟**：浦发银行 (sh600000) 前 200 根日线，验证：
  - `detect_pivots` 同时检出 H 和 L pivot（第一刀已验证 48 个 pivot）
  - `find_initial_wave` 能在真实数据上触发 down_alive（或保持 uninitialized，取决于实际序列）
  - 无崩溃，down 方向初始化逻辑在真实 OHLC 数据上稳定
  - 可能触发的边界情况：连续 L pivot 无 H 穿插、连续 H pivot 无 L 穿插、L0→H1→L2 但 L2 >= L0（不满足触发条件）
  - 更新 `test_real_data_smoke.py`：记录 H/L pivot 分布、验证 down 方向不再抛 NotImplementedError（除非替换场景）
- [x] S2-7 回补文档：在 BUILD-PLAN.md「已发现待处理」标记 down 方向已从待办转为已实现。确认 `initialization.py` 模块 docstring 已更新（标记 up/down 均已实现）

### 完成标志

第二刀 done = S2-5 绿 + S2-6 无意外崩溃 + S2-7 文档更新。达标后，才排第三刀（same-direction break / opposite-direction break / transition）。

---

## 已发现待处理（滚动记录）

_（推 fixture 时若发现规格语义有洞，记在这里，别就地改规格——先记，评估后再动）_

- ~~**S5 发现·down 方向初始化未验证**~~ → **第二刀已排期**：spec §2.4 写了 `L0→H1→L2, L2<L0`，结构上与 up 对称。补 down 方向 golden fixture + 实现（见第二刀 S2-1 至 S2-5）。
- **S5 发现·【填洞 C-07】H0 替换后 L1 候选范围未定义**：spec 只说"更高的 H 可替换 H0，需重新评估条件"，没规定替换后能接受的 L1 候选是否受限（只认替换点之后的 L，还是任意更早的 L 都算）。当前遇到 H0 之后、L1 确认前的第二个 H 会显式报错。**待办**：需要用户/deepseek/规格作者对这条给出裁决，再补 fixture 实现。
- **S5 发现·L1 替换未提及**：spec 对"L1 确认后、H2 确认前又出现更低的 L 是否替换 guard 候选"完全没有规定（不是 C-07 的范围，是全新的空白）。当前显式报错。**待办**：同上，需要裁决 + fixture。
