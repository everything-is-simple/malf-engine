# MALF V2 人工验证一键运行脚本 (Windows PowerShell)
# 自动检查依赖、运行验证、生成报告

$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "MALF V2 人工验证 - 一键运行脚本" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# 检测脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EngineRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
$ValidationPkg = Join-Path $EngineRoot ".work\V2-validation-package"
$OutputDir = Join-Path $EngineRoot "var\validation"

Write-Host "📂 工作目录检查..." -ForegroundColor Yellow
Write-Host "   引擎根目录: $EngineRoot"
Write-Host "   验证包路径: $ValidationPkg"
Write-Host "   输出目录: $OutputDir"
Write-Host ""

# 检查验证包是否存在
if (-not (Test-Path $ValidationPkg)) {
    Write-Host "❌ 错误: 验证包不存在: $ValidationPkg" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 验证包存在" -ForegroundColor Green
Write-Host ""

# 检查 Python
Write-Host "🐍 检查 Python 环境..." -ForegroundColor Yellow

$PythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $PythonCmd = $cmd
                Write-Host "   Python 版本: $version" -ForegroundColor Green
                break
            }
        }
    } catch {
        continue
    }
}

if (-not $PythonCmd) {
    Write-Host "❌ 错误: 未找到 Python 3.10+ " -ForegroundColor Red
    Write-Host "   请安装 Python 3.10 或更高版本" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python 版本符合要求 (>= 3.10)" -ForegroundColor Green
Write-Host ""

# 检查必需的 Python 包
Write-Host "📦 检查 Python 依赖..." -ForegroundColor Yellow
$MissingDeps = @()

function Check-Package {
    param($ImportName, $PkgName)

    $result = & $PythonCmd -c "import $ImportName" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ 已安装: $PkgName" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 缺失: $PkgName" -ForegroundColor Red
        return $false
    }
    return $true
}

if (-not (Check-Package "matplotlib" "matplotlib")) { $MissingDeps += "matplotlib" }
if (-not (Check-Package "numpy" "numpy")) { $MissingDeps += "numpy" }

if ($MissingDeps.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  缺少依赖包，正在安装..." -ForegroundColor Yellow
    foreach ($pkg in $MissingDeps) {
        Write-Host "   安装 $pkg..." -ForegroundColor Yellow
        & $PythonCmd -m pip install $pkg --quiet
    }
    Write-Host "✅ 依赖安装完成" -ForegroundColor Green
}

Write-Host ""

# 检查 TDX 数据路径
Write-Host "📊 检查 TDX 数据..." -ForegroundColor Yellow
$TdxFile = "Z:\new_tdx64\vipdoc\sh\lday\sh510300.day"
if (Test-Path $TdxFile) {
    Write-Host "✅ TDX 数据可访问" -ForegroundColor Green
} else {
    Write-Host "⚠️  警告: 标准 TDX 路径不存在: $TdxFile" -ForegroundColor Yellow
    Write-Host "   脚本将使用配置中的路径" -ForegroundColor Yellow
}

Write-Host ""

# 运行验证脚本
Write-Host "🚀 开始生成验证报告..." -ForegroundColor Cyan
Write-Host ""

Set-Location $EngineRoot
& $PythonCmd scripts\verify\v2_visual_validator.py

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "✨ 验证报告生成完成！" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📄 报告位置:" -ForegroundColor Yellow
Write-Host "   HTML: $OutputDir\v2_visual_report.html"
Write-Host "   图表: $OutputDir\charts\"
Write-Host ""
Write-Host "💡 使用提示:" -ForegroundColor Yellow
Write-Host "   1. 在浏览器中打开 HTML 报告"
Write-Host "   2. 使用侧边栏目录快速跳转案例"
Write-Host "   3. 点击顶部导航返回概览"
Write-Host "   4. 勾选验证清单标记验证进度"
Write-Host ""
