"""
Unit tests for guard break detection.
第三刀：测试 guard break 逻辑
"""

import pytest
from malf.types import PriceBar, SystemState, Direction
from malf.core_engine import MALFCoreEngine


class TestGuardBreakDetection:
    """测试 guard break 检测逻辑"""

    def test_check_guard_break_up_alive_no_break(self):
        """
        Given: up_alive, guard=96
        When: bar.close=98 > guard (未突破)
        Then: 状态保持 up_alive
        """
        engine = MALFCoreEngine(k=2)

        # 构造 up_alive 状态序列（复用第一刀已验证的序列）
        bars = [
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d00", open=100, high=102, low=99, close=101),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d01", open=101, high=105, low=100, close=104),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d02", open=104, high=110, low=103, close=108),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d03", open=108, high=107, low=104, close=105),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d04", open=105, high=106, low=102, close=103),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d05", open=103, high=104, low=96, close=98),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d06", open=98, high=101, low=97, close=100),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d07", open=100, high=103, low=98, close=102),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d08", open=102, high=108, low=101, close=107),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d09", open=107, high=114, low=106, close=112),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d10", open=112, high=111, low=108, close=109),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d11", open=109, high=110, low=106, close=108),
        ]

        for bar in bars:
            snapshot = engine.on_bar(bar)

        # 验证已进入 up_alive，guard=96
        assert snapshot.system_state == SystemState.UP_ALIVE
        assert snapshot.current_effective_guard_price == 96

        # 喂入未突破 guard 的 bar (close=98 > 96)
        bar_no_break = PriceBar(symbol="TEST", timeframe="day", bar_dt="d12", open=109, high=109, low=97, close=98)
        snapshot = engine.on_bar(bar_no_break)

        # 状态应保持 up_alive
        assert snapshot.system_state == SystemState.UP_ALIVE
        assert snapshot.current_effective_guard_price == 96

    def test_check_guard_break_up_alive_with_break(self):
        """
        Given: up_alive, guard=96
        When: bar.close=94 < guard (LH break)
        Then: system_state = transition（第四刀已实现）
        """
        engine = MALFCoreEngine(k=2)

        # 构造 up_alive 状态序列（复用第一刀已验证的序列）
        bars = [
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d00", open=100, high=102, low=99, close=101),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d01", open=101, high=105, low=100, close=104),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d02", open=104, high=110, low=103, close=108),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d03", open=108, high=107, low=104, close=105),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d04", open=105, high=106, low=102, close=103),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d05", open=103, high=104, low=96, close=98),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d06", open=98, high=101, low=97, close=100),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d07", open=100, high=103, low=98, close=102),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d08", open=102, high=108, low=101, close=107),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d09", open=107, high=114, low=106, close=112),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d10", open=112, high=111, low=108, close=109),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d11", open=109, high=110, low=106, close=108),
        ]

        for bar in bars:
            snapshot = engine.on_bar(bar)

        # 验证已进入 up_alive，guard=96, progress=114
        assert snapshot.system_state == SystemState.UP_ALIVE
        assert snapshot.current_effective_guard_price == 96
        assert snapshot.progress_extreme_price == 114

        # 喂入 LH break bar (close=94 < 96)
        bar_break = PriceBar(symbol="TEST", timeframe="day", bar_dt="d12", open=100, high=100, low=90, close=94)
        snapshot = engine.on_bar(bar_break)

        # 验证进入 transition（第四刀已实现）
        assert snapshot.system_state == SystemState.TRANSITION
        assert snapshot.transition_boundary_high == 114  # old final HH
        assert snapshot.transition_boundary_low == 96    # broken guard

    def test_check_guard_break_down_alive_no_break(self):
        """
        Given: down_alive, guard=115
        When: bar.close=113 < guard (未突破)
        Then: 状态保持 down_alive
        """
        engine = MALFCoreEngine(k=2)

        # 构造 down_alive 状态序列（复用第二刀已验证的序列）
        bars = [
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d00", open=110, high=112, low=108, close=111),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d01", open=111, high=113, low=109, close=112),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d02", open=112, high=114, low=100, close=102),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d03", open=102, high=110, low=101, close=108),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d04", open=108, high=112, low=107, close=111),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d05", open=111, high=115, low=110, close=113),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d06", open=113, high=114, low=108, close=109),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d07", open=109, high=110, low=95, close=96),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d08", open=96, high=100, low=96, close=99),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d09", open=99, high=102, low=97, close=101),
        ]

        for bar in bars:
            snapshot = engine.on_bar(bar)

        # 验证已进入 down_alive，guard=115
        assert snapshot.system_state == SystemState.DOWN_ALIVE
        assert snapshot.current_effective_guard_price == 115

        # 喂入未突破 guard 的 bar (close=113 < 115)
        bar_no_break = PriceBar(symbol="TEST", timeframe="day", bar_dt="d10", open=100, high=113, low=98, close=113)
        snapshot = engine.on_bar(bar_no_break)

        # 状态应保持 down_alive
        assert snapshot.system_state == SystemState.DOWN_ALIVE
        assert snapshot.current_effective_guard_price == 115

    def test_check_guard_break_down_alive_with_break(self):
        """
        Given: down_alive, guard=115
        When: bar.close=117 > guard (HL break)
        Then: system_state = transition（第四刀已实现）
        """
        engine = MALFCoreEngine(k=2)

        # 构造 down_alive 状态序列（复用第二刀已验证的序列）
        bars = [
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d00", open=110, high=112, low=108, close=111),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d01", open=111, high=113, low=109, close=112),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d02", open=112, high=114, low=100, close=102),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d03", open=102, high=110, low=101, close=108),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d04", open=108, high=112, low=107, close=111),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d05", open=111, high=115, low=110, close=113),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d06", open=113, high=114, low=108, close=109),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d07", open=109, high=110, low=95, close=96),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d08", open=96, high=100, low=96, close=99),
            PriceBar(symbol="TEST", timeframe="day", bar_dt="d09", open=99, high=102, low=97, close=101),
        ]

        for bar in bars:
            snapshot = engine.on_bar(bar)

        # 验证已进入 down_alive，guard=115, progress=95
        assert snapshot.system_state == SystemState.DOWN_ALIVE
        assert snapshot.current_effective_guard_price == 115
        assert snapshot.progress_extreme_price == 95

        # 喂入 HL break bar (close=117 > 115)
        bar_break = PriceBar(symbol="TEST", timeframe="day", bar_dt="d10", open=100, high=120, low=100, close=117)
        snapshot = engine.on_bar(bar_break)

        # 验证进入 transition（第四刀已实现）
        assert snapshot.system_state == SystemState.TRANSITION
        assert snapshot.transition_boundary_high == 115  # broken guard
        assert snapshot.transition_boundary_low == 95    # old final LL
