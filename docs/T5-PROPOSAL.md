# 第五刀建议任务清单

**目标**: 闭合 Core 层，确保基础牢固后再进 Range 层

## 根据 DeepSeek 复查建议，第五刀应聚焦三个方向：

### 1. 补齐 alive 状态的完整行为

**当前状态**: 
- ✅ D16 Progress Confirmation 已实现（2026-07-26 修复）
- ❌ Guard 更新逻辑未实现（D9 守护唯一性铁律）
- ❌ Wave 的 bar_count 未计算
- ❌ alive 期间的 pivot 留痕不完整

**任务**:
1. **Guard 更新逻辑**
   - 在 alive 状态下，确认的回撤 pivot（UP_ALIVE 中的 L，DOWN_ALIVE 中的 H）应替换 guard
   - 验证 D9 守护唯一性：只有确认的 HL/LH 才能替换 guard，HH/LL 只更新 progress
   - 添加测试：guard 被新的同类型 pivot 正确替换

2. **Wave bar_count 计算**
   - 每个 snapshot 记录当前 wave 已持续的 bar 数量
   - 从 initialization 确认的 bar 开始计数
   - break 时记录最终 bar_count

3. **Alive 期间 pivot 留痕**
   - 确保每个确认的 pivot 都被记录到 `_confirmed_pivots`
   - 验证 pivot 的 structure_context 正确标记（active_wave vs transition_candidate）

### 2. 写第一条 Replay 确定性测试（O8 铁律验证）

**当前状态**: 
- ❌ 没有任何测试验证 O8 replay 确定性
- ❌ 没有测试验证 lineage_hash 机制
- ❌ 没有测试验证 runtime_fingerprint 的隔离性

**任务**:
1. **基础 Replay 测试**
   - 同一个 fixture，跑两遍，逐字节比对所有 snapshot
   - 验证 `runtime_fingerprint` 记录但不影响 replay（规格 §7.6）
   - 验证 `core_rule_version`/`pivot_detection_rule_version` 的版本标记正确

2. **跨 session Replay 测试**
   - 模拟两个"独立运行"：reset engine，重新喂相同 bars
   - 验证结果完全一致（除了 runtime_fingerprint 的时间戳部分）

3. **Lineage hash 机制**
   - 实现 lineage_hash 计算（如果尚未实现）
   - 验证相同输入 → 相同 hash

### 3. 扩大真实数据冒烟测试

**当前状态**: 
- ✅ sh600000 200 根日线冒烟测试通过
- ❌ 只有 1 只标的、1 种周期、1 种场景
- ❌ 未记录状态转换统计

**任务**:
1. **多标的覆盖**
   - 增加 3-5 只不同特征的标的：
     - 强趋势（连续单向）
     - 震荡（频繁转换）
     - 低波动（pivot 稀疏）
   - 每只标的至少 500 根 bars

2. **边界场景测试**
   - 跳空场景（找一个 gap up/down 明显的标的）
   - 连续同向 pivot（极端趋势）
   - 极端震荡（transition 内多次 candidate 替换）

3. **状态转换统计**
   - 记录每只标的的状态转换次数：
     - uninitialized → up_alive/down_alive 次数
     - alive → transition 次数
     - transition → new wave 次数
   - 验证至少覆盖所有关键转换路径

---

## 优先级排序

**高优先级（第五刀必做）**:
1. Guard 更新逻辑（D9 核心机制）
2. 第一条 Replay 确定性测试（O8 验收线）
3. 扩大真实数据冒烟（置信度建立）

**中优先级（第五刀建议做）**:
4. Wave bar_count 计算（Range 层依赖）
5. 跨 session Replay 测试（完整 O8 验证）
6. 状态转换统计（覆盖度可见性）

**低优先级（可推迟到第六刀）**:
7. Alive 期间 pivot 留痕（审计需求）
8. Lineage hash 机制（长期 replay 需求）

---

## 验收标准（第五刀 DONE 定义）

第五刀完成时，Core 层应满足：

1. ✅ 所有 Core 状态转换路径有 golden fixture 覆盖
2. ✅ D9 守护唯一性铁律有专门测试验证
3. ✅ 至少 1 条 Replay 确定性测试通过（O8 验收线第一条）
4. ✅ 真实数据冒烟覆盖至少 3 只标的、1500+ 根 bars
5. ✅ 测试套件记录并展示状态转换统计
6. ✅ 所有测试通过，无 skip（除非有明确的规格歧义标记）

---

## 为什么不急着进 Range 层

DeepSeek 的建议非常正确：

> Range 层依赖 Core 层的 progress 更新、transition 边界和 wave 切换——这些 Core 层功能应该先被更严格地验证。

**现实原因**:
- D16 Progress Confirmation 刚在本次修复中补上
- Guard 更新逻辑（D9）尚未完整实现
- Replay 确定性（O8）还没有一条测试
- 真实数据覆盖度不足以建立置信度

如果现在就进 Range 层，会遇到两个问题：
1. **基础不牢**：Range 层的 boundary 演化依赖 Core 层的状态切换，如果 Core 层有 bug，Range 层的测试会变成"在流沙上造房子"
2. **debug 成本高**：一旦 Range 层出问题，无法确定是 Range 层逻辑错误还是 Core 层传入数据有误

**正确顺序**：
1. 第五刀：闭合 Core 层（本文档）
2. 第六刀：Range 层第一刀（boundary 计算 + range 状态机）
3. 第七刀：Range 层第二刀（range 演化 + range_id 生成）
4. 第八刀：Lifespan 层
5. 第九刀：Probability 层
6. 第十刀：Service 层 + 端到端集成

---

**总结**: DeepSeek 说"方向是对的，但不要低估后续工作量"。第五刀的任务就是：在进入后续层之前，确保 Core 层的根基牢固到可以承受整个系统的重量。

**日期**: 2026-07-26  
**来源**: DeepSeek 四大刀验收复查建议
