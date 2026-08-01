# MALF V2 验证工具 - 依赖安装说明

> **文档版本**: v1.0  
> **更新日期**: 2026-08-01  
> **适用范围**: malf-engine V2 人工验证工具

---

## 📋 系统要求

### 必需环境

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Python | 3.10 | 3.10+ | 必需，用于运行验证脚本 |
| pip | 任意 | 最新 | Python 包管理器 |
| TDX 数据 | - | - | 510300 日线数据 (.day 文件) |

### 操作系统支持

- ✅ **Linux** (Ubuntu 20.04+, Debian 11+)
- ✅ **Windows** (Windows 10+, PowerShell 5.1+)
- ✅ **macOS** (10.15+)

---

## 📦 Python 依赖包

### 核心依赖

```bash
matplotlib>=3.5.0    # K 线图表生成
numpy>=1.21.0        # 数值计算
```

### 可选依赖（已内置在 Python 标准库）

```bash
pathlib              # 路径操作
json                 # JSON 解析
datetime             # 日期时间处理
```

---

## 🚀 快速安装

### 方法 1: 使用一键脚本（推荐）

#### Linux / macOS

```bash
cd Z:\ai-malf-riskbench-components\malf-engine
chmod +x scripts/verify/run_validation.sh
./scripts/verify/run_validation.sh
```

脚本会自动：
- ✅ 检查 Python 版本
- ✅ 检测缺失的依赖包
- ✅ 自动安装缺失依赖
- ✅ 运行验证并生成报告

#### Windows PowerShell

```powershell
cd Z:\ai-malf-riskbench-components\malf-engine
.\scripts\verify\run_validation.ps1
```

### 方法 2: 手动安装依赖

#### Linux / macOS

```bash
# 安装依赖
python3 -m pip install matplotlib numpy --break-system-packages

# 验证安装
python3 -c "import matplotlib; import numpy; print('依赖安装成功')"

# 运行验证
cd Z:\ai-malf-riskbench-components\malf-engine
python3 scripts/verify/v2_visual_validator.py
```

#### Windows

```powershell
# 安装依赖
python -m pip install matplotlib numpy

# 验证安装
python -c "import matplotlib; import numpy; print('依赖安装成功')"

# 运行验证
cd Z:\ai-malf-riskbench-components\malf-engine
python scripts\verify\v2_visual_validator.py
```

---

## 🔧 常见问题排查

### 问题 1: `ModuleNotFoundError: No module named 'matplotlib'`

**原因**: matplotlib 未安装

**解决**:
```bash
python3 -m pip install matplotlib --break-system-packages
```

### 问题 2: `Permission denied: index.lock`

**原因**: pip 缓存锁定

**解决**:
```bash
rm -rf ~/.cache/pip
python3 -m pip install matplotlib numpy --break-system-packages
```

### 问题 3: `Python version < 3.10`

**原因**: Python 版本过低

**解决**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10

# macOS (Homebrew)
brew install python@3.10

# Windows
# 从 python.org 下载 Python 3.10+ 安装包
```

### 问题 4: `PermissionError: [Errno 13] Permission denied`

**原因**: TDX 数据路径权限问题

**解决**:
```bash
# 检查路径是否存在
ls -la /sessions/awesome-quirky-mendel/mnt/new_tdx64/vipdoc/sh/lday/sh510300.day

# 如果路径不同，修改 v2_visual_validator.py 中的 tdx_path 配置
```

### 问题 5: 图表显示中文乱码

**原因**: 缺少中文字体

**解决**:

**Linux**:
```bash
sudo apt install fonts-wqy-zenhei fonts-wqy-microhei
```

**macOS**:
```bash
# 系统自带中文字体，无需额外安装
```

**Windows**:
```bash
# 系统自带中文字体，无需额外安装
```

然后在代码中配置字体（已在脚本中处理）：
```python
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
```

---

## 🧪 验证安装

运行以下命令验证所有依赖是否正确安装：

```bash
cd Z:\ai-malf-riskbench-components\malf-engine

python3 << 'EOF'
import sys
import matplotlib
import numpy

print("=" * 60)
print("依赖检查 Dependency Check")
print("=" * 60)
print(f"Python 版本 Version: {sys.version}")
print(f"Matplotlib 版本: {matplotlib.__version__}")
print(f"NumPy 版本: {numpy.__version__}")
print("=" * 60)
print("✅ 所有依赖已正确安装 All dependencies installed")
print("=" * 60)
EOF
```

**预期输出**:
```
============================================================
依赖检查 Dependency Check
============================================================
Python 版本 Version: 3.10.12 (main, ...)
Matplotlib 版本: 3.8.0
NumPy 版本: 1.26.0
============================================================
✅ 所有依赖已正确安装 All dependencies installed
============================================================
```

---

## 📊 生成验证报告

### 完整命令

```bash
cd Z:\ai-malf-riskbench-components\malf-engine
python3 scripts/verify/v2_visual_validator.py
```

### 输出文件

```
var/validation/
├── v2_visual_report.html    # 主报告（中英文对照，带导航）
└── charts/
    ├── case_01.png           # 案例 1 K 线图
    ├── case_02.png           # 案例 2 K 线图
    └── ...                   # 共 15 张图表
```

### 查看报告

在浏览器中打开：
```
file:///Z:/ai-malf-riskbench-components/malf-engine/var/validation/v2_visual_report.html
```

或使用一键脚本后会自动提示报告位置。

---

## 🔗 相关文档

- [验证清单](../../.work/V2-validation-package/02-VALIDATION-CHECKLIST.md)
- [机器预检报告](../../docs/.record/reports/VALIDATION-V2-MACHINE-PRECHECK.md)
- [人工签字报告](../../docs/.record/reports/VALIDATION-V2-HUMAN-SIGNOFF.md)
- [MALF V2.1 权威参考](../../.work/V2-validation-package/MALF_V2_1_AUTHORITY_REFERENCE.md)

---

## 📞 技术支持

如遇到其他问题，请：

1. 检查 Python 版本是否 >= 3.10
2. 确认 TDX 数据路径是否正确
3. 查看脚本输出的错误信息
4. 参考上述常见问题排查

---

**文档维护**: 随验证工具更新  
**最后更新**: 2026-08-01
