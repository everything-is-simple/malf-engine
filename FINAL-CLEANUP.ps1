# 最终清理脚本 - 删除根目录的临时文件
# 执行方式：.\FINAL-CLEANUP.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "最终清理 - 删除根目录临时文件" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "I:\asteria-riskbench-components\malf-engine"

# 归档报告
Write-Host "Step 1: 归档报告..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "docs\archive\reports" -Force | Out-Null

if (Test-Path "PROJECT-STATUS-2026-07-27.md") {
    Move-Item "PROJECT-STATUS-2026-07-27.md" "docs\archive\reports\" -Force
    Write-Host "  归档: PROJECT-STATUS-2026-07-27.md" -ForegroundColor Gray
}

if (Test-Path "REVIEW-REPORT-2026-07-27.md") {
    Move-Item "REVIEW-REPORT-2026-07-27.md" "docs\archive\reports\" -Force
    Write-Host "  归档: REVIEW-REPORT-2026-07-27.md" -ForegroundColor Gray
}

if (Test-Path "T7_COMPLETE_AND_FILE_ORGANIZATION.md") {
    Move-Item "T7_COMPLETE_AND_FILE_ORGANIZATION.md" "docs\archive\tasks\T7.3-T7.4\" -Force
    Write-Host "  归档: T7_COMPLETE_AND_FILE_ORGANIZATION.md" -ForegroundColor Gray
}

if (Test-Path "USER-GUIDE-CLEANUP-AND-VALIDATION.md") {
    Move-Item "USER-GUIDE-CLEANUP-AND-VALIDATION.md" "docs\archive\tasks\T7.3-T7.4\" -Force
    Write-Host "  归档: USER-GUIDE-CLEANUP-AND-VALIDATION.md" -ForegroundColor Gray
}
Write-Host "  ✅ 报告归档完成" -ForegroundColor Green
Write-Host ""

# 删除临时脚本
Write-Host "Step 2: 删除临时脚本..." -ForegroundColor Yellow
if (Test-Path "CLEANUP-FILES.ps1") {
    Remove-Item "CLEANUP-FILES.ps1" -Force
    Write-Host "  删除: CLEANUP-FILES.ps1" -ForegroundColor Gray
}

if (Test-Path "COMMIT-T7-AND-CLEANUP.ps1") {
    Remove-Item "COMMIT-T7-AND-CLEANUP.ps1" -Force
    Write-Host "  删除: COMMIT-T7-AND-CLEANUP.ps1" -ForegroundColor Gray
}
Write-Host "  ✅ 临时脚本已删除" -ForegroundColor Green
Write-Host ""

# 检查根目录
Write-Host "Step 3: 检查根目录..." -ForegroundColor Yellow
Write-Host ""
Write-Host "根目录文件列表：" -ForegroundColor Cyan
Get-ChildItem -Path . -File | Where-Object { $_.Extension -in @(".md", ".py", ".ps1", ".toml") } | ForEach-Object {
    $status = if ($_.Name -in @("README.md", "CLAUDE.md", "pyproject.toml", ".gitignore")) { "✅" } else { "⚠️" }
    Write-Host "  $status $($_.Name)" -ForegroundColor Gray
}
Write-Host ""

# 显示期望结果
Write-Host "============================================================" -ForegroundColor Green
Write-Host "✅ 清理完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "根目录应该只有 4 个文件：" -ForegroundColor Yellow
Write-Host "  ✅ README.md" -ForegroundColor Gray
Write-Host "  ✅ CLAUDE.md" -ForegroundColor Gray
Write-Host "  ✅ pyproject.toml" -ForegroundColor Gray
Write-Host "  ✅ .gitignore" -ForegroundColor Gray
Write-Host ""
Write-Host "如果还有其他文件，请手动检查是否需要删除" -ForegroundColor Yellow
Write-Host ""
Write-Host "下一步：提交更改" -ForegroundColor Cyan
Write-Host "  git add -A" -ForegroundColor Gray
Write-Host '  git commit -m "chore: 最终清理 - 归档报告并删除临时脚本"' -ForegroundColor Gray
Write-Host "  git push origin HEAD" -ForegroundColor Gray
Write-Host ""
Write-Host "然后删除本脚本：" -ForegroundColor Cyan
Write-Host "  Remove-Item 'FINAL-CLEANUP.ps1' -Force" -ForegroundColor Gray
