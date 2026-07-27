"""
V1.2: 完整 5 层集成流水线

实现策略：
1. 维护额外的状态追踪（wave/range 历史）
2. 检测事件触发 Lifespan 计算
3. 集成 Structural Position 层
4. 实现持久化和 lineage_hash
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dataclasses import asdict, replace
import json

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tdx_reader import load_tdx_daily_bars

from malf.core_engine import MALFCoreEngine
from malf.lifespan_engine import LifespanEngine
from malf.rank_engine import RankEngine
from malf.structural_position_engine import StructuralPositionEngine
from malf.service_engine import build_wave_structural_snapshot, determine_usage, generate_reason_codes
from malf.persistence import (
    serialize_snapshot,
    calculate_lineage_hash,
    ensure_var_directory,
    persist_snapshot,
)
from malf.version import CORE_RULE_VERSION, RANGE_RULE_VERSION, PIVOT_DETECTION_RULE_VERSION
from malf.types import (
    PriceBar,
    CoreStateSnapshot,
    SystemState,
    WaveCoreState,
    Direction,
    WaveLifespan,
    RangeLifespan,
    RangeResolutionType,
)


class WaveTracker:
    """追踪 wave 生命周期信息"""

    def __init__(self):
        self.wave_counter = 0
        self.current_wave_start_bar_dt: Optional[str] = None
        self.current_wave_start_price: Optional[int] = None
        self.current_wave_direction: Optional[Direction] = None
        self.current_wave_pivot_count = 0
        self.current_wave_new_count = 0

    def on_wave_initialized(self, snapshot: CoreStateSnapshot):
        """记录 wave 初始化"""
        self.wave_counter += 1
        self.current_wave_start_bar_dt = snapshot.bar_dt
        self.current_wave_direction = snapshot.direction

        # 初始化时的 guard 价格就是起始价格（L1 for UP, H1 for DOWN）
        self.current_wave_start_price = snapshot.current_effective_guard_price
        self.current_wave_pivot_count = 3  # 初始化原语固定 3 个 pivot
        self.current_wave_new_count = 0

    def on_progress_update(self):
        """记录 progress 更新（新 pivot 确认）"""
        self.current_wave_new_count += 1
        self.current_wave_pivot_count += 1

    def on_wave_terminated(self, snapshot: CoreStateSnapshot) -> dict:
        """Wave 终止，返回 lifespan 计算所需的信息"""
        wave_info = {
            "wave_id": f"{snapshot.symbol}_{snapshot.timeframe}_W{self.wave_counter}",
            "symbol": snapshot.symbol,
            "timeframe": snapshot.timeframe,
            "direction": self.current_wave_direction,
            "wave_start_bar_dt": self.current_wave_start_bar_dt,
            "wave_start_price": self.current_wave_start_price,
            "wave_end_bar_dt": snapshot.bar_dt,
            "wave_end_price": snapshot.progress_extreme_price,  # 前一根 bar 的 progress
            "span_bars": snapshot.bar_count if snapshot.bar_count else 0,
            "primitive_count": 3,  # 初始化原语固定为 3
            "pivot_count": self.current_wave_pivot_count,
            "new_count": self.current_wave_new_count,
            "no_new_span": 0,  # 简化：暂不计算
        }

        # 重置追踪状态
        self.current_wave_start_bar_dt = None
        self.current_wave_start_price = None
        self.current_wave_direction = None
        self.current_wave_pivot_count = 0
        self.current_wave_new_count = 0

        return wave_info


class RangeTracker:
    """追踪 range 生命周期信息"""

    def __init__(self):
        self.range_counter = 0
        self.current_range_start_bar_dt: Optional[str] = None
        self.current_range_start_bar_index: Optional[int] = None

    def on_range_born(self, snapshot: CoreStateSnapshot, bar_index: int):
        """记录 range 诞生"""
        self.range_counter += 1
        self.current_range_start_bar_dt = snapshot.range_birth_bar_dt
        self.current_range_start_bar_index = bar_index

    def on_range_resolved(self, snapshot: CoreStateSnapshot, bar_index: int) -> dict:
        """Range resolved，返回 lifespan 计算所需的信息"""
        span_bars = bar_index - self.current_range_start_bar_index if self.current_range_start_bar_index else 0

        # 解析 resolution_type
        resolution_type_enum = None
        if snapshot.range_resolution_type == "continuation":
            resolution_type_enum = RangeResolutionType.CONTINUATION
        elif snapshot.range_resolution_type == "reversal":
            resolution_type_enum = RangeResolutionType.REVERSAL

        range_info = {
            "range_id": f"{snapshot.symbol}_{snapshot.timeframe}_R{self.range_counter}",
            "symbol": snapshot.symbol,
            "timeframe": snapshot.timeframe,
            "range_type": resolution_type_enum,
            "range_start_bar_dt": self.current_range_start_bar_dt,
            "range_end_bar_dt": snapshot.range_resolution_bar_dt,
            "span_bars": span_bars,
            "evolution_count": snapshot.range_evolution_count,
            "replacement_count": snapshot.candidate_replacement_count,
            "resolution_distance": snapshot.range_resolution_distance if snapshot.range_resolution_distance else 0,
            "boundary_high_init": snapshot.range_boundary_init_high,
            "boundary_low_init": snapshot.range_boundary_init_low,
            "boundary_high_now": snapshot.range_boundary_now_high,
            "boundary_low_now": snapshot.range_boundary_now_low,
            "resolution_type": snapshot.range_resolution_type,
            "confirmation_pivot_extreme_price": snapshot.progress_extreme_price,  # 简化
        }

        # 重置追踪状态
        self.current_range_start_bar_dt = None
        self.current_range_start_bar_index = None

        return range_info


class IntegratedStats:
    """完整统计信息"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

        self.total_bars = 0
        self.success_bars = 0
        self.error_bars = 0
        self.errors: List[dict] = []

        # 状态转换
        self.state_transitions: List[tuple] = []
        self.last_system_state: Optional[SystemState] = None

        # Wave 统计
        self.waves_terminated = 0
        self.waves_up = 0
        self.waves_down = 0

        # Range 统计
        self.ranges_born = 0
        self.ranges_resolved = 0
        self.ranges_continuation = 0
        self.ranges_reversal = 0

        # Lifespan 统计
        self.wave_lifespan_calculated = 0
        self.wave_lifespan_with_rank = 0
        self.range_lifespan_calculated = 0

        # Structural Position 统计
        self.p1_generated = 0
        self.p2_generated = 0
        self.p3_generated = 0
        self.p4_generated = 0

        # Usage 统计
        self.usage_rejected = 0
        self.usage_research_only = 0
        self.usage_verification_only = 0
        self.usage_operational = 0

    def record_bar(
        self,
        bar_index: int,
        bar_dt: str,
        core: CoreStateSnapshot,
        usage: str,
        wave_lifespan: Optional[WaveLifespan] = None,
        range_lifespan: Optional[RangeLifespan] = None,
        has_p1: bool = False,
        has_p2: bool = False,
        has_p3: bool = False,
        has_p4: bool = False,
    ):
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

        # Usage 统计
        if usage == "rejected":
            self.usage_rejected += 1
        elif usage == "research_only":
            self.usage_research_only += 1
        elif usage == "verification_only":
            self.usage_verification_only += 1
        elif usage == "operational":
            self.usage_operational += 1

        # Wave lifespan
        if wave_lifespan is not None:
            self.wave_lifespan_calculated += 1
            self.waves_terminated += 1
            if wave_lifespan.direction == Direction.UP:
                self.waves_up += 1
            else:
                self.waves_down += 1
            if wave_lifespan.span_rank is not None:
                self.wave_lifespan_with_rank += 1

        # Range lifespan
        if range_lifespan is not None:
            self.range_lifespan_calculated += 1
            self.ranges_resolved += 1
            if range_lifespan.range_type == RangeResolutionType.CONTINUATION:
                self.ranges_continuation += 1
            elif range_lifespan.range_type == RangeResolutionType.REVERSAL:
                self.ranges_reversal += 1

        # Structural Position
        if has_p1:
            self.p1_generated += 1
        if has_p2:
            self.p2_generated += 1
        if has_p3:
            self.p3_generated += 1
        if has_p4:
            self.p4_generated += 1

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
        """打印进度"""
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
        print(f"V1.2 Full Integration Summary - {self.symbol}")
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

        print(f"\nWave Statistics:")
        print(f"  Terminated: {self.waves_terminated}")
        print(f"  UP:         {self.waves_up}")
        print(f"  DOWN:       {self.waves_down}")

        print(f"\nRange Statistics:")
        print(f"  Resolved:      {self.ranges_resolved}")
        print(f"  Continuation:  {self.ranges_continuation}")
        print(f"  Reversal:      {self.ranges_reversal}")

        print(f"\nLifespan Statistics:")
        print(f"  WaveLifespan calculated:  {self.wave_lifespan_calculated}")
        print(f"  WaveLifespan with rank:   {self.wave_lifespan_with_rank}")
        print(f"  RangeLifespan calculated: {self.range_lifespan_calculated}")

        print(f"\nStructural Position Statistics:")
        print(f"  P1 generated: {self.p1_generated}")
        print(f"  P2 generated: {self.p2_generated}")
        print(f"  P3 generated: {self.p3_generated}")
        print(f"  P4 generated: {self.p4_generated}")

        print(f"\nUsage Distribution:")
        total = self.success_bars if self.success_bars > 0 else 1
        print(f"  rejected:            {self.usage_rejected:4d} ({self.usage_rejected/total*100:.1f}%)")
        print(f"  research_only:       {self.usage_research_only:4d} ({self.usage_research_only/total*100:.1f}%)")
        print(f"  verification_only:   {self.usage_verification_only:4d} ({self.usage_verification_only/total*100:.1f}%)")
        print(f"  operational:         {self.usage_operational:4d} ({self.usage_operational/total*100:.1f}%)")

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for err in self.errors[:5]:
                print(f"  [{err['bar_index']:4d}] {err['bar_dt']}: {err['error_type']}")
                print(f"    {err['error']}")
            if len(self.errors) > 5:
                print(f"  ... ({len(self.errors) - 5} more errors)")

        print()


def run_integrated_pipeline(
    symbol: str,
    timeframe: str = "D",
    tdx_data_path: str = "/sessions/youthful-friendly-volta/mnt/new_tdx64",
    base_path: str = "var",
    market: str = "sh",
    enable_persistence: bool = True
) -> IntegratedStats:
    """运行完整集成流水线"""

    def _create_current_wave_lifespan(
        core_snapshot: CoreStateSnapshot,
        wave_tracker: WaveTracker,
        lifespan_engine: LifespanEngine,
        rank_engine: RankEngine
    ) -> Optional[WaveLifespan]:
        """为当前 alive wave 创建 partial lifespan（用于 Structural Position）"""

        if core_snapshot.bar_count is None or core_snapshot.bar_count == 0:
            return None

        # 计算当前 wave 的指标
        current_span_bars = core_snapshot.bar_count
        current_direction = core_snapshot.direction

        if not wave_tracker.current_wave_start_price or not core_snapshot.progress_extreme_price:
            return None

        current_price_range = abs(core_snapshot.progress_extreme_price - wave_tracker.current_wave_start_price)
        current_progress_pct = (core_snapshot.progress_extreme_price - wave_tracker.current_wave_start_price) / wave_tracker.current_wave_start_price

        # 创建 partial WaveLifespan
        current_wave = WaveLifespan(
            wave_id=f"current_{symbol}_{timeframe}_W{wave_tracker.wave_counter}",
            symbol=symbol,
            timeframe=timeframe,
            direction=current_direction,
            wave_start_bar_dt=wave_tracker.current_wave_start_bar_dt,
            wave_end_bar_dt=core_snapshot.bar_dt,  # 当前时刻
            span_bars=current_span_bars,
            wave_start_price=wave_tracker.current_wave_start_price,
            wave_end_price=core_snapshot.progress_extreme_price,
            price_range=current_price_range,
            progress_pct=current_progress_pct,
            primitive_count=3,
            pivot_count=wave_tracker.current_wave_pivot_count,
            new_count=wave_tracker.current_wave_new_count,
            no_new_span=0,
            # 计算 rank
            span_rank=None,
            range_rank=None,
            stagnation_rank=None,
            progress_rank=None,
        )

        # 计算排名
        terminated_waves = lifespan_engine.get_terminated_waves(current_direction)
        if len(terminated_waves) >= rank_engine.MIN_SAMPLE_SIZE:
            span_rank = rank_engine.calculate_percentile_rank(
                current_wave.span_bars,
                [w.span_bars for w in terminated_waves]
            )
            range_rank = rank_engine.calculate_percentile_rank(
                current_wave.price_range,
                [w.price_range for w in terminated_waves]
            )
            stagnation_metric = current_wave.span_bars / max(current_wave.primitive_count, 1)
            stagnation_rank = rank_engine.calculate_percentile_rank(
                stagnation_metric,
                [w.span_bars / max(w.primitive_count, 1) for w in terminated_waves]
            )
            progress_rank = rank_engine.calculate_percentile_rank(
                current_wave.progress_pct,
                [w.progress_pct for w in terminated_waves]
            )

            current_wave = replace(current_wave,
                                   span_rank=span_rank,
                                   range_rank=range_rank,
                                   stagnation_rank=stagnation_rank,
                                   progress_rank=progress_rank)

        return current_wave

    print(f"\n{'=' * 80}")
    print(f"Processing {symbol} ({market.upper()} {timeframe}) - Full 5-Layer Integration")
    print(f"{'=' * 80}\n")

    stats = IntegratedStats(symbol)

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

    # 2. 初始化引擎和追踪器
    print(f"\nInitializing engines...")

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

    wave_tracker = WaveTracker()
    range_tracker = RangeTracker()

    # 准备持久化
    if enable_persistence:
        output_dir = Path(base_path) / "published" / symbol / timeframe
        ensure_var_directory(output_dir.parent.parent)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 使用时间戳创建唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = output_dir / f"snapshots_{timestamp}.jsonl"
        print(f"  Output: {snapshot_file}")
    else:
        snapshot_file = None

    print(f"  All engines initialized")

    # 3. 逐 bar 推进
    print(f"\nProcessing bars...")
    print(f"  {'[BAR]':<6} {'DATE':<12} {'STATE':<15} {'SPEED'}")
    print(f"  {'-' * 60}")

    prev_snapshot: Optional[CoreStateSnapshot] = None
    prev_progress_extreme_price: Optional[int] = None

    for i, bar in enumerate(bars):
        try:
            # Core 层
            core_snapshot = core_engine.on_bar(bar)

            # 检测 wave 初始化
            if prev_snapshot and prev_snapshot.system_state == SystemState.UNINITIALIZED:
                if core_snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
                    wave_tracker.on_wave_initialized(core_snapshot)

            # 检测 range resolved 后新 wave 开始
            if prev_snapshot and prev_snapshot.system_state == SystemState.TRANSITION:
                if core_snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
                    wave_tracker.on_wave_initialized(core_snapshot)

            # 检测 progress 更新（新 pivot 确认）
            if prev_snapshot and core_snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
                if prev_progress_extreme_price and core_snapshot.progress_extreme_price:
                    if core_snapshot.progress_extreme_price != prev_progress_extreme_price:
                        wave_tracker.on_progress_update()

            # 检测 wave 终止（alive → transition）
            wave_lifespan = None
            if prev_snapshot and prev_snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
                if core_snapshot.system_state == SystemState.TRANSITION:
                    # Wave 终止！
                    # 使用 prev_snapshot 的 progress（因为 transition 时已经改变）
                    terminated_snapshot = replace(core_snapshot,
                                                   progress_extreme_price=prev_snapshot.progress_extreme_price,
                                                   bar_count=prev_snapshot.bar_count)
                    wave_info = wave_tracker.on_wave_terminated(terminated_snapshot)

                    # 检查必要字段是否存在
                    if (wave_info['wave_start_price'] is None or
                        wave_info['wave_end_price'] is None or
                        wave_info['span_bars'] == 0):
                        # 跳过无效的 wave
                        pass
                    else:
                        wave_lifespan = lifespan_engine.calculate_wave_lifespan(**wave_info)

                        # 计算排名
                        terminated_waves = lifespan_engine.get_terminated_waves(wave_lifespan.direction)
                        if len(terminated_waves) >= rank_engine.MIN_SAMPLE_SIZE:
                            # 更新排名
                            span_rank = rank_engine.calculate_percentile_rank(
                                wave_lifespan.span_bars,
                                [w.span_bars for w in terminated_waves]
                            )
                            range_rank = rank_engine.calculate_percentile_rank(
                                wave_lifespan.price_range,
                                [w.price_range for w in terminated_waves]
                            )
                            stagnation_metric = wave_lifespan.span_bars / max(wave_lifespan.primitive_count, 1)
                            stagnation_rank = rank_engine.calculate_percentile_rank(
                                stagnation_metric,
                                [w.span_bars / max(w.primitive_count, 1) for w in terminated_waves]
                            )
                            progress_rank = rank_engine.calculate_percentile_rank(
                                wave_lifespan.progress_pct,
                                [w.progress_pct for w in terminated_waves]
                            )

                            wave_lifespan = replace(wave_lifespan,
                                                    span_rank=span_rank,
                                                    range_rank=range_rank,
                                                    stagnation_rank=stagnation_rank,
                                                    progress_rank=progress_rank)

                        # 记录到历史
                        lifespan_engine.record_terminated_wave(wave_lifespan)

            # 检测 range 诞生（alive → transition）
            if prev_snapshot and prev_snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
                if core_snapshot.system_state == SystemState.TRANSITION:
                    range_tracker.on_range_born(core_snapshot, i)
                    stats.ranges_born += 1

            # 检测 range resolved（transition → alive）
            range_lifespan = None
            if prev_snapshot and prev_snapshot.system_state == SystemState.TRANSITION:
                if core_snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
                    # Range resolved！
                    range_info = range_tracker.on_range_resolved(core_snapshot, i)
                    range_lifespan = lifespan_engine.calculate_range_lifespan(**range_info)

            # Structural Position 层（为当前 alive wave 生成视图）
            p1, p2, p3, p4 = None, None, None, None
            if core_snapshot.system_state in [SystemState.UP_ALIVE, SystemState.DOWN_ALIVE]:
                # 需要为当前 alive wave 创建 partial lifespan（包含 rank）
                if wave_tracker.current_wave_direction is not None:
                    # 创建当前 wave 的 partial lifespan（用于 Structural Position 计算）
                    current_wave_lifespan = _create_current_wave_lifespan(
                        core_snapshot,
                        wave_tracker,
                        lifespan_engine,
                        rank_engine
                    )

                    if current_wave_lifespan and current_wave_lifespan.span_rank is not None:
                        # 获取已终止 wave 列表
                        terminated_waves = lifespan_engine.get_terminated_waves()

                        try:
                            # 生成 P1-P4 视图
                            p1 = structural_position_engine.build_p1_view(current_wave_lifespan)
                            p2 = structural_position_engine.build_p2_view(current_wave_lifespan, terminated_waves)
                            p3 = structural_position_engine.build_p3_view(current_wave_lifespan, terminated_waves)

                            # P4 需要 w_minus_1（最近已终止 wave）和 current_wave_is_alive 标志
                            w_minus_1 = terminated_waves[-1] if terminated_waves else None
                            current_wave_is_alive = True  # 只有 alive wave 才会生成 P 视图
                            p4 = structural_position_engine.build_p4_view(
                                current_wave_lifespan,
                                w_minus_1,
                                current_wave_is_alive
                            )
                        except Exception as e:
                            # P1-P4 生成失败不阻塞流水线
                            pass

            # Service 层：组装 snapshot
            usage = determine_usage(
                core=core_snapshot,
                wave_lifespan=wave_lifespan,
                range_lifespan=range_lifespan,
                p1=p1,
                p2=p2,
                p3=p3,
                p4=p4,
                input_integrity_passed=True,
                peer_sample_sufficient=(wave_lifespan is not None and wave_lifespan.span_rank is not None),
                data_stale=False,
            )

            reason_codes = generate_reason_codes(
                core=core_snapshot,
                wave_lifespan=wave_lifespan,
                range_lifespan=range_lifespan,
                p1=p1,
                p2=p2,
                p3=p3,
                p4=p4,
                active_range=None,
                input_integrity_passed=True,
                peer_sample_sufficient=(wave_lifespan is not None and wave_lifespan.span_rank is not None),
                data_stale=False,
                operational_enabled=False,
            )

            snapshot = build_wave_structural_snapshot(
                symbol=symbol,
                timeframe=timeframe,
                bar_dt=bar.bar_dt,
                bar_index=i,
                core=core_snapshot,
                active_range=None,
                wave_lifespan=wave_lifespan,
                range_lifespan=range_lifespan,
                p1=p1,
                p2=p2,
                p3=p3,
                p4=p4,
                rule_versions=rule_versions,
                lineage_hash=None,
                input_integrity_passed=True,
                peer_sample_sufficient=(wave_lifespan is not None and wave_lifespan.span_rank is not None),
                data_stale=False,
                operational_enabled=False,
            )

            # 计算 lineage_hash
            snapshot_dict = asdict(snapshot)
            lineage_hash = calculate_lineage_hash(snapshot_dict)
            snapshot = replace(snapshot, lineage_hash=lineage_hash)

            # 持久化
            if enable_persistence and snapshot_file:
                json_str = serialize_snapshot(snapshot)
                with open(snapshot_file, "a", encoding="utf-8") as f:
                    f.write(json_str + "\n")

            # 记录统计
            stats.record_bar(
                i, bar.bar_dt, core_snapshot, usage,
                wave_lifespan, range_lifespan,
                has_p1=(p1 is not None),
                has_p2=(p2 is not None),
                has_p3=(p3 is not None),
                has_p4=(p4 is not None),
            )

            # 打印进度
            stats.print_progress(i, bar.bar_dt, core_snapshot.system_state)

            # 保存状态供下一轮使用
            prev_snapshot = core_snapshot
            prev_progress_extreme_price = core_snapshot.progress_extreme_price

        except Exception as e:
            stats.record_error(i, bar.bar_dt, e)
            print(f"  ERROR at bar {i} ({bar.bar_dt}): {e}")
            import traceback
            traceback.print_exc()

            if stats.error_bars > 10:
                print(f"\n  Too many errors ({stats.error_bars}), aborting...")
                break

    # 4. 完成
    stats.finalize()
    stats.print_summary()

    return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="V1.2 Full Integration Pipeline")
    parser.add_argument("--symbol", type=str, default="510300", help="Symbol to process")
    parser.add_argument("--market", type=str, default="sh", help="Market (sh/sz)")
    parser.add_argument("--timeframe", type=str, default="D", help="Timeframe")
    parser.add_argument("--tdx-data-path", type=str,
                        default="/sessions/youthful-friendly-volta/mnt/new_tdx64",
                        help="TDX data directory")
    parser.add_argument("--base-path", type=str, default="var", help="Output directory")
    parser.add_argument("--no-persistence", action="store_true",
                        help="Disable persistence")

    args = parser.parse_args()

    print(f"\n{'#' * 80}")
    print(f"# V1.2 Full 5-Layer Integration Pipeline")
    print(f"{'#' * 80}")

    stats = run_integrated_pipeline(
        symbol=args.symbol,
        timeframe=args.timeframe,
        tdx_data_path=args.tdx_data_path,
        base_path=args.base_path,
        market=args.market,
        enable_persistence=not args.no_persistence,
    )

    # 返回状态码
    if stats.error_bars > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
