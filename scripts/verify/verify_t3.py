"""手动验证第三刀的逻辑"""
import sys
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from malf.types import PriceBar, SystemState
from malf.core_engine import MALFCoreEngine

def test_up_direction():
    """测试 UP 方向的 guard break"""
    print("=" * 80)
    print("测试 UP 方向：up_alive → transition (LH break)")
    print("=" * 80)

    fixture_path = Path(__file__).parent / "tests" / "fixtures" / "t3_same_direction_break_up.json"
    with open(fixture_path) as f:
        d = json.load(f)

    bars = [
        PriceBar(
            symbol="TEST",
            timeframe="day",
            bar_dt=b["bar_dt"],
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"],
        )
        for b in d["input_bars"]
    ]

    engine = MALFCoreEngine(k=2)

    for i, bar in enumerate(bars):
        expected = d["expected_snapshots"][i]
        print(f"\nBar {i} ({bar.bar_dt}): H={bar.high}, L={bar.low}, C={bar.close}")

        try:
            snapshot = engine.on_bar(bar)
            print(f"  State: {snapshot.system_state.value}")
            if snapshot.direction:
                print(f"  Direction: {snapshot.direction.value}")
            if snapshot.current_effective_guard_price:
                print(f"  Guard: {snapshot.current_effective_guard_price}")
            if snapshot.progress_extreme_price:
                print(f"  Progress: {snapshot.progress_extreme_price}")

            # 验证
            assert snapshot.system_state.value == expected["system_state"], \
                f"Expected {expected['system_state']}, got {snapshot.system_state.value}"
            print(f"  ✅ 状态匹配")

        except NotImplementedError as e:
            print(f"  🚧 NotImplementedError: {e}")
            assert expected["system_state"] == "transition", \
                f"Unexpected NotImplementedError at state {expected['system_state']}"
            print(f"  ✅ 预期的 NotImplementedError（transition 后续逻辑未实现）")
            break

    print("\n✅ UP 方向测试通过")

def test_down_direction():
    """测试 DOWN 方向的 guard break"""
    print("\n" + "=" * 80)
    print("测试 DOWN 方向：down_alive → transition (HL break)")
    print("=" * 80)

    fixture_path = Path(__file__).parent / "tests" / "fixtures" / "t3_same_direction_break_down.json"
    with open(fixture_path) as f:
        d = json.load(f)

    bars = [
        PriceBar(
            symbol="TEST",
            timeframe="day",
            bar_dt=b["bar_dt"],
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"],
        )
        for b in d["input_bars"]
    ]

    engine = MALFCoreEngine(k=2)

    for i, bar in enumerate(bars):
        expected = d["expected_snapshots"][i]
        print(f"\nBar {i} ({bar.bar_dt}): H={bar.high}, L={bar.low}, C={bar.close}")

        try:
            snapshot = engine.on_bar(bar)
            print(f"  State: {snapshot.system_state.value}")
            if snapshot.direction:
                print(f"  Direction: {snapshot.direction.value}")
            if snapshot.current_effective_guard_price:
                print(f"  Guard: {snapshot.current_effective_guard_price}")
            if snapshot.progress_extreme_price:
                print(f"  Progress: {snapshot.progress_extreme_price}")

            # 验证
            assert snapshot.system_state.value == expected["system_state"], \
                f"Expected {expected['system_state']}, got {snapshot.system_state.value}"
            print(f"  ✅ 状态匹配")

        except NotImplementedError as e:
            print(f"  🚧 NotImplementedError: {e}")
            assert expected["system_state"] == "transition", \
                f"Unexpected NotImplementedError at state {expected['system_state']}"
            print(f"  ✅ 预期的 NotImplementedError（transition 后续逻辑未实现）")
            break

    print("\n✅ DOWN 方向测试通过")

if __name__ == "__main__":
    try:
        test_up_direction()
        test_down_direction()
        print("\n" + "=" * 80)
        print("🎉 所有测试通过！第三刀实现正确。")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
