# malf-engine 验证审计记录（2026-08-02，修订版）

> 本记录区分“实现完成”和“验证阶段完成”。它不把历史流水线报告、V2 人工案例通过或单元测试通过，扩写成真实 TDX 五层事实已经完整形成。

## 1. 回归门禁

在 `Z:\ai-malf-riskbench-components\malf-engine` 执行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='Z:\ai-malf-riskbench-components\malf-engine;Z:\ai-malf-riskbench-components\malf-engine\src'
$env:MALF_TDX_ROOT='Z:\new_tdx64'
D:\miniconda\py310\python.exe -m pytest tests -q -p no:cacheprovider -rs
```

结果：

```text
109 passed in 1.23s
```

本次修订移除了唯一的测试 skip：原测试场景误把同向 candidate refresh 设计成必然触发 new wave；已改为可复核的同向 refresh fixture，并验证 latest-wins 与 replacement count。

## 2. 验证阶段状态

| 阶段 | 当前状态 | 证据边界 |
|---|---|---|
| V1 流水线 | ✅ 历史报告保留 | 旧集成脚本可跑通真实数据；不替代 T02 正式 driver |
| V2 结构正确性 | ✅ PASS | 15/15 人工案例；机器预检 38/38 pivot、4/4 break |
| V3 参数校准 | 🟡 参数审计通过，经验校准未关闭 | `k=2`、rank 最小 `N=30` 有权威来源；尚无批准的独立敏感性数据集 |
| V4 公式核对 | ✅ PASS（代码合同层） | 新增方向对称 progress、Range resolution distance、严格 rank 阈值测试；既有 P1–P4 测试继续通过 |
| V5 bar_index | ✅ PASS | `bar_index` 从 0 开始、逐 bar 单调递增、回归测试通过 |
| V6 文档治理 | 🟡 本次完成活动文档刷新 | 当前状态/审计记录已刷新；历史归档仍保留，不能伪装成无历史路径 |

## 3. 本次 TDD 变更

- `tests/test_transition_candidate.py`：删除设计问题 skip，补齐同向 candidate refresh fixture。
- `tests/test_validation_contracts.py`：增加 V3/V4/V5 的确定性合同测试。
- `tests/test_wave_lifespan.py`：补齐 DOWN 方向 progress 公式测试。
- `tests/test_real_data_smoke.py`：使用 `MALF_TDX_ROOT` / `Z:\new_tdx64`，不依赖旧 VM 盘符。
- `src/malf/types.py`：纠正 RangeLifespan 最小样本量文档为 `N=30`。
- `docs/.plan/00-当前状态.md`：区分实现完成与验证阶段完成。

## 4. 对 T02 的正式影响

- malf-engine 的 Lifespan、Rank、Structural Position、Service **实现存在且公开 API 回归通过**；不能再把“引擎尚未实现”写成阻塞理由。
- T02 driver 的 synthetic fixture 已证明真实 API 调用顺序：

```text
Core → Lifespan（Wave + Range）→ Rank（Wave + Range）→ Structural Position（P1–P4）→ Service
```

- 真实 TDX 默认 driver 仍不得读取 Core 私有状态或猜测缺失的 WaveLifecycleFacts / resolved Range facts；因此真实数据中的相关字段仍可诚实为 `None + reason_codes`。
- V3 经验校准仍开放；V4–V6 的当前状态已分别记录。按 `docs/spec/kiro-task.md`，V3–V6 属于 malf-engine 后续优化/验证事项，不构成 T02 当前关闭门禁；T00 15 案例人工清单已由用户确认通过，已不再是 T02 阻塞项。

## 5. 不得作出的结论

本审计不授权：

- 将 109 个单元/回归测试写成真实 TDX 五层事实全量通过；
- 将旧 V1 集成脚本替代 T02 44 字段 Service 合同；
- 将任何真实输出升级为 `operational`；
- 提前把 CLI、CHECKPOINT、Parquet、fallback、恢复、scheduler 并入 T02。
