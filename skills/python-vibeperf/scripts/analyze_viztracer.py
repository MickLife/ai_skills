import json
import argparse
import os
from collections import defaultdict
from typing import Dict, List, Any

def parse_viztracer_json(file_path: str) -> Dict[str, Any]:
    """解析 viztracer 生成的 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # viztracer 的数据通常在 traceEvents 列表中
    events = data.get('traceEvents', [])
    if not events and isinstance(data, list):
        events = data
        
    return events

def analyze_events(events: List[Dict[str, Any]]) -> tuple:
    """分析事件，计算函数和模块的耗时"""
    function_stats = defaultdict(lambda: {'calls': 0, 'total_dur': 0.0})
    module_stats = defaultdict(lambda: {'calls': 0, 'total_dur': 0.0})
    
    total_trace_time = 0.0
    
    for event in events:
        # 只关注 Complete events (X)
        if event.get('ph') == 'X' and 'name' in event:
            name = event['name']
            # dur 的单位是微秒 (us)
            dur = event.get('dur', 0)
            
            if dur > 0:
                total_trace_time += dur
                
                # 更新函数统计
                function_stats[name]['calls'] += 1
                function_stats[name]['total_dur'] += dur
                
                # 尝试提取模块名 (通常格式为 module.function)
                parts = name.split('.')
                if len(parts) > 1:
                    module_name = '.'.join(parts[:-1])
                else:
                    module_name = "unknown_module"
                    
                module_stats[module_name]['calls'] += 1
                module_stats[module_name]['total_dur'] += dur

    return function_stats, module_stats, total_trace_time

def format_time(us: float) -> str:
    """将微秒格式化为易读的时间字符串"""
    if us < 1000:
        return f"{us:.2f} µs"
    elif us < 1000000:
        return f"{us / 1000:.2f} ms"
    else:
        return f"{us / 1000000:.2f} s"

def generate_markdown_report(
    function_stats: dict, 
    module_stats: dict, 
    total_time: float, 
    output_path: str,
    top_n: int = 100
):
    """生成 Markdown 格式的报告"""
    
    # 按总耗时排序
    sorted_funcs = sorted(
        function_stats.items(), 
        key=lambda x: x[1]['total_dur'], 
        reverse=True
    )[:top_n]

    md_content = [
        "# VizTracer 性能分析报告\n",
        f"**总记录耗时:** {format_time(total_time)}\n",
        "*(注意：由于函数调用存在嵌套，所有函数的耗时总和可能会大于总记录耗时)*\n",
        "\n## 🎯 Top 100 最耗时函数排行\n",
        "| 排名 | 函数名 | 总耗时 | 调用次数 | 平均每次耗时 | 耗时占比 (粗略) |",
        "|------|--------|--------|----------|--------------|----------------|"
    ]

    for i, (func, stats) in enumerate(sorted_funcs, 1):
        dur = stats['total_dur']
        calls = stats['calls']
        avg = dur / calls if calls > 0 else 0
        pct = (dur / total_time * 100) if total_time > 0 else 0
        
        md_content.append(
            f"| {i} | `{func}` | {format_time(dur)} | {calls} | {format_time(avg)} | {pct:.1f}% |"
        )

    # 写入文件
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
        
    print(f"Report successfully generated at: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='解析 viztracer JSON 并生成 Markdown 报告')
    parser.add_argument('input_json', help='viztracer 生成的 json 文件路径 (例如 result.json)')
    parser.add_argument('-o', '--output', default='docs/perf/PERF_BASELINE.md', 
                        help='输出的 Markdown 文件路径 (默认: docs/perf/PERF_BASELINE.md)')
    parser.add_argument('-n', '--top', type=int, default=100,
                        help='显示的 Top N 数量 (默认: 100)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_json):
        print(f"Error: File not found {args.input_json}")
        return

    print(f"[{args.input_json}] is being parsed...")
    events = parse_viztracer_json(args.input_json)
    
    print("Analyzing duration data...")
    func_stats, mod_stats, total_time = analyze_events(events)
    
    print(f"Generating Top {args.top} report...")
    generate_markdown_report(func_stats, mod_stats, total_time, args.output, args.top)

if __name__ == "__main__":
    main()