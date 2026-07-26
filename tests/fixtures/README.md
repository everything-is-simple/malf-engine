# golden fixtures

每个 fixture 是一段人工构造的最小 OHLC 序列（10–20 根 bar），专门触发一个特定状态转换，
配一份**人肉推导**的预期输出（逐 bar 的 CoreStateSnapshot）。

## 铁律

- 预期输出必须**人肉按 spec §2 推导**，绝不能用待测的 CoreEngine 生成——否则等于用待测代码判自己对错（TDD 铁律）。
- 一个 fixture 只测一条转换路径，序列尽量短、意图尽量单一。
- fixture 文件名 = 它测的转换，如 `uninitialized_to_up_alive.json`。

## 当前

第一条 `uninitialized → up_alive`（H0→L1→H2>H0）的预期输出正在与人一起逐根推导中，
推完存为 `uninitialized_to_up_alive.json`。
