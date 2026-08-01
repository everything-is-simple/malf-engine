#!/usr/bin/env python3
"""V2 人工验证可视化工具

读取验证材料包，生成带 K 线图的 HTML 报告，辅助人工验证。

功能：
1. 读取 03-SNAPSHOTS-DATA.json 中的 15 个验证案例
2. 从 TDX 原始数据中提取每个案例的 K 线窗口
3. 使用 matplotlib 绘制 K 线图，标注 Pivot、Guard、Progress
4. 生成交互式 HTML 报告，包含所有图表和验证清单
5. 支持逐案例对照验证和结果记录

输出：
- var/validation/v2_visual_report.html
- var/validation/charts/*.png (15 个案例的 K 线图)
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "verify"))

# 导入 TDX 读取器
from tdx_reader import load_tdx_daily_bars

# matplotlib 配置
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates


def load_validation_cases(package_path: Path) -> List[Dict[str, Any]]:
    """加载验证案例数据"""
    json_file = package_path / "03-SNAPSHOTS-DATA.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_bar_window(all_bars, bar_dt: str, window_size: int = 20) -> List:
    """提取指定 bar 前后的窗口数据"""
    # 找到目标 bar 的索引
    target_idx = None
    for i, bar in enumerate(all_bars):
        if bar.bar_dt == bar_dt:
            target_idx = i
            break

    if target_idx is None:
        return []

    # 提取窗口（前后各 window_size/2）
    start = max(0, target_idx - window_size // 2)
    end = min(len(all_bars), target_idx + window_size // 2 + 1)

    return all_bars[start:end], target_idx - start


def plot_case_chart(case: Dict[str, Any], all_bars, output_path: Path):
    """绘制单个案例的 K 线图"""

    # 提取窗口数据（前后各 15 根 bar）
    window_bars, target_offset = extract_bar_window(
        all_bars,
        case['event_bar']['bar_dt'],
        window_size=30
    )

    if not window_bars:
        print(f"  Warning: Cannot find bars for {case['event_bar']['bar_dt']}")
        return

    # 准备数据
    dates = [datetime.strptime(b.bar_dt, '%Y-%m-%d') for b in window_bars]
    opens = [b.open / 1000 for b in window_bars]
    highs = [b.high / 1000 for b in window_bars]
    lows = [b.low / 1000 for b in window_bars]
    closes = [b.close / 1000 for b in window_bars]

    # 创建图表
    fig, ax = plt.subplots(figsize=(14, 8))

    # 绘制 K 线
    for i in range(len(dates)):
        color = 'red' if closes[i] >= opens[i] else 'green'

        # 绘制影线
        ax.plot([dates[i], dates[i]], [lows[i], highs[i]], color=color, linewidth=1)

        # 绘制实体
        body_height = abs(closes[i] - opens[i])
        body_bottom = min(opens[i], closes[i])
        rect = Rectangle(
            (mdates.date2num(dates[i]) - 0.3, body_bottom),
            0.6, body_height,
            facecolor=color, edgecolor=color, alpha=0.8
        )
        ax.add_patch(rect)

    # 标注当前案例 bar（黄色高亮）
    if target_offset < len(dates):
        ax.axvline(dates[target_offset], color='yellow', linewidth=2, alpha=0.5,
                   label=f"Event Bar: {case['event_bar']['bar_dt']}")

    # 标注 Pivot
    if 'confirmed_pivot' in case and case['confirmed_pivot']:
        pivot = case['confirmed_pivot']
        pivot_dt = datetime.strptime(pivot['extreme_bar_dt'], '%Y-%m-%d')
        pivot_price = pivot['price'] / 1000

        marker = 'v' if pivot['pivot_type'] == 'H' else '^'
        color = 'blue' if pivot['pivot_type'] == 'H' else 'orange'
        ax.scatter(pivot_dt, pivot_price, marker=marker, s=200, color=color,
                   label=f"{pivot['pivot_type']} Pivot @ {pivot_price:.2f}", zorder=5)

    # 标注 Guard
    snapshot = case['core_snapshot']
    if snapshot['current_effective_guard_price']:
        guard_price = snapshot['current_effective_guard_price'] / 1000
        ax.axhline(guard_price, color='purple', linestyle='--', linewidth=2,
                   label=f"Guard @ {guard_price:.2f}")

    # 标注 Progress
    if snapshot['progress_extreme_price']:
        progress_price = snapshot['progress_extreme_price'] / 1000
        ax.axhline(progress_price, color='cyan', linestyle='--', linewidth=2,
                   label=f"Progress @ {progress_price:.2f}")

    # 设置标题和标签
    title = f"Case #{case['event_bar']['bar_index']} - {case['event_bar']['bar_dt']}\n"
    title += f"Category: {case['selection_category']} | Events: {', '.join(case['events'])}\n"
    title += f"State: {snapshot['system_state']} | Direction: {snapshot['direction']}"

    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Price (CNY)', fontsize=10)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

    # 格式化 x 轴日期
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()


def generate_html_report(cases: List[Dict], output_dir: Path):
    """生成 HTML 验证报告"""

    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V2 人工验证报告 - 510300</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        header h1 { font-size: 32px; margin-bottom: 10px; }
        header p { font-size: 16px; opacity: 0.9; }
        .summary {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 24px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .stat-card .label {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }
        .stat-card .value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .case {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .case-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        .case-title {
            font-size: 22px;
            font-weight: bold;
            color: #333;
        }
        .case-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            background: #e3f2fd;
            color: #1976d2;
        }
        .case-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .info-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .info-item .label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .info-item .value {
            font-size: 15px;
            font-weight: 600;
            color: #333;
        }
        .chart-container {
            margin: 25px 0;
            text-align: center;
        }
        .chart-container img {
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .validation-form {
            background: #fff9e6;
            padding: 20px;
            border-radius: 8px;
            border: 2px solid #ffd54f;
            margin-top: 20px;
        }
        .validation-form h3 {
            color: #f57c00;
            margin-bottom: 15px;
            font-size: 18px;
        }
        .checkbox-group {
            margin: 10px 0;
        }
        .checkbox-group label {
            display: block;
            padding: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .checkbox-group label:hover {
            background: #fff3cd;
        }
        .checkbox-group input {
            margin-right: 8px;
        }
        textarea {
            width: 100%;
            min-height: 80px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-family: inherit;
            font-size: 14px;
            margin-top: 10px;
        }
        .pivot-window {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        .pivot-window table {
            width: 100%;
            border-collapse: collapse;
        }
        .pivot-window th, .pivot-window td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .pivot-window th {
            background: #e0e0e0;
            font-weight: bold;
        }
        .pivot-window .extreme-row {
            background: #fff3cd;
            font-weight: bold;
        }
        footer {
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 MALF V2 人工验证报告</h1>
            <p>标的: 510300 (沪深300ETF) | 生成时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </header>

        <div class="summary">
            <h2>📊 验证概览</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="label">验证案例总数</div>
                    <div class="value">""" + str(len(cases)) + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">要求最少验证</div>
                    <div class="value">10 案例</div>
                </div>
                <div class="stat-card">
                    <div class="label">Pivot 准确率要求</div>
                    <div class="value">&gt; 95%</div>
                </div>
                <div class="stat-card">
                    <div class="label">Guard/Progress 要求</div>
                    <div class="value">&gt; 90%</div>
                </div>
            </div>
        </div>
"""

    # 生成每个案例的内容
    for i, case in enumerate(cases, 1):
        snapshot = case['core_snapshot']
        event_bar = case['event_bar']

        # 格式化价格
        def fmt_price(p):
            return f"{p/1000:.3f}" if p else "—"

        html_content += f"""
        <div class="case" id="case-{i}">
            <div class="case-header">
                <div class="case-title">案例 #{i} - Bar #{event_bar['bar_index']}</div>
                <div class="case-badge">{case['selection_category']}</div>
            </div>

            <div class="case-info">
                <div class="info-item">
                    <div class="label">日期</div>
                    <div class="value">{event_bar['bar_dt']}</div>
                </div>
                <div class="info-item">
                    <div class="label">事件</div>
                    <div class="value">{', '.join(case['events'])}</div>
                </div>
                <div class="info-item">
                    <div class="label">状态</div>
                    <div class="value">{snapshot['system_state']}</div>
                </div>
                <div class="info-item">
                    <div class="label">方向</div>
                    <div class="value">{snapshot['direction'] or '—'}</div>
                </div>
                <div class="info-item">
                    <div class="label">Guard</div>
                    <div class="value">{fmt_price(snapshot['current_effective_guard_price'])}</div>
                </div>
                <div class="info-item">
                    <div class="label">Progress</div>
                    <div class="value">{fmt_price(snapshot['progress_extreme_price'])}</div>
                </div>
            </div>

            <div class="chart-container">
                <img src="charts/case_{i:02d}.png" alt="Case {i} Chart">
            </div>
"""

        # 添加 Pivot 窗口（如果有）
        if 'confirmed_pivot' in case and case['confirmed_pivot']:
            pivot = case['confirmed_pivot']
            if 'strict_fractal_window' in pivot and pivot['strict_fractal_window']:
                window = pivot['strict_fractal_window']
                html_content += """
            <div class="pivot-window">
                <h4>📍 Pivot 确认窗口 (fractal k=2)</h4>
                <table>
                    <tr>
                        <th>日期</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Close</th>
                        <th>标记</th>
                    </tr>
"""
                for bar_data in window:
                    row_class = ' class="extreme-row"' if bar_data.get('is_extreme') else ''
                    marker = '⭐ EXTREME' if bar_data.get('is_extreme') else ''
                    html_content += f"""
                    <tr{row_class}>
                        <td>{bar_data['bar_dt']}</td>
                        <td>{bar_data['open']/1000:.3f}</td>
                        <td>{bar_data['high']/1000:.3f}</td>
                        <td>{bar_data['low']/1000:.3f}</td>
                        <td>{bar_data['close']/1000:.3f}</td>
                        <td>{marker}</td>
                    </tr>
"""
                html_content += """
                </table>
            </div>
"""

        # 添加验证表单
        html_content += """
            <div class="validation-form">
                <h3>✅ 人工验证清单</h3>
                <div class="checkbox-group">
                    <label><input type="checkbox"> Pivot 识别与确认延迟正确</label>
                    <label><input type="checkbox"> Guard 引用与方向规则正确</label>
                    <label><input type="checkbox"> Progress 引用与方向规则正确</label>
                    <label><input type="checkbox"> 状态转换 / break / candidate 行为正确</label>
                </div>
                <div style="margin-top: 15px;">
                    <strong>结论：</strong>
                    <label><input type="radio" name="conclusion_""" + str(i) + """" value="pass"> ✅ 通过</label>
                    <label><input type="radio" name="conclusion_""" + str(i) + """" value="fail"> ❌ 不通过</label>
                    <label><input type="radio" name="conclusion_""" + str(i) + """" value="pending"> ⏳ 待确认</label>
                </div>
                <textarea placeholder="备注（可选）..."></textarea>
            </div>
        </div>
"""

    # 添加页脚
    html_content += """
        <footer>
            <p>生成工具: scripts/verify/v2_visual_validator.py</p>
            <p>数据源: I:\\new_tdx64\\vipdoc\\sh\\lday\\sh510300.day</p>
        </footer>
    </div>
</body>
</html>
"""

    # 写入文件
    report_file = output_dir / "v2_visual_report.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ HTML report generated: {report_file}")


def main():
    """主函数"""
    print("=" * 80)
    print("V2 人工验证可视化工具")
    print("=" * 80)

    # 路径配置
    package_path = PROJECT_ROOT / ".work" / "V2-validation-package"
    output_dir = PROJECT_ROOT / "var" / "validation"
    charts_dir = output_dir / "charts"

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(exist_ok=True)

    print(f"\n📂 Package path: {package_path}")
    print(f"📂 Output dir: {output_dir}")

    # 加载验证案例
    print("\n📥 Loading validation cases...")
    cases = load_validation_cases(package_path)
    print(f"   Loaded {len(cases)} cases")

    # 加载 TDX 原始数据
    print("\n📊 Loading TDX data for 510300...")
    tdx_path = "/sessions/awesome-quirky-mendel/mnt/new_tdx64"
    all_bars = load_tdx_daily_bars("510300", tdx_data_path=tdx_path, market="sh")
    print(f"   Loaded {len(all_bars)} bars")

    # 生成每个案例的图表
    print("\n🎨 Generating charts...")
    for i, case in enumerate(cases, 1):
        print(f"   [{i:2d}/{len(cases)}] Plotting case #{case['event_bar']['bar_index']}...", end='')
        chart_file = charts_dir / f"case_{i:02d}.png"
        plot_case_chart(case, all_bars, chart_file)
        print(" ✅")

    # 生成 HTML 报告
    print("\n📄 Generating HTML report...")
    generate_html_report(cases, output_dir)

    print("\n" + "=" * 80)
    print("✨ Done! Open the report:")
    print(f"   {output_dir / 'v2_visual_report.html'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
