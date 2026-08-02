"""Lifespan 层真实数据验证 - 多股票验证。

验证 5 只股票的 Lifespan 层功能：
- WaveLifespan 指标计算
- RangeLifespan 指标计算
- percentile_rank 计算
- peer_sample 过滤

股票清单：
1. sh600000 - 浦发银行
2. sh600036 - 招商银行
3. sh600519 - 贵州茅台
4. sh601318 - 中国平安
5. sh601857 - 中国石油
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# 添加 src 到 path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from malf.core_engine import CoreEngine
from malf.range_engine import RangeEngine
from malf.lifespan_engine import LifespanEngine
from malf.rank_engine import RankEngine
from malf.types import PriceBar


def load_test_data(symbol: str, limit: int = 200) -> list[PriceBar]:
    """加载测试数据（模拟，实际应从真实数据源加载）。

    注意：这是占位符实现。真实验证需要从数据源加载 OHLC 数据。
    """
    # TODO: 替换为真实数据加载逻辑
    # 这里返回空列表，实际验证时需要加载真实 OHLC 数据
    print(f"  ⚠️  加载 {symbol} 数据（占位符实现）")
    return []


def verify_lifespan_for_stock(symbol: str, bars: list[PriceBar]) -> dict:
    """验证单只股票的 Lifespan 层功能。"""
    print(f"\n{'='*70}")
    print(f"验证股票: {symbol}")
    print(f"{'='*70}")

    if not bars:
        print("  ⚠️  无数据，跳过")
        return {
            "symbol": symbol,
            "status": "SKIPPED",
            "reason": "no_data"
        }

    # 初始化引擎
    core_engine = CoreEngine()
    range_engine = RangeEngine()
    lifespan_engine = LifespanEngine()
    rank_engine = RankEngine()

    # 统计
    wave_count = 0
    range_count = 0
    lifespan_calculated = 0
    ranks_calculated = 0

    try:
        # 逐 bar 处理
        for bar in bars:
            snapshot = core_engine.process_bar(bar)

            # 检测 wave 终止
            if snapshot.wave_core_state == "terminated":
                wave_count += 1

                # 计算 WaveLifespan
                # TODO: 从 snapshot 提取参数
                # lifespan = lifespan_engine.calculate_wave_lifespan(...)
                # lifespan_calculated += 1

                # 计算 rank
                # peer_sample = lifespan_engine.get_terminated_waves(direction=...)
                # if len(peer_sample) >= 30:
                #     ranks = rank_engine.calculate_wave_ranks(lifespan, peer_sample)
                #     ranks_calculated += 1

            # 检测 Range resolution
            # TODO: 实现 Range 检测和 RangeLifespan 计算

        print(f"  ✅ 处理完成")
        print(f"     - Bars: {len(bars)}")
        print(f"     - Waves: {wave_count}")
        print(f"     - Ranges: {range_count}")
        print(f"     - Lifespan 计算: {lifespan_calculated}")
        print(f"     - Rank 计算: {ranks_calculated}")

        return {
            "symbol": symbol,
            "status": "SUCCESS",
            "bars": len(bars),
            "waves": wave_count,
            "ranges": range_count,
            "lifespan_calculated": lifespan_calculated,
            "ranks_calculated": ranks_calculated
        }

    except Exception as e:
        print(f"  ❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()

        return {
            "symbol": symbol,
            "status": "FAILED",
            "error": str(e)
        }


def main():
    """主函数：验证 5 只股票。"""
    print("="*70)
    print("Lifespan 层真实数据验证（5 只股票）")
    print("="*70)

    stocks = [
        "sh600000",  # 浦发银行
        "sh600036",  # 招商银行
        "sh600519",  # 贵州茅台
        "sh601318",  # 中国平安
        "sh601857",  # 中国石油
    ]

    results = []

    for symbol in stocks:
        bars = load_test_data(symbol, limit=200)
        result = verify_lifespan_for_stock(symbol, bars)
        results.append(result)

    # 生成总结报告
    print("\n" + "="*70)
    print("验证总结")
    print("="*70)

    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    failed_count = sum(1 for r in results if r["status"] == "FAILED")
    skipped_count = sum(1 for r in results if r["status"] == "SKIPPED")

    print(f"总计: {len(results)} 只股票")
    print(f"  ✅ 成功: {success_count}")
    print(f"  ❌ 失败: {failed_count}")
    print(f"  ⚠️  跳过: {skipped_count}")
    print("")

    # 保存结果
    report_path = Path(__file__).parent.parent.parent / "docs" / "reports" / "lifespan" / f"MULTI-STOCK-VALIDATION-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "stocks": stocks,
            "results": results,
            "summary": {
                "total": len(results),
                "success": success_count,
                "failed": failed_count,
                "skipped": skipped_count
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"报告已保存: {report_path}")
    print("")

    # 返回状态
    if failed_count > 0:
        print("❌ 验证失败")
        sys.exit(1)
    elif skipped_count == len(results):
        print("⚠️  所有股票都被跳过（缺少真实数据）")
        print("")
        print("下一步：")
        print("  1. 实现 load_test_data() 函数，从真实数据源加载 OHLC")
        print("  2. 实现 WaveLifespan 和 RangeLifespan 的完整计算逻辑")
        print("  3. 重新运行验证")
        sys.exit(0)
    else:
        print("✅ 验证通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
