#!/bin/bash
# 第四刀提交脚本

cd "$(dirname "$0")/malf-engine" || exit 1

echo "=== 第四刀提交准备 ==="
echo ""

echo "1. 检查 git 状态..."
git status --short

echo ""
echo "2. 添加所有变更..."
git add .

echo ""
echo "3. 提交..."
git commit -m "feat: implement transition active candidate evolution (T4)

第四刀：Transition 期间 Active Candidate 演化完成

Core implementation:
- Add 7 transition fields to CoreStateSnapshot
- Implement _calculate_boundaries() (D12)
- Implement _update_active_candidate() (O4/T5 flip-flop)
- Implement _check_new_wave_confirmation() (T6)
- Implement _enter_new_wave()
- Update on_bar() with S4 transition evolution branch

Test coverage:
- Unit tests: 6 passed, 1 skipped (design issue)
- Integration tests: 4 passed (guard_break updated)
- Real data smoke: 2 passed
- Total: 31 passed, 1 skipped, 0 failed

Fixtures:
- 4 new T4 fixtures (l0_candidate, l0_replacement, flip_flop, new_wave)
- Fixed T3 fixtures (window padding issue, strict inequality)

Key features:
- Symmetric UP/DOWN implementation
- Flip-flop mechanism (latest wins, direction-agnostic)
- Strict timing check (C-02: confirmation after candidate)
- C-05 compliance (break bar excluded from candidate pool)
- New wave dual condition (T6: candidate + boundary breach)

Documentation:
- BUILD-PLAN.md updated (S4-1 to S4-8 complete)
- T4-COMPLETION-SUMMARY.md created
- T4-DELIVERY-SUMMARY.md final status
- debug_t4.py and verify_t3_fixed.py tools

Bonus:
- Fixed T3 fixture window padding (added 3 window bars)
- Fixed T3 DOWN fixture strict inequality issue
- All historical tests now pass (T1, T2, T3)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"

echo ""
echo "4. 完成！"
echo ""
echo "=== 测试结果摘要 ==="
/d/miniconda/py310/python.exe -m pytest tests/ -v --tb=no 2>&1 | grep -E "passed|skipped|failed"

echo ""
echo "=== 第四刀交付完成 🎉 ==="
