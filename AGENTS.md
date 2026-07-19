# AGENTS.md — RiskBench 组件实验工厂操作约束

> 这是 `J:\asteria-riskbench-factory` 的独立、可删除、可重建实验仓库。
> 它不是 `J:\asteria-riskbench` 的业务项目，也不自动授权主系统装配。

## 1. 实验工厂身份

- 目的：对 RiskBench 候选技术和开源组件做隔离、可重复、可审计的最小实验。
- 主仓库：`J:\asteria-riskbench`。
- 工厂目录：`J:\asteria-riskbench-factory`。
- 当前状态：候选实验工厂；试验通过不等于正式选型。
- 工厂可以安装自己的开发依赖，但不得修改主仓库业务结构。

## 2. 开工入口

每次开工按顺序阅读：

1. 本文件；
2. `docs/00-实验索引.md`；
3. `docs/01-工厂运行合同.md`；
4. `docs/02-候选组件矩阵.md`；
5. 当前实验目录的 README、测试和证据要求。

## 3. 参考目录安全边界

下列目录只读、禁止复制迁移、禁止写入缓存或测试产物：

- `J:\asteria-trading-lab`
- `J:\asteria-trading-labs-data`
- `J:\asteria-trading-labs-Definitive-validated`
- `J:\asteria-trading-labs-reference`
- `J:\malf-data`
- `J:\malf-system-history`
- `J:\tdx_offline_Data`
- 数据权威源 `J:\new_tdx64\vipdoc`

首批实验必须使用工厂自造 fixture；不得读取真实 TDX/MALF 目录来“证明”组件可用。

## 4. 状态语义

- `candidate`：只登记，未实验。
- `trial-running`：实验正在进行。
- `trial-passed`：实验通过了定义的能力卡，但尚未进入主系统。
- `selected`：主仓库技术栈基线正式批准采用。
- `deferred`：当前 v0.1 不装配，未来触发条件明确。
- `rejected`：不满足约束或证据不足。

任何文件不得把 `trial-passed` 写成 `selected`。

## 5. 禁止事项

- 不修改主仓库 `src/`、`tests/`、配置或 Git 历史；
- 不向参考目录或 `J:\new_tdx64\vipdoc` 写入；
- 不复制真实数据到工厂；
- 不把实验代码直接复制进主仓库；
- 不以实验通过代替主仓库任务计划和批准门禁；
- 不引入遥测、CDN、远程运行时数据或外部网络依赖到 Viewer smoke test；
- 不在实验中启用 `operational`、自动重算、scheduler 或 watcher。

## 6. 证据要求

每次实验至少记录：实验 ID、日期、环境、候选版本、许可证、安装命令、输入、输出、测试命令、退出码、文件哈希、失败/残留、结论和主系统装配建议。

## 7. 恢复规则

中断后先读本文件和 `docs/00-实验索引.md`，再根据实验状态继续。若证据不完整，状态只能保持 `trial-running` 或 `candidate`，不得猜测为通过。
