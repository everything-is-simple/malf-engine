"""L1 Core：结构状态机（骨架占位）。

⚠️ 现在是空壳。引擎逻辑等 golden fixture 的预期输出人肉推导完成后再写（TDD RED→GREEN）。
第一刀纵切：uninitialized → up_alive（spec §2，覆盖 S1→S9 + pivot k=2 + guard + break + new wave）。

不在此处提前定 CoreStateSnapshot 的字段形态（含 runtime_fingerprint）——
那是写代码时该由测试验证的，不是现在拿直觉拍死的。见 docs/BUILD-PLAN.md。
"""


class CoreEngine:
    """占位。第一个 golden fixture 就绪后填实。"""

    def __init__(self) -> None:
        raise NotImplementedError(
            "CoreEngine 尚未实现。先推 golden fixture 预期输出，再进 TDD GREEN。"
        )
