# RiskBench 组件实验工厂

本目录用于回答一个具体问题：**哪些免费开源组件在 RiskBench 的约束下真的能工作，哪些不能，什么时候可以装配。**

工厂不是主系统，不承载正式业务代码，不读取真实 TDX/MALF 目录，不把试验结果自动升级为主系统选型。

## 快速开始（Windows PowerShell）

```powershell
Set-Location J:\asteria-riskbench-factory
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Playwright 浏览器只在需要执行浏览器验收时安装：

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest experiments/RB-FX-005-playwright-viewer -q
```

图表实验在自己的 npm 工作目录中运行，不影响 Python 环境：

```powershell
Set-Location experiments/RB-FX-007-chart-comparison
npm install --package-lock-only
npm install
node smoke.mjs
```

## 当前实验

| ID | 能力 | 当前状态 |
|---|---|---|
| RB-FX-001 | Python 标准库边界：TDX 32 字节解析、哈希、原子指针 | trial-passed（证据已生成） |
| RB-FX-002 | Pydantic v2 发布快照合同 | trial-passed（证据已生成） |
| RB-FX-003 | FastAPI + Uvicorn 只读 Viewer | trial-passed（证据已生成） |
| RB-FX-004 | pytest 测试装配和故障注入 | trial-passed（证据已生成） |
| RB-FX-005 | Playwright Python 浏览器验收 | trial-passed（证据已生成） |
| RB-FX-006 | uv 与 venv/pip 装配比较 | trial-passed（证据已生成） |
| RB-FX-007 | ECharts / Lightweight Charts / 原生 SVG | trial-passed（证据已生成） |

状态以 `docs/03-试验记录.md` 与 `evidence/` 中的实际结果为准。

## 与主仓库的关系

主仓库的正式入口是：

- `J:\asteria-riskbench\AGENTS.md`
- `J:\asteria-riskbench\docs\00-索引.md`
- `J:\asteria-riskbench\docs\implementation\TECH-工程技术选型、开源组件、调试与装配治理.md`
- `J:\asteria-riskbench\docs\implementation\TECH-STACK-RiskBench-v0.1-技术栈选型基线.md`
- `J:\asteria-riskbench\docs\implementation\COMPONENTS-RiskBench-v0.1-组件台账.md`

工厂只输出能力卡和证据；主仓库必须通过自己的任务计划和门禁后才可装配。

