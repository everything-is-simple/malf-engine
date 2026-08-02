# Lifespan 层完整验证脚本（Windows PowerShell）
# 运行方式：在 PowerShell 中执行 .\TEST-LIFESPAN-LAYER.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Lifespan 层完整验证（T7.1 - T7.4）" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 切换到项目目录
Set-Location "I:\asteria-riskbench-components\malf-engine"

# 运行 Lifespan 层所有测试
Write-Host "运行 Lifespan 层测试（19 个）..." -ForegroundColor Yellow
Write-Host "  - T7.1 + T7.2: WaveLifespan (8 tests)" -ForegroundColor Gray
Write-Host "  - T7.3: RangeLifespan 指标 (6 tests)" -ForegroundColor Gray
Write-Host "  - T7.4: RangeLifespan rank (5 tests)" -ForegroundColor Gray
Write-Host ""

D:\miniconda\py310\python.exe -m pytest tests\test_wave_lifespan.py tests\test_percentile_rank.py tests\test_range_lifespan.py tests\test_range_ranks.py -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✅ Lifespan 层测试全部通过（19 passed）" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "运行全量回归测试..." -ForegroundColor Yellow
    D:\miniconda\py310\python.exe -m pytest tests\ -v --tb=line -q

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "✅ 全量测试通过！" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎉 里程碑：Lifespan 层 100% 完成" -ForegroundColor Cyan
        Write-Host "   - 项目进度：10/20 刀完成（50%）" -ForegroundColor Cyan
        Write-Host "   - 下一步：Structural Position 层（T8.1-T8.4）" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Red
        Write-Host "❌ 全量测试失败！需要修复" -ForegroundColor Red
        Write-Host "============================================================" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "❌ Lifespan 层测试失败" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    exit 1
}
