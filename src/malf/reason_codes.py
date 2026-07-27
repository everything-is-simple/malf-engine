"""
MALF v2.1 Service 层 - Reason Codes 枚举

根据规格 MALF_05_Service_v2_1 §6 和 §8 定义所有 reason codes。
每个 reason code 说明某个字段为 None 的原因。
"""

from typing import Final


class ReasonCode:
    """
    Reason codes 枚举（规格 §6 铁律 6 和 §8 失败模式）

    所有为 None 的字段必须在 reason_codes 中说明原因。
    """

    # ========== Core 层 ==========
    UNINITIALIZED: Final[str] = "uninitialized"
    """数据不足，尚未初始化。bar 序列不足 k+2 根，尚未检测到 pivot"""

    TRANSITION_ACTIVE: Final[str] = "transition_active"
    """Transition 期间，某些 Core 字段为 None（如 bar_count）"""

    WAVE_ALIVE: Final[str] = "wave_alive"
    """当前 wave 未终止，Lifespan rank 不可用"""

    # ========== 输入层 ==========
    INPUT_INTEGRITY_FAILURE: Final[str] = "input_integrity_failure"
    """输入完整性失败（G0）。结构性坏记录，整只标的拒绝"""

    DATA_STALE: Final[str] = "data_stale"
    """数据过期。最后 bar 的日期距离当前日期超过阈值"""

    # ========== Lifespan 层 ==========
    PEER_SAMPLE_INSUFFICIENT: Final[str] = "peer_sample_insufficient"
    """样本不足。同方向已终止 Wave 不足 30 个"""

    # ========== Structural Position 层 ==========
    SAME_DIR_PEERS_ABSENT: Final[str] = "same_dir_peers_absent"
    """同向对照不存在。W-1, W-2, W-3 中没有与 W0 同方向的波"""

    CROSS_DIR_PEERS_ABSENT: Final[str] = "cross_dir_peers_absent"
    """反向对照不存在。W-1, W-2, W-3 中没有与 W0 反方向的波"""

    NO_PRIOR_WAVE: Final[str] = "no_prior_wave"
    """W-1 不存在。只有 W0（首次波），无历史波"""

    # ========== Range 层 ==========
    RANGE_ALIVE: Final[str] = "range_alive"
    """Range 未结束。当前在 transition 中，Range 尚未 resolution"""

    # ========== Service 层 ==========
    OPERATIONAL_DISABLED: Final[str] = "operational_disabled"
    """Operational 模式在 v0.1 禁用。需未来独立审批后方可启用"""


    @classmethod
    def all_codes(cls) -> list[str]:
        """返回所有 reason codes（用于验证）"""
        return [
            cls.UNINITIALIZED,
            cls.TRANSITION_ACTIVE,
            cls.WAVE_ALIVE,
            cls.INPUT_INTEGRITY_FAILURE,
            cls.DATA_STALE,
            cls.PEER_SAMPLE_INSUFFICIENT,
            cls.SAME_DIR_PEERS_ABSENT,
            cls.CROSS_DIR_PEERS_ABSENT,
            cls.NO_PRIOR_WAVE,
            cls.RANGE_ALIVE,
            cls.OPERATIONAL_DISABLED,
        ]


    @classmethod
    def validate(cls, code: str) -> bool:
        """验证 reason code 是否有效"""
        return code in cls.all_codes()
