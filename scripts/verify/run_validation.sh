#!/bin/bash
# MALF V2 人工验证一键运行脚本
# 自动检查依赖、运行验证、生成报告

set -e  # 遇到错误立即退出

echo "================================================================================"
echo "MALF V2 人工验证 - 一键运行脚本"
echo "================================================================================"
echo ""

# 检测脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VALIDATION_PKG="$ENGINE_ROOT/.work/V2-validation-package"
OUTPUT_DIR="$ENGINE_ROOT/var/validation"

echo "📂 工作目录检查..."
echo "   引擎根目录: $ENGINE_ROOT"
echo "   验证包路径: $VALIDATION_PKG"
echo "   输出目录: $OUTPUT_DIR"
echo ""

# 检查验证包是否存在
if [ ! -d "$VALIDATION_PKG" ]; then
    echo "❌ 错误: 验证包不存在: $VALIDATION_PKG"
    exit 1
fi

echo "✅ 验证包存在"
echo ""

# 检查 Python 版本
echo "🐍 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "   Python 版本: $PYTHON_VERSION"

# 检查 Python 版本是否 >= 3.10
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "❌ 错误: Python 版本需要 >= 3.10，当前: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python 版本符合要求 (>= 3.10)"
echo ""

# 检查必需的 Python 包
echo "📦 检查 Python 依赖..."
MISSING_DEPS=()

check_package() {
    if ! python3 -c "import $1" 2>/dev/null; then
        MISSING_DEPS+=("$2")
        echo "   ❌ 缺失: $2"
    else
        echo "   ✅ 已安装: $2"
    fi
}

check_package "matplotlib" "matplotlib"
check_package "numpy" "numpy"

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  缺少依赖包，正在安装..."
    for pkg in "${MISSING_DEPS[@]}"; do
        echo "   安装 $pkg..."
        python3 -m pip install "$pkg" --break-system-packages --quiet
    done
    echo "✅ 依赖安装完成"
fi

echo ""

# 检查 TDX 数据路径
echo "📊 检查 TDX 数据..."
TDX_FILE="/sessions/awesome-quirky-mendel/mnt/new_tdx64/vipdoc/sh/lday/sh510300.day"
if [ ! -f "$TDX_FILE" ]; then
    echo "⚠️  警告: 标准 TDX 路径不存在: $TDX_FILE"
    echo "   脚本将使用配置中的路径"
else
    echo "✅ TDX 数据可访问"
fi

echo ""

# 运行验证脚本
echo "🚀 开始生成验证报告..."
echo ""

cd "$ENGINE_ROOT"
python3 scripts/verify/v2_visual_validator.py

echo ""
echo "================================================================================"
echo "✨ 验证报告生成完成！"
echo "================================================================================"
echo ""
echo "📄 报告位置:"
echo "   HTML: $OUTPUT_DIR/v2_visual_report.html"
echo "   图表: $OUTPUT_DIR/charts/"
echo ""
echo "💡 使用提示:"
echo "   1. 在浏览器中打开 HTML 报告"
echo "   2. 使用侧边栏目录快速跳转案例"
echo "   3. 点击顶部导航返回概览"
echo "   4. 勾选验证清单标记验证进度"
echo ""
