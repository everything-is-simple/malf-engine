# RB-FX-006 — 包管理器比较

比较对象：

1. Python 标准库 `venv` + `pip`：系统内置、最保守、锁定和跨机缓存能力较弱；
2. Astral `uv`：快速解析、锁文件、项目/工具/Python 管理能力强，但应保持开发工具身份，不能成为 Viewer 运行时依赖。

通过标准：两种方式都能在工厂目录内创建可删除环境；`uv` 能生成锁文件并以 Python 3.10 执行测试；删除环境后可按锁定结果重建；最终生产运行命令不得依赖 `uv`。

机器实验由 `run_factory_trials.py` 执行并写入 `evidence/RB-FX-006-package-manager/result.json`。
