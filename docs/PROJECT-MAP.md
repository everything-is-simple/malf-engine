# malf-engine 项目地图 🗺️

**目的**: 一张图看懂项目全貌，知道现在在哪里，下一步做什么。

**最后更新**: 2026-07-26

---

## 🎯 项目目标

**交付物**: MALF v2.1 结构计算核心引擎  
**输入**: OHLC 价格数据  
**输出**: `CoreStateSnapshot`（包含 Core + Range 层状态）  
**约束**: 确定性、单遍、零外部依赖

---

## 📍 当前位置

```
进度: ████████████████░░░░ 80% 完成

已完成: Core 层 + Range 层 + C-07 补丁
状态: 生产就绪，功能完整
测试: 58 passed, 1 skipped
```

---

## 🛤️ 整体路线图

### ✅ 已完成的刀

| 刀数 | 名称 | 核心功能 | 测试 | 完成日期 |
|------|------|---------|------|---------|
| **T1** | UP 初始化 | H0→L1→H2 进入 up_alive | 8 | 2026-07-25 |
| **T2** | DOWN 初始化 | L0→H1→L2 进入 down_alive | +6 | 2026-07-25 |
| **T3** | Guard Break | 同向突破 → transition | +4 | 2026-07-26 |
| **T4** | Candidate 演化 | Flip-flop 替换 | +6 | 2026-07-26 |
| **T5** | Guard/Progress 更新 | 新 wave 确认后更新 | +5 | 2026-07-26 |
| **C-07** | Pivot 替换 | H0/L0/L1/H1 替换 | +4 | 2026-07-26 |
| **T6** | Range 层 | Range 诞生/演化/resolution | +7 | 2026-07-26 |

**总计**: 47 Core 层 + 4 C-07 + 7 Range 层 = **58 passed** ✅

**刀的命名说明**:
- **T1-T5**: Core 层的 5 个刀（T = Task）
- **C-07**: 规格补丁（C = Clarification，发现规格空白后的补充实现）
- **T6**: Range 层（独立的大刀）

---

## 📚 核心文档（只需要看这 3 个）

### 1️⃣ 本文档 - 项目地图 ⭐
**路径**: [`docs/PROJECT-MAP.md`](docs/PROJECT-MAP.md)  
**用途**: 一眼看懂项目全貌，现在在哪里，下一步做什么  
**更新**: 每次完成一个大任务时

### 2️⃣ BUILD-PLAN.md - 执行计划
**路径**: [`docs/dev/BUILD-PLAN.md`](docs/dev/BUILD-PLAN.md)  
**用途**: 详细的 step 清单，每完成一步勾一个  
**更新**: 每天（活文档）

### 3️⃣ BUILD-CONTRACT.md - 建造合同
**路径**: [`docs/spec/BUILD-CONTRACT.md`](docs/spec/BUILD-CONTRACT.md)  
**用途**: 范围、验收标准、7 条铁律  
**更新**: 几乎不变（稳定）

**其他文档都是支撑材料**，不需要天天看。

---

## 🧭 快速导航

### 我想...

| 需求 | 看这个 |
|------|--------|
| 了解项目全貌 | **本文档** (PROJECT-MAP.md) ⭐ |
| 知道下一步做什么 | dev/BUILD-PLAN.md |
| 查规格定义（如 D18） | spec/MALF_V2_1_AUTHORITY_REFERENCE.md |
| 使用 API | guide/API.md |
| 查看历史任务 | archive/tasks/T*/ |
| 运行测试 | `pytest` |

---

## 🎯 当前状态总结

### 已完成 ✅
- ✅ **Core 层**: 100% 完成（T1-T5 + C-07）
- ✅ **Range 层**: 100% 完成（T6）
- ✅ **测试**: 58 passed, 1 skipped
- ✅ **真实数据验证**: 通过（sh600000, 200 bars）

### 功能完成度

#### Core 层（100% 完成）✅
- ✅ Pivot 检测（k=2 延迟确认）
- ✅ 初始化判定（UP/DOWN 双方向）
- ✅ C-07 Pivot 替换（H0/L0/L1/H1）
- ✅ Guard break 检测（同向/反向突破）
- ✅ Progress 追踪
- ✅ TRANSITION 期间 Candidate 机制
- ✅ 确定性 replay

#### Range 层（100% 完成）✅
- ✅ Range 诞生（guard break 触发）
- ✅ Boundary 双系统（init / now）
- ✅ Evolution 检测
- ✅ Resolution 判定（T6 定理）
- ✅ Continuation/Reversal 分类

---

## 🚀 下一步选项

### 选项 A: 工程化增强（推荐）✅

| 任务 | 功能 | 时间 | 价值 |
|------|------|------|------|
| 序列化支持 | JSON 导出/导入 snapshot | 4h | 高（状态持久化） |
| CI/CD | GitHub Actions 自动测试 | 4h | 高（质量保证） |
| PyPI 发布 | 打包发布 | 4h | 高（可用性） |
| 性能优化 | 基准测试 + 优化 | 8h | 中（大数据量） |

### 选项 B: 新功能层

| 层 | 功能 | 时间 | 状态 |
|----|------|------|------|
| Lifespan | 波段生命周期 | 3-5天 | ⚠️ v2.1 规格不完整 |
| Probability | 概率计算 | 3-5天 | ⚠️ v2.1 规格不完整 |

### 选项 C: 项目收尾

- 整理文档
- 写使用示例
- 标记为 v1.0

**建议**: **选项 A（工程化增强）**，核心功能已完整，现在需要让它可用。

---

## 🔧 开发命令速查

```bash
# 运行测试
/d/miniconda/py310/python.exe -m pytest

# 运行特定测试
/d/miniconda/py310/python.exe -m pytest tests/test_c07_replacement.py

# 详细输出
/d/miniconda/py310/python.exe -m pytest -v

# 验证文档链接
/d/miniconda/py310/python.exe scripts/verify/verify_doc_links.py
```

---

## 📝 版本规划

### v1.0（当前可发布）✅
- ✅ Core 层完整
- ✅ Range 层完整
- ✅ 真实数据验证通过
- ✅ 58 个测试全部通过

### v1.1（工程化增强）
- ⬜ 序列化支持
- ⬜ CI/CD
- ⬜ PyPI 发布

### v2.0（新功能层）
- ⬜ Lifespan 层
- ⬜ Probability 层
- **注意**: 需要先完善规格

---

## ❓ 常见问题

### Q: 为什么 T1-T5 后是 C-07，然后是 T6？
**A**: 
- **T1-T5**: Core 层的 5 个刀（核心状态机）
- **C-07**: 规格补丁（发现规格空白，补充实现 Pivot 替换）
- **T6**: Range 层（独立的大刀，震荡期识别）

顺序：Core 层（T1-T5 + C-07 补丁） → Range 层（T6）

### Q: 还需要多少刀才能完成？
**A**: **0 刀**。Core + Range 层已完整，v2.1 规格中的核心功能已全部实现。

### Q: 下一步做什么？
**A**: **看你的目标**：
- 想让引擎可用 → 工程化增强（序列化/CI/CD/发布）
- 想增加功能 → 新功能层（需先完善规格）
- 想结束项目 → 项目收尾，标记 v1.0

### Q: 文档太多，看哪个？
**A**: **只看 3 个**:
1. **本文档**（PROJECT-MAP.md）- 项目地图 ⭐
2. dev/BUILD-PLAN.md - 详细计划
3. spec/BUILD-CONTRACT.md - 验收标准

---

## 💡 最重要的信息

```
✅ Core 层 100% 完成
✅ Range 层 100% 完成  
✅ 58 测试全部通过
✅ 真实数据验证通过

🎉 现在可以发布 v1.0

📋 下一步：选一个工程化增强任务
   - 序列化支持（推荐）
   - CI/CD 配置
   - PyPI 发布
```

---

**维护**: 每完成一个大任务更新本文档  
**负责人**: 项目所有者
