# 第四刀完成总结（进行中）

## ✅ 已完成步骤

### S4-1: 扩展数据结构 ✅
- 添加 transition 相关字段到 `CoreStateSnapshot`
- 字段：`transition_boundary_high/low`, `active_candidate_guard_*`, `candidate_replacement_count`

### S4-2: Golden Fixture 人肉推导 ✅
- 场景 A：UP → transition → L0 candidate（首个反向 pivot）
- 场景 B：L0 → L0' 替换（同向 refresh）- 发现会触发 new wave
- 场景 C：L0 → H1 flip-flop（反向替换）
- 场景 D：New wave 确认（H > boundary_high）
- 工具辅助：`debug_t4.py` 验证所有场景的 pivots ✅

### S4-3: Fixture JSON 定稿 ✅
- `t4_transition_l0_candidate.json`
- `t4_transition_l0_replacement.json`（设计问题，会触发 new wave）
- `t4_transition_flip_flop.json`
- `t4_transition_new_wave.json`

### S4-4: 单元测试 ✅
- `tests/test_transition_candidate.py` 创建
- 7 个单元测试（6 passed, 1 skipped）
- 测试覆盖：双边界计算、candidate 检测、替换、flip-flop、new wave 确认

### S4-5: 核心逻辑实现 ✅
- `src/malf/core_engine.py` 更新完成
- 新增方法：
  - `_calculate_boundaries()` - D12 双边界计算
  - `_update_active_candidate()` - O4/T5 flip-flop 逻辑
  - `_check_new_wave_confirmation()` - T6 双条件检查
  - `_enter_new_wave()` - 进入新波段
- 修改 `on_bar()` - 添加 S4 transition 演化分支
- C-05 实现：break bar 自身极值不进 candidate
- 对称实现（up/down 方向）

**测试结果**：
- 单元测试：6 passed, 1 skipped
- guard_break 测试：4 passed（更新为验证 transition 状态）
- 总计：30 passed, 1 skipped, 2 failed

## ⚠️ 已知问题

### 1. T3 Fixture 窗口填充不足
**问题**：`tests/test_t3_same_direction_break.py` 的 2 个端到端测试失败
- H0 @ bar 1，但左侧只有 1 根 bar（bar 0），不满足 k=2 窗口要求
- 违反铁律 1：窗口填充必须充足
- **影响**：第三刀端到端测试失败（但单元测试通过）
- **原因**：第三刀测试在遇到 `NotImplementedError` 时提前终止，掩盖了 fixture 缺陷
- **解决方案**：需要修复 T3 fixture，在序列开头添加足够的窗口填充 bars

### 2. 场景 B（同向替换）设计问题
**问题**：L0 → L0' 同向替换在当前设计下会触发 new wave
- L0 = 90（DOWN candidate）
- boundary_low = 100（broken guard）
- L0' = 85 < boundary_low → 触发 new DOWN wave
- **标记**：单元测试跳过（pytest.skip）

## 📊 测试覆盖

### 通过的测试（30个）
- ✅ Pivot detection（3个）
- ✅ Initialization（6个）
- ✅ Core uninitialized → up_alive（2个）
- ✅ T2 down initialization（1个）
- ✅ Guard break detection（4个，已更新）
- ✅ Transition candidate（6个，1个跳过）
- ✅ Real data smoke（2个）
- ✅ Types carry fixture（5个）

### 失败的测试（2个）
- ❌ test_t3_same_direction_break_up_end_to_end（fixture 问题）
- ❌ test_t3_same_direction_break_down_end_to_end（fixture 问题）

### 跳过的测试（1个）
- ⏭️ test_candidate_replacement_same_direction（场景设计问题）

## 🔄 下一步

### S4-6: 端到端测试
- [ ] 创建 `tests/test_t4_transition_evolution.py`
- [ ] 使用第四刀的 4 个 fixtures
- [ ] 逐 bar 喂入，全等比对

### S4-7: 真实数据冒烟
- [ ] 更新 `tests/test_real_data_smoke.py`
- [ ] 新增 `test_sh600000_with_transition_evolution()`
- [ ] 验证 bar 12 的 L0 替换场景能正确处理

### S4-8: 文档回补
- [ ] 更新 BUILD-PLAN.md（标记完成）
- [ ] 更新 DAILY-LOG
- [ ] 创建 T4-COMPLETION-SUMMARY.md

## 💡 技术亮点

1. **Flip-flop 机制**：active_candidate = latest，不分同向反向（O4/T5）
2. **时序检查**：C-02 严格要求 confirmation 在 active candidate 之后
3. **边界计算**：D12 对称设计（up/down 方向反向）
4. **New wave 双条件**：T6 必须同时满足 candidate 存在 + 突破边界
5. **C-05 实现**：break bar 自身极值不进 candidate 池
6. **逻辑顺序修复**：先检查 new wave，再更新 candidate（避免时序冲突）

## 📝 代码统计

- 新增文件：5个
  - `tests/test_transition_candidate.py`（280+ 行）
  - 4 个 fixture JSON 文件
- 修改文件：4个
  - `src/malf/types.py`（新增 7 个字段）
  - `src/malf/core_engine.py`（新增 ~150 行逻辑）
  - `tests/test_guard_break.py`（更新 2 个测试）
  - `docs/BUILD-PLAN.md`（新增第四刀章节）
- 辅助脚本：2个
  - `debug_t4.py`（验证 fixture 设计）
  - `debug_t3_fixture.py`（诊断 T3 问题）
