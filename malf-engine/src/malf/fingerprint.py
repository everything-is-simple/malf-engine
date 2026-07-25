"""runtime_fingerprint —— replay 审计用的运行环境指纹。

【填洞 L4-6，形态在此由代码定，回补规格 §7 前的验证实现】

设计决定：runtime_fingerprint 记录 Python 版本 + 平台，随每条 CoreStateSnapshot 存，
但 **不进 lineage_hash 的计算输入**。
- 进 hash 的坏处：同一份数据换台机器（Python 小版本不同）算出的哈希就不同，
  反而没法跨机器比对"算法逻辑是否一致"。
- 不进 hash 的做法：当独立审计元数据存着，replay 校验时单独比对这一栏——
  环境变了看得见，但不污染"逻辑指纹"（lineage_hash）。

依赖：仅 stdlib（sys, platform）。
"""

from __future__ import annotations

import platform
import sys


def runtime_fingerprint() -> str:
    """返回当前运行环境指纹，形如 'py3.10.19|win32|CPython'。

    分量：Python 版本（major.minor.micro）+ sys.platform + 解释器实现名。
    只用于审计比对，不参与 lineage_hash（见模块 docstring）。
    """
    v = sys.version_info
    return f"py{v.major}.{v.minor}.{v.micro}|{sys.platform}|{platform.python_implementation()}"
