# scripts/ - 工具脚本目录

**用途**: 存放调试、验证、分析脚本，保持根目录整洁。

---

## 目录结构

```
scripts/
├── debug/       # 调试脚本（fixture 推导辅助）
├── verify/      # 验证脚本（真实数据测试）
└── analyze/     # 分析脚本（统计/可视化）
```

---

## 脚本分类

### 1. debug/ - 调试脚本

**用途**: 辅助 fixture 推导，验证 pivot 检测是否符合预期

| 脚本 | 用途 | 使用场景 |
|------|------|---------|
| `debug_c07_3.py` | 调试 C07-3 fixture pivot 序列 | C-07 L1 替换场景推导 |
| `debug_guard_break.py` | 调试 guard break 检测逻辑 | 第三刀 guard break 验证 |
| `debug_t2.py` | 调试 T2 DOWN 初始化 fixture | 第二刀 fixture 推导 |
| `debug_t3_fixture.py` | 调试 T3 same-direction break | 第三刀 fixture 推导 |

**典型用法**:
```bash
/d/miniconda/py310/python.exe scripts/debug/debug_c07_3.py
```

---

### 2. verify/ - 验证脚本

**用途**: 真实数据验证，确保引擎在生产数据上稳定

| 脚本 | 用途 | 数据源 |
|------|------|--------|
| `verify_t3.py` | 验证 T3 fixture pivot 检测 | 合成数据 |
| `verify_t3_fixed.py` | 验证修复后的 T3 fixture | 合成数据 |
| `test_offset_0_real_data.py` | 验证 offset=0 真实数据处理 | sh600000 |

**典型用法**:
```bash
/d/miniconda/py310/python.exe scripts/verify/test_offset_0_real_data.py
```

**数据要求**:
- 真实数据脚本需要 TDX 数据路径：`I:/new_tdx64/vipdoc/sh/lday/sh600000.day`
- 如果数据不存在，脚本会跳过

---

### 3. analyze/ - 分析脚本

**用途**: 数据分析、统计、可视化

| 脚本 | 用途 | 输出 |
|------|------|------|
| `analyze_c07_3.py` | 分析 C07-3 bar 序列，检查 pivot 窗口 | 终端输出 |
| `analyze_range_stats.py` | 分析 Range 层真实数据统计 | 终端输出 |

**典型用法**:
```bash
/d/miniconda/py310/python.exe scripts/analyze/analyze_range_stats.py
```

---

## 脚本编写规范

### 1. 命名规范
- **debug_*.py**: 调试 fixture 推导
- **verify_*.py**: 验证功能正确性
- **analyze_*.py**: 数据分析统计
- **test_*.py**: 独立测试（不在 pytest 中）

### 2. 文档规范
每个脚本开头应包含：
```python
"""脚本用途的一句话描述。

详细说明：
- 用途
- 输入数据
- 输出格式
- 使用场景
"""
```

### 3. 路径规范
- 脚本内使用相对路径引用项目文件
- 真实数据路径应检查存在性，不存在时优雅退出

### 4. 执行规范
- 所有脚本应能独立执行（`if __name__ == "__main__"`）
- 使用完整 Python 路径（Windows 环境）
- 不依赖环境变量

---

## 与测试的区别

### scripts/ vs tests/

| 特性 | `scripts/` | `tests/` |
|------|-----------|---------|
| 用途 | 辅助开发、调试、分析 | 自动化测试、验收 |
| 执行方式 | 手动运行 | `pytest` 自动运行 |
| 稳定性 | 可以临时、随意 | 必须稳定、可重复 |
| 生命周期 | 任务完成后可删除 | 长期维护 |
| 数据依赖 | 可依赖外部数据 | 尽量自包含 |

---

## 清理策略

### 何时保留
- 脚本有长期价值（如真实数据验证）
- 脚本可能在未来任务中复用

### 何时删除
- 任务完成，脚本不再需要
- 功能已集成到正式测试
- 脚本过时或被替代

**原则**: 保持 `scripts/` 目录精简，及时清理不再使用的脚本

---

## 示例：创建新脚本

```bash
# 1. 创建脚本
touch scripts/debug/debug_new_feature.py

# 2. 编写脚本（包含 docstring）
# ...

# 3. 运行验证
/d/miniconda/py310/python.exe scripts/debug/debug_new_feature.py

# 4. 任务完成后决定保留或删除
```

---

**维护**: 定期清理不再使用的脚本  
**原则**: 工具脚本服务于开发，不应成为负担
