"""蓉城净途命令行入口：不启动 Web 服务，直接调用路由规划器。

用法（需在 python/ 目录下执行，以便 config 与 route_planner 可被导入）：
    python main.py "天府广场,宽窄巷子,武侯祠" --preference balanced
"""

import argparse
import sys

from route_planner import RoutePlanner
from config import DEFAULT_ALPHA, DEFAULT_BETA, MAX_DESTINATIONS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="蓉城净途 - 健康导航系统命令行测试")
    parser.add_argument(
        "destinations",
        type=str,
        help="目的地名称，用逗号分隔，例如：天府广场,宽窄巷子,武侯祠",
    )
    parser.add_argument(
        "--preference",
        type=str,
        choices=["shortest", "green", "balanced"],
        default="balanced",
        help="路线偏好: shortest(最短距离), green(最绿色), balanced(均衡，默认)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help="距离权重（仅对 balanced 模式有效）",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=DEFAULT_BETA,
        help="AQI 权重（仅对 balanced 模式有效）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dest_names = [name.strip() for name in args.destinations.split(",") if name.strip()]

    if not dest_names:
        print("错误：请至少提供一个目的地", file=sys.stderr)
        return 1
    if len(dest_names) > MAX_DESTINATIONS:
        print(f"错误：目的地数量不能超过 {MAX_DESTINATIONS}", file=sys.stderr)
        return 1

    planner = RoutePlanner()
    try:
        order, total_cost, ordered_aqi = planner.plan(
            destinations=dest_names,
            preference=args.preference,
            alpha=args.alpha,
            beta=args.beta,
        )
    except Exception as exc:
        print(f"规划过程中发生异常: {exc}", file=sys.stderr)
        return 1

    print("=== 路线规划结果 ===")
    print(f"目的地: {dest_names}")
    print(f"偏好: {args.preference}")
    print(f"最优访问顺序 (索引): {order}")
    print("顺序名称: " + " → ".join(dest_names[i] for i in order))
    print(f"总综合代价: {total_cost:.4f}")
    print(f"逐站 AQI: {ordered_aqi}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
