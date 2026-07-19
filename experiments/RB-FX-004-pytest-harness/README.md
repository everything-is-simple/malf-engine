# RB-FX-004 — pytest harness

pytest 在本工厂同时承载 fixture、参数化、异常断言、故障注入（monkeypatch）和 HTTP 合同测试。机器证据由根目录 `run_factory_trials.py` 生成；另用一个故意失败的临时用例验证非零退出码，失败文件不会提交。
