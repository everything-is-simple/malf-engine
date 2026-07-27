# 文件清理脚本（Windows PowerShell）
# 运行方式：在 PowerShell 中执行 .\CLEANUP-FILES.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "文件清理脚本 - 整理项目目录结构" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 确保在正确的目录
Set-Location "I:\asteria-riskbench-components\malf-engine"

Write-Host "Phase 1: 创建目录结构..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path ".work\test-runs" -Force | Out-Null
New-Item -ItemType Directory -Path ".work\debug" -Force | Out-Null
New-Item -ItemType Directory -Path ".work\scratch" -Force | Out-Null
New-Item -ItemType Directory -Path "scripts\verify" -Force | Out-Null
New-Item -ItemType Directory -Path "scripts\debug" -Force | Out-Null
New-Item -ItemType Directory -Path "scripts\tools" -Force | Out-Null
New-Item -ItemType Directory -Path "docs\archive\tasks\T7.3-T7.4" -Force | Out-Null
New-Item -ItemType Directory -Path "docs\reports\lifespan" -Force | Out-Null
Write-Host "✅ 目录结构创建完成" -ForegroundColor Green
Write-Host ""

Write-Host "Phase 2: 删除临时验证/调试脚本..." -ForegroundColor Yellow
$tempScripts = @(
    "verify_t7_3.py",
    "verify_t7_4.py",
    "debug_t7_4.py",
    "run_test_t7_3.py",
    "run_all_t7_3_tests.py",
    "run_t7_3_manual.py",
    "run_full_tests.py"
)
foreach ($file in $tempScripts) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  删除: $file" -ForegroundColor Gray
    }
}
Write-Host "✅ 临时脚本清理完成" -ForegroundColor Green
Write-Host ""

Write-Host "Phase 3: 删除临时 PowerShell 脚本..." -ForegroundColor Yellow
$tempPs1 = @(
    "TEST-T7_3.ps1",
    "create-pr.ps1",
    "create-pr-fixed.ps1",
    "delete-lock-and-commit.ps1",
    "run-all-tests-t7.ps1",
    "run-full-test.ps1",
    "run-full-test-report.ps1",
    "run-percentile-rank-test-green.ps1",
    "run-percentile-rank-test-red.ps1",
    "run-wave-lifespan-test.ps1",
    "run-wave-lifespan-test-v2.ps1",
    "run-wave-lifespan-test-green.ps1"
)
foreach ($file in $tempPs1) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  删除: $file" -ForegroundColor Gray
    }
}
Write-Host "✅ PowerShell 脚本清理完成" -ForegroundColor Green
Write-Host ""

Write-Host "Phase 4: 归档完成报告..." -ForegroundColor Yellow
if (Test-Path "T7_3_COMPLETION_REPORT.md") {
    Move-Item "T7_3_COMPLETION_REPORT.md" "docs\archive\tasks\T7.3-T7.4\T7.3-COMPLETION.md" -Force
    Write-Host "  归档: T7_3_COMPLETION_REPORT.md → docs\archive\tasks\T7.3-T7.4\" -ForegroundColor Gray
}
if (Test-Path "T7_3_T7_4_SUMMARY.md") {
    Move-Item "T7_3_T7_4_SUMMARY.md" "docs\archive\tasks\T7.3-T7.4\SUMMARY.md" -Force
    Write-Host "  归档: T7_3_T7_4_SUMMARY.md → docs\archive\tasks\T7.3-T7.4\" -ForegroundColor Gray
}
if (Test-Path "LIFESPAN_LAYER_COMPLETE.md") {
    Move-Item "LIFESPAN_LAYER_COMPLETE.md" "docs\reports\lifespan\LAYER-COMPLETE.md" -Force
    Write-Host "  归档: LIFESPAN_LAYER_COMPLETE.md → docs\reports\lifespan\" -ForegroundColor Gray
}
Write-Host "✅ 报告归档完成" -ForegroundColor Green
Write-Host ""

Write-Host "Phase 5: 移动测试脚本..." -ForegroundColor Yellow
if (Test-Path "TEST-LIFESPAN-LAYER.ps1") {
    Move-Item "TEST-LIFESPAN-LAYER.ps1" "scripts\test_lifespan_layer.ps1" -Force
    Write-Host "  移动: TEST-LIFESPAN-LAYER.ps1 → scripts\" -ForegroundColor Gray
}
Write-Host "✅ 测试脚本整理完成" -ForegroundColor Green
Write-Host ""

Write-Host "Phase 6: 清理测试报告..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "test-report-*.txt" | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  删除: $($_.Name)" -ForegroundColor Gray
}
Write-Host "✅ 测试报告清理完成" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host "✅ 文件清理完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "根目录剩余文件（应该只有永久文件）：" -ForegroundColor Yellow
Get-ChildItem -Path . -File | Where-Object { $_.Extension -in @(".md", ".py", ".ps1") } | ForEach-Object {
    Write-Host "  $($_.Name)" -ForegroundColor Gray
}
Write-Host ""

Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "  1. 运行 'git add -A' 添加更改" -ForegroundColor Gray
Write-Host "  2. 运行 'git status' 检查状态" -ForegroundColor Gray
Write-Host "  3. 如果满意，提交更改" -ForegroundColor Gray
