# 完整提交脚本 - T7.3-T7.4 + 文件组织规范
# 执行方式：.\COMMIT-T7-AND-CLEANUP.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "提交 T7.3-T7.4 + 文件组织规范" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "I:\asteria-riskbench-components\malf-engine"

# Step 1: 取消暂存旧的临时文件
Write-Host "Step 1: 清理 Git 暂存区..." -ForegroundColor Yellow
$oldTempFiles = @(
    "TEST-T7_3.ps1",
    "create-pr-fixed.ps1",
    "create-pr.ps1",
    "delete-lock-and-commit.ps1",
    "run-all-tests-t7.ps1",
    "run-full-test-report.ps1",
    "run-full-test.ps1",
    "run-percentile-rank-test-green.ps1",
    "run-percentile-rank-test-red.ps1",
    "run-wave-lifespan-test-green.ps1",
    "run-wave-lifespan-test-v2.ps1",
    "run-wave-lifespan-test.ps1",
    "run_all_t7_3_tests.py",
    "run_full_tests.py",
    "run_t7_3_manual.py",
    "run_test_t7_3.py",
    "verify_t7_3.py",
    "test-report-2026-07-27_02-31-32.txt"
)

foreach ($file in $oldTempFiles) {
    git restore --staged $file 2>$null
}
Write-Host "  ✅ 旧临时文件已从暂存区移除" -ForegroundColor Green
Write-Host ""

# Step 2: 添加所有有用的更改
Write-Host "Step 2: 添加新的更改..." -ForegroundColor Yellow
git add -A
Write-Host "  ✅ 所有更改已添加" -ForegroundColor Green
Write-Host ""

# Step 3: 显示将要提交的内容
Write-Host "Step 3: 检查提交内容..." -ForegroundColor Yellow
Write-Host ""
git status --short
Write-Host ""

# Step 4: 提交
Write-Host "Step 4: 提交更改..." -ForegroundColor Yellow
$commitMessage = @"
feat: 完成 Lifespan 层 + 文件组织规范

T7.3: RangeLifespan 指标计算
- 实现 calculate_range_lifespan() 方法
- 修正 resolution_distance_pct 公式（v2.1 Range §5）
- Golden fixture: t7_3_range_lifespan_continuation.json
- 测试：6 passed

T7.4: RangeLifespan peer_sample + rank
- 实现 filter_range_peer_sample() 方法
- 实现 calculate_range_ranks() 方法
- Golden fixture: t7_4_range_ranks_continuation.json（35 样本）
- 测试：5 passed

文件组织规范
- 制定文件组织规范（docs/dev/FILE-ORGANIZATION.md）
- 创建自动清理脚本（CLEANUP-FILES.ps1）
- 更新 CLAUDE.md 添加文件创建规则
- 创建规范目录结构（.work/, scripts/, docs/archive/）
- 归档 T7.3-T7.4 完成报告

真实数据验证框架
- 创建多股票验证脚本（scripts/verify/verify_lifespan_multi_stocks.py）
- 支持 5 只股票验证

里程碑：Lifespan 层 100% 完成
- 总测试：19 passed (Lifespan) + 77 passed (全量)
- 进度：10/20 刀（50%）
"@

git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ 提交成功" -ForegroundColor Green
    Write-Host ""

    # Step 5: 推送
    Write-Host "Step 5: 推送到远程仓库..." -ForegroundColor Yellow
    git push origin HEAD

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 推送成功" -ForegroundColor Green
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "🎉 所有任务完成！" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "完成内容：" -ForegroundColor Cyan
        Write-Host "  ✅ Lifespan 层 100% 完成（19 tests）" -ForegroundColor Gray
        Write-Host "  ✅ 文件组织规范制定" -ForegroundColor Gray
        Write-Host "  ✅ 项目目录整理完成" -ForegroundColor Gray
        Write-Host "  ✅ 真实数据验证框架就绪" -ForegroundColor Gray
        Write-Host ""
        Write-Host "项目进度：10/20 刀（50%）🎊" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host "  ❌ 推送失败" -ForegroundColor Red
        Write-Host "  请手动执行：git push origin HEAD" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ 提交失败" -ForegroundColor Red
    Write-Host "  请检查错误信息" -ForegroundColor Yellow
}
