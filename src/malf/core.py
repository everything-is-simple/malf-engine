"""L1 Core：结构状态机（已废弃）。

⚠️ 此文件是历史占位符，真正的实现在 core_engine.py 的 MALFCoreEngine。
请使用：from malf.core_engine import MALFCoreEngine

保留此文件仅用于向后兼容和文档追溯。
"""

from malf.core_engine import MALFCoreEngine


class CoreEngine(MALFCoreEngine):
    """已废弃：请直接使用 MALFCoreEngine。

    此类为历史兼容性而保留，直接继承自 MALFCoreEngine。
    新代码应导入：from malf.core_engine import MALFCoreEngine
    """

    def __init__(self, k: int = 2) -> None:
        super().__init__(k=k)
