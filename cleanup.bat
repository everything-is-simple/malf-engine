@echo off
REM malf-engine 项目完整清理脚本
REM 生成日期: 2026-07-27
REM 请以管理员权限运行此脚本

echo ========================================
echo malf-engine 项目清理脚本
echo ========================================
echo.

REM 阶段 1: 根目录和脚本清理
echo [阶段 1] 根目录和脚本清理...
echo.

REM 注意: TASK-SUMMARY.md 已移动
echo ✓ TASK-SUMMARY.md 已移动到 docs/archive/tasks/T6/T6-TASK-SUMMARY.md

REM 删除根目录遗留
if exist commit_t4.sh (
    del /F commit_t4.sh
    echo ✓ 删除 commit_t4.sh
) else (
    echo - commit_t4.sh 已删除
)

REM 删除过时脚本
echo.
echo 删除过时脚本...
if exist scripts\debug\debug_t2.py del /F scripts\debug\debug_t2.py && echo ✓ 删除 debug_t2.py
if exist scripts\debug\debug_t3_fixture.py del /F scripts\debug\debug_t3_fixture.py && echo ✓ 删除 debug_t3_fixture.py
if exist scripts\verify\verify_t3.py del /F scripts\verify\verify_t3.py && echo ✓ 删除 verify_t3.py
if exist scripts\verify\verify_t3_fixed.py del /F scripts\verify\verify_t3_fixed.py && echo ✓ 删除 verify_t3_fixed.py

echo.
echo ========================================
echo [阶段 2] 精简归档文档
echo ========================================
echo.

REM T6 目录清理 (10 -> 4)
echo 清理 T6 目录...
if exist docs\archive\tasks\T6\T6-DAY-0-PROMPT.md del /F docs\archive\tasks\T6\T6-DAY-0-PROMPT.md
if exist docs\archive\tasks\T6\T6-DAY-2-PROMPT.md del /F docs\archive\tasks\T6\T6-DAY-2-PROMPT.md
if exist docs\archive\tasks\T6\T6-DAY-MINUS-1-COMPLETION.md del /F docs\archive\tasks\T6\T6-DAY-MINUS-1-COMPLETION.md
if exist docs\archive\tasks\T6\T6-DAY-MINUS-1-PROMPT.md del /F docs\archive\tasks\T6\T6-DAY-MINUS-1-PROMPT.md
if exist docs\archive\tasks\T6\T6-DAY-MINUS-2-COMPLETION.md del /F docs\archive\tasks\T6\T6-DAY-MINUS-2-COMPLETION.md
if exist docs\archive\tasks\T6\T6-DAY-MINUS-3-COMPLETION.md del /F docs\archive\tasks\T6\T6-DAY-MINUS-3-COMPLETION.md
echo ✓ T6: 10 -> 4 文档

REM T5 目录清理 (5 -> 2)
echo 清理 T5 目录...
if exist docs\archive\tasks\T5\T5-PROPOSAL.md del /F docs\archive\tasks\T5\T5-PROPOSAL.md
if exist docs\archive\tasks\T5\T5-REVIEW-FIXES.md del /F docs\archive\tasks\T5\T5-REVIEW-FIXES.md
if exist docs\archive\tasks\T5\t5_guard_update_derivation.md del /F docs\archive\tasks\T5\t5_guard_update_derivation.md
if exist docs\archive\tasks\T5\t5_replay_test_design.md del /F docs\archive\tasks\T5\t5_replay_test_design.md
echo ✓ T5: 5 -> 2 文档

REM T4 目录清理 (5 -> 2)
echo 清理 T4 目录...
if exist docs\archive\tasks\T4\T4-DELIVERY-SUMMARY.md del /F docs\archive\tasks\T4\T4-DELIVERY-SUMMARY.md
if exist docs\archive\tasks\T4\T4-PROGRESS-SUMMARY.md del /F docs\archive\tasks\T4\T4-PROGRESS-SUMMARY.md
if exist docs\archive\tasks\T4\T4-START-PROMPT.md del /F docs\archive\tasks\T4\T4-START-PROMPT.md
echo ✓ T4: 5 -> 2 文档

REM T3 目录清理 (4 -> 2)
echo 清理 T3 目录...
if exist docs\archive\tasks\T3\T3-TEST-RESULTS.md del /F docs\archive\tasks\T3\T3-TEST-RESULTS.md
if exist docs\archive\tasks\T3\T3-MEMORY-RECORDED.md del /F docs\archive\tasks\T3\T3-MEMORY-RECORDED.md
echo ✓ T3: 4 -> 2 文档

REM C07 目录清理 (2 -> 1)
echo 清理 C07 目录...
if exist docs\archive\tasks\C07\DAILY-LOG-2026-07-26-C07.md del /F docs\archive\tasks\C07\DAILY-LOG-2026-07-26-C07.md
echo ✓ C07: 2 -> 1 文档

REM logs 目录清理 (3 -> 1)
echo 清理 logs 目录...
if exist docs\archive\logs\DAILY-LOG-2026-07-26.md del /F docs\archive\logs\DAILY-LOG-2026-07-26.md
if exist docs\archive\logs\TASK-COMPLETION-REPORT-20260726.md del /F docs\archive\logs\TASK-COMPLETION-REPORT-20260726.md
echo ✓ logs: 3 -> 1 文档

REM summaries 目录清理 (删除整个目录)
echo 清理 summaries 目录...
if exist docs\archive\summaries\FINAL-SUMMARY-20260726.md del /F docs\archive\summaries\FINAL-SUMMARY-20260726.md
if exist docs\archive\summaries\V2_1_ALIGNMENT_COMPLETION_REPORT.md del /F docs\archive\summaries\V2_1_ALIGNMENT_COMPLETION_REPORT.md
if exist docs\archive\summaries rmdir docs\archive\summaries
echo ✓ summaries 目录已删除

REM 根目录清理
echo 清理 archive 根目录...
if exist docs\archive\PROJECT-REORGANIZATION-PLAN.md del /F docs\archive\PROJECT-REORGANIZATION-PLAN.md
echo ✓ 删除重组计划文档

echo.
echo ========================================
echo [阶段 3] 脚本优化 (可选)
echo ========================================
echo.
echo 保守方案: 保留 C07 相关脚本
echo 如需删除 C07 脚本，请手动执行:
echo   del /F scripts\analyze\analyze_c07_3.py
echo   del /F scripts\debug\debug_c07_3.py
echo   del /F scripts\debug\debug_guard_break.py
echo.

echo ========================================
echo 清理完成！
echo ========================================
echo.
echo 清理统计:
echo - 根目录: 2 个遗留文件已处理
echo - 脚本: 9 -> 5 (删除 4 个过时脚本)
echo - 归档文档: 33 -> 12 (删除 21 个冗余文档)
echo.
echo 下一步:
echo 1. 运行测试确认项目正常: python -m pytest
echo 2. 提交清理结果: git add -A ^&^& git commit -m "chore: cleanup project structure"
echo 3. 手动更新 docs/00-INDEX.md (见 PROJECT-CLEANUP-REPORT.md)
echo.
pause
