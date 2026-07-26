"""验证修复后的 T3 fixtures"""
import sys
sys.path.insert(0, 'src')

from malf.types import PriceBar
from malf.pivot_detection import detect_pivots

def verify_t3_up():
    print("="*80)
    print("验证 T3 UP fixture（修复后）")
    print("="*80)

    bars = [
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d00", open=98, high=99, low=96, close=97),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d01", open=97, high=98, low=95, close=96),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d02", open=96, high=100, low=95, close=98),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d03", open=99, high=102, low=96, close=99),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d04", open=99, high=99, low=94, close=95),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d05", open=95, high=98, low=95, close=97),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d06", open=97, high=104, low=96, close=103),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d07", open=103, high=103, low=95, close=98),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d08", open=98, high=99, low=94, close=96),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d09", open=96, high=98, low=90, close=92),
    ]

    pivots = detect_pivots(bars, k=2)

    print(f"\n检测到 {len(pivots)} 个 pivots:")
    for p in pivots:
        print(f"  {p.pivot_type.value} @ {p.extreme_bar_dt} (price={p.price}), confirmed @ {p.confirm_bar_dt}")

    # 验证预期
    expected = [
        ("H", "d03", 102, "d05"),
        ("L", "d04", 94, "d06"),
        ("H", "d06", 104, "d08"),
    ]

    assert len(pivots) == 3, f"Expected 3 pivots, got {len(pivots)}"

    for i, (exp_type, exp_extreme, exp_price, exp_confirm) in enumerate(expected):
        p = pivots[i]
        assert p.pivot_type.value == exp_type, f"Pivot {i}: expected type {exp_type}, got {p.pivot_type.value}"
        assert p.extreme_bar_dt == exp_extreme, f"Pivot {i}: expected extreme {exp_extreme}, got {p.extreme_bar_dt}"
        assert p.price == exp_price, f"Pivot {i}: expected price {exp_price}, got {p.price}"
        assert p.confirm_bar_dt == exp_confirm, f"Pivot {i}: expected confirm {exp_confirm}, got {p.confirm_bar_dt}"

    print("\n[OK] T3 UP fixture 验证通过!")

def verify_t3_down():
    print("\n" + "="*80)
    print("验证 T3 DOWN fixture（修复后）")
    print("="*80)

    bars = [
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d00", open=102, high=104, low=101, close=103),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d01", open=103, high=105, low=102, close=104),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d02", open=104, high=104, low=100, close=102),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d03", open=102, high=102, low=98, close=101),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d04", open=101, high=108, low=101, close=105),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d05", open=105, high=105, low=100, close=101),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d06", open=101, high=101, low=90, close=92),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d07", open=92, high=100, low=94, close=96),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d08", open=96, high=101, low=95, close=98),
        PriceBar(symbol="TEST", timeframe="day", bar_dt="d09", open=98, high=110, low=104, close=108),
    ]

    pivots = detect_pivots(bars, k=2)

    print(f"\n检测到 {len(pivots)} 个 pivots:")
    for p in pivots:
        print(f"  {p.pivot_type.value} @ {p.extreme_bar_dt} (price={p.price}), confirmed @ {p.confirm_bar_dt}")

    # 验证预期
    expected = [
        ("L", "d03", 98, "d05"),
        ("H", "d04", 108, "d06"),
        ("L", "d06", 90, "d08"),
    ]

    assert len(pivots) == 3, f"Expected 3 pivots, got {len(pivots)}"

    for i, (exp_type, exp_extreme, exp_price, exp_confirm) in enumerate(expected):
        p = pivots[i]
        assert p.pivot_type.value == exp_type, f"Pivot {i}: expected type {exp_type}, got {p.pivot_type.value}"
        assert p.extreme_bar_dt == exp_extreme, f"Pivot {i}: expected extreme {exp_extreme}, got {p.extreme_bar_dt}"
        assert p.price == exp_price, f"Pivot {i}: expected price {exp_price}, got {p.price}"
        assert p.confirm_bar_dt == exp_confirm, f"Pivot {i}: expected confirm {exp_confirm}, got {p.confirm_bar_dt}"

    print("\n[OK] T3 DOWN fixture 验证通过!")

if __name__ == "__main__":
    try:
        verify_t3_up()
        verify_t3_down()
        print("\n" + "="*80)
        print("[SUCCESS] 所有 T3 fixtures 验证通过!")
        print("="*80)
    except Exception as e:
        print(f"\n[FAIL] 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
