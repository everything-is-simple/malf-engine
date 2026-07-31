"""
V1: 真实数据流水线验证

目标：
- 证明引擎能在完整历史数据上跑通
- 产出完整 snapshot 序列
- 记录统计信息和异常

数据集：
- 510300, 510500, 159915, 512880, 513100（TDX 日线）

产出：
- var/published/{symbol}/D/snapshots.jsonl
- 控制台日志（进度、状态转换、异常）
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tdx_reader import load_tdx_daily_bars

from malf.core_engine import MALFCoreEngine
from malf.lifespan_engine import LifespanEngine
from malf.rank_engine import RankEngine
from malf.structural_position_engine import StructuralPositionEngine
from malf.service_engine import build_wave_structural_snapshot, determine_usage, generate_reason_codes
from malf.persistence import serialize_snapshot, calculate_lineage_hash, persist_snapshot
from malf.version import CORE_RULE_VERSION, RANGE_RULE_VERSION, PIVOT_DETECTION_RULE_VERSION
from malf.types import (
    PriceBar,
    CoreStateSnapshot,
    SystemState,
    WaveCoreState,
    Direction,
)


class V1PipelineStats:
    """流水线统计信息"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

        self.total_bars = 0
        self.success_bars = 0
        self.error_bars = 0
        self.errors: List[dict] = []

        # 状态转换统计
        self.state_transitions: List[tuple] = []
        self.last_system_state: Optional[SystemState] = None

        # Wave 统计
        self.waves_initialized = 0
        self.waves_up = 0
        self.waves_down = 0

        # Range 统计
        self.ranges_born = 0
        self.ranges_resolved = 0

        # Usage 统计
        self.usage_rejected = 0
        self.usage_research_only = 0
        self.usage_verification_only = 0
        self.usage_operational = 0

    def record_bar(self, bar_index: int, bar_dt: str, core: CoreStateSnapshot, usage: str):
        """记录 bar 处理结果"""
        self.success_bars += 1

        # 状态转换
        if core.system_state != self.last_system_state:
            self.state_transitions.append((
                bar_index,
                bar_dt,
                self.last_system_state,
                core.system_state
            ))
            self.last_system_state = core.system_state

        # Wave 统计
        if core.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
            if core.direction == Direction.UP and bar_index > 0:
                # 检查是否是新 wave
                pass

        # Usage 统计
        if usage == "rejected":
            self.usage_rejected += 1
        elif usage == "research_only":
            self.usage_research_only += 1
        elif usage == "verification_only":
            self.usage_verification_only += 1
        elif usage == "operational":
            self.usage_operational += 1

    def record_error(self, bar_index: int, bar_dt: str, error: Exception):
        """记录错误"""
        self.error_bars += 1
        self.errors.append({
            "bar_index": bar_index,
            "bar_dt": bar_dt,
            "error": str(error),
            "error_type": type(error).__name__,
        })

    def print_progress(self, bar_index: int, bar_dt: str, system_state: SystemState):
        """打印进度（每100根打印一次）"""
        if bar_index % 100 == 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            bars_per_sec = bar_index / elapsed if elapsed > 0 else 0
            print(f"  [{bar_index:4d}] {bar_dt} | {system_state.value:15s} | "
                  f"{bars_per_sec:.1f} bars/s")

    def finalize(self):
        """完成统计"""
        self.end_time = datetime.now()

    def print_summary(self):
        """打印摘要"""
        elapsed = (self.end_time - self.start_time).total_seconds()

        print("\n" + "=" * 80)
        print(f"V1 Pipeline Summary - {self.symbol}")
        print("=" * 80)
        print(f"\nTime:")
        print(f"  Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  End:   {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Elapsed: {elapsed:.1f} seconds")

        print(f"\nBars:")
        print(f"  Total:   {self.total_bars}")
        print(f"  Success: {self.success_bars} ({self.success_bars/self.total_bars*100:.1f}%)")
        print(f"  Errors:  {self.error_bars}")

        print(f"\nState Transitions:")
        for bar_idx, bar_dt, from_state, to_state in self.state_transitions[:10]:
            from_str = from_state.value if from_state else "None"
            print(f"  [{bar_idx:4d}] {bar_dt}: {from_str:15s} → {to_state.value}")
        if len(self.state_transitions) > 10:
            print(f"  ... ({len(self.state_transitions) - 10} more transitions)")

        print(f"\nUsage Distribution:")
        print(f"  rejected:            {self.usage_rejected:4d} ({self.usage_rejected/self.success_bars*100:.1f}%)")
        print(f"  research_only:       {self.usage_research_only:4d} ({self.usage_research_only/self.success_bars*100:.1f}%)")
        print(f"  verification_only:   {self.usage_verification_only:4d} ({self.usage_verification_only/self.success_bars*100:.1f}%)")
        print(f"  operational:         {self.usage_operational:4d} ({self.usage_operational/self.success_bars*100:.1f}%)")

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for err in self.errors[:5]:
                print(f"  [{err['bar_index']:4d}] {err['bar_dt']}: {err['error_type']}")
                print(f"    {err['error']}")
            if len(self.errors) > 5:
                print(f"  ... ({len(self.errors) - 5} more errors)")

        print()


def run_single_symbol(
    symbol: str,
    timeframe: str = "D",
    tdx_data_path: str = "/sessions/youthful-friendly-volta/mnt/new_tdx64",
    base_path: str = "var",
    market: str = "sh"
) -> V1PipelineStats:
    """运行单个标的的流水线"""

    print(f"\n{'=' * 80}")
    print(f"Processing {symbol} ({market.upper()} {timeframe})")
    print(f"{'=' * 80}\n")

    stats = V1PipelineStats(symbol)

    # 1. 加载数据
    print(f"Loading TDX data...")
    try:
        bars = load_tdx_daily_bars(symbol, tdx_data_path=tdx_data_path, market=market)
        stats.total_bars = len(bars)
        print(f"  Loaded {len(bars)} bars")
        print(f"  Date range: {bars[0].bar_dt} ~ {bars[-1].bar_dt}")
    except Exception as e:
        print(f"  ERROR: Failed to load data: {e}")
        stats.finalize()
        return stats

    # 2. 初始化引擎
    print(f"\nInitializing engines...")

    # 构建 rule_versions 字典
    rule_versions = {
        "core": CORE_RULE_VERSION,
        "range": RANGE_RULE_VERSION,
        "pivot_detection": PIVOT_DETECTION_RULE_VERSION,
    }

    core_engine = MALFCoreEngine(k=2)
    lifespan_engine = LifespanEngine()
    rank_engine = RankEngine()
    structural_position_engine = StructuralPositionEngine(
        same_dir_threshold=0.10,
        cross_threshold=0.15
    )
    print(f"  All engines initialized")

    # 3. 逐 bar 推进
    print(f"\nProcessing bars...")
    print(f"  {'[BAR]':<6} {'DATE':<12} {'STATE':<15} {'SPEED'}")
    print(f"  {'-' * 60}")

    for i, bar in enumerate(bars):
        try:
            # Core 层
            core_snapshot = core_engine.on_bar(bar)

            # 简化版本：只产出 Core snapshot，不集成其他层
            # TODO: 集成 Range, Lifespan, Structural Position 层

            # 判定 usage（简化版本）
            usage = determine_usage(
                core=core_snapshot,
                wave_lifespan=None,
                range_lifespan=None,
                p1=None,
                p2=None,
                p3=None,
                p4=None,
                input_integrity_passed=True,
                peer_sample_sufficient=False,  # 简化：假设 peer_sample 不足
                data_stale=False,
            )

            # 生成 reason_codes（简化版本）
            reason_codes = generate_reason_codes(
                core=core_snapshot,
                wave_lifespan=None,
                range_lifespan=None,
                p1=None,
                p2=None,
                p3=None,
                p4=None,
                active_range=None,
                input_integrity_passed=True,
                peer_sample_sufficient=False,
                data_stale=False,
                operational_enabled=False,
            )

            # 组装 snapshot
            snapshot = build_wave_structural_snapshot(
                symbol=symbol,
                timeframe=timeframe,
                bar_dt=bar.bar_dt,
                bar_index=i,
                core=core_snapshot,
                active_range=None,
                wave_lifespan=None,
                range_lifespan=None,
                p1=None,
                p2=None,
                p3=None,
                p4=None,
                rule_versions=rule_versions,
                lineage_hash=None,  # TODO: 计算 lineage_hash
                input_integrity_passed=True,
                peer_sample_sufficient=False,
                data_stale=False,
                operational_enabled=False,
            )

            # 持久化（TODO: 实现）
            # persist_snapshot(snapshot, base_path)

            # 记录统计
            stats.record_bar(i, bar.bar_dt, core_snapshot, usage)

            # 打印进度
            stats.print_progress(i, bar.bar_dt, core_snapshot.system_state)

        except Exception as e:
            stats.record_error(i, bar.bar_dt, e)
            print(f"  ERROR at bar {i} ({bar.bar_dt}): {e}")
            import traceback
            traceback.print_exc()

            # 暂时不中断，继续处理下一根 bar
            # 如果错误率太高，考虑提前终止
            if stats.error_bars > 10:
                print(f"\n  Too many errors ({stats.error_bars}), aborting...")
                break

    # 4. 完成
    stats.finalize()
    stats.print_summary()

    return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="V1 Real Data Pipeline")
    parser.add_argument("--symbol", type=str, default="510300", help="Symbol to process")
    parser.add_argument("--market", type=str, default="sh", help="Market (sh/sz)")
    parser.add_argument("--timeframe", type=str, default="D", help="Timeframe")
    parser.add_argument("--tdx-data-path", type=str,
                        default="/sessions/youthful-friendly-volta/mnt/new_tdx64",
                        help="TDX data directory")
    parser.add_argument("--base-path", type=str, default="var", help="Output directory")

    args = parser.parse_args()

    print(f"\n{'#' * 80}")
    print(f"# V1 Real Data Pipeline - MALF Engine Validation")
    print(f"{'#' * 80}")

    stats = run_single_symbol(
        symbol=args.symbol,
        timeframe=args.timeframe,
        tdx_data_path=args.tdx_data_path,
        base_path=args.base_path,
        market=args.market,
    )

    # 返回状态码
    if stats.error_bars > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
