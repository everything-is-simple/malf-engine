# V2 结构正确性 — 机器预检报告

**日期**: 2026-07-28
**标的**: 510300（沪深300 ETF，日线）
**材料包**: `.work/V2-validation-package/`
**源数据**: `I:\new_tdx64\vipdoc\sh\lday\sh510300.day`
**执行**: 两个独立 stdlib 脚本，不信任引擎自带的审计布尔值

---

## 结论

机器可自动核验的部分**全部通过**。V2 的最终验收仍需人工对照 K 线签字（见文末待办）。

| 检查项 | 结果 |
|---|---|
| Pivot fractal k=2 重算 | 38/38 通过 |
| 确认延迟（extreme→confirm = k=2 根） | 38/38 通过 |
| Guard break 不等式重算 | 4/4 通过 |
| 引擎 `strict_fractal_check` 与独立重算是否一致 | 0 处不一致 |
| 包内 OHLC 与 TDX 原始 `.day` 逐字节对账 | 190/190 bar 字段组一致 |

---

## 两层独立核验的意义

材料包里带了引擎自己算的 `strict_fractal_check=true` 标记。直接信它等于"自己考自己"，没有交叉验证价值。因此本次做了两层**不依赖引擎结论**的核验：

**第一层 — 逻辑重算**（`scripts/verify/v2_independent_crosscheck.py`）
用材料包里每个 pivot 的 5-bar 原始 OHLC 窗口，从零重算：
- fractal k=2：中心 bar 的 high 严格高于左右各 2 根（H pivot）/ low 严格低于左右各 2 根（L pivot）
- 确认延迟：窗口末根就是 confirm bar，且与 extreme bar 相隔恰好 2 根
- pivot.price 与中心 bar 极值一致、extreme_bar_dt 与中心 bar 日期一致
- guard break：UP 方向 `low < guard`，DOWN 方向 `high > guard`

15 个案例共 38 个 pivot 审计、4 个 break 算式，全部通过；且引擎自带 flag 与独立重算**无一处矛盾**。

**第二层 — 源数据对账**（`scripts/verify/v2_tdx_source_check.py`）
第一层仍然只信任"包内嵌的 OHLC"。第二层直接解析 TDX 原始 `.day` 二进制（32 字节/记录，价格 元×100），换算成引擎 int_fixed（元×1000，即 ×10），与包内所有窗口的 190 个 bar 逐字段（O/H/L/C）对账。**0 缺失、0 不一致**。这同时验证了 int_fixed 缩放系数正确——若换算错误会立即暴露为 190 处全错。

---

## 15 个案例覆盖度

材料包实际含 15 个案例（不是交接 prompt 里说的 7 个），覆盖所有要求场景：

| 场景 | 案例 |
|---|---|
| pivot_high / pivot_low（uninitialized） | #6, #11 |
| initialization（up_alive） | #177 |
| guard_break_up | #182, #1865 |
| guard_break_down | #199, #2028 |
| range_evolution | #184 |
| candidate_start / candidate_replacement | #187, #209 |
| new_wave_down / new_wave_up | #188, #2033 / #230, #1854 |
| guard_update（alive） | #1818 |

跨越 2012–2020 多个市场阶段，UP/DOWN 双方向均有覆盖。

---

## 仍需人工完成（V2 真正的验收）

机器只能证明"引擎输出与它读到的原始数据自洽、fractal/break 算术无误"。它**不能**替代人眼判断"引擎选的这个 pivot 在整张 K 线图上是否是结构上正确的那个转折点"。请按 `.work/V2-validation-package/02-VALIDATION-CHECKLIST.md`：

1. 打开 510300 日线图（通达信/东方财富，注意用不复权或与 TDX 同源）
2. 逐案例对照 5-bar 窗口，肉眼确认 Pivot / Guard / Progress / 状态转换是否符合结构直觉
3. 填写每个案例的通过/不通过与备注
4. 完成文末汇总，判定 V2 通过与否

**验收门槛**：Pivot 准确率 > 95%，Guard/Progress 准确率 > 90%，至少核验 10 个案例。

---

## 复现命令

```bash
# Linux VM / Windows（Windows 用 /d/miniconda/py310/python.exe）
python3 scripts/verify/v2_independent_crosscheck.py
python3 scripts/verify/v2_tdx_source_check.py \
  --tdx I:/new_tdx64/vipdoc/sh/lday/sh510300.day
```
