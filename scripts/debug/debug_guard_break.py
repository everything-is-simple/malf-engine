"""调试 guard break 测试失败原因"""
import sys
sys.path.insert(0, 'src')

from malf.types import PriceBar, SystemState
from malf.core_engine import MALFCoreEngine
from malf.pivot_detection import detect_pivots

# 构造 up_alive 状态序列
bars = [
    PriceBar(symbol="TEST", timeframe="day", bar_dt="d00", open=100, high=100, low=95, close=98),
    PriceBar(symbol="TEST", timeframe="day", bar_dt="d01", open=102, high=102, low=96, close=99),
    PriceBar(symbol="TEST", timeframe="day", bar_dt="d02", open=99, high=99, low=94, close=95),
    PriceBar(symbol="TEST", timeframe="day", bar_dt="d03", open=98, high=98, low=95, close=97),
    PriceBar(symbol="TEST", timeframe="day", bar_dt="d04", open=104, high=104, low=96, close=103),
    PriceBar(symbol="TEST", timeframe="day", bar_dt="d05", open=100, high=100, low=95, close=98),
    PriceBar(symbol="TEST", timeframe="day", bar_dt="d06", open=99, high=99, low=94, close=96),
]

print("=" * 80)
print("调试 UP 方向序列")
print("=" * 80)

for i, bar in enumerate(bars):
    print(f"Bar {i} ({bar.bar_dt}): H={bar.high}, L={bar.low}, C={bar.close}")

print("\n检测 pivots:")
pivots = detect_pivots(bars, k=2)
for p in pivots:
    print(f"  {p.pivot_type.value} @ {p.extreme_bar_dt} (price={p.price}), confirmed @ {p.confirm_bar_dt}")

print(f"\n共检测到 {len(pivots)} 个 pivots")

if len(pivots) >= 3:
    print("\n预期: H0 @ d01, L1 @ d02, H2 @ d04")
    print(f"实际: {pivots[0].pivot_type.value} @ {pivots[0].extreme_bar_dt}, {pivots[1].pivot_type.value} @ {pivots[1].extreme_bar_dt}, {pivots[2].pivot_type.value} @ {pivots[2].extreme_bar_dt}")
else:
    print(f"\n⚠️ 只检测到 {len(pivots)} 个 pivots，少于预期的 3 个")

print("\n逐 bar 推进引擎:")
engine = MALFCoreEngine(k=2)
for i, bar in enumerate(bars):
    snapshot = engine.on_bar(bar)
    print(f"Bar {i}: state={snapshot.system_state.value}, guard={snapshot.current_effective_guard_price}")

print(f"\n最终状态: {snapshot.system_state.value}")
if snapshot.system_state != SystemState.UP_ALIVE:
    print("❌ 未进入 up_alive 状态")
else:
    print("✅ 进入 up_alive 状态")
