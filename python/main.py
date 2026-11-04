# main.py
print("main.py 开始执行")
import argparse
import sys
import traceback
from route_planner import RoutePlanner
from config import DEFAULT_ALPHA, DEFAULT_BETA, MAX_DESTINATIONS

def parse_args():
    parser = argparse.ArgumentParser(description="蓉城净途 - 健康导航系统命令行测试")
    parser.add_argument("destinations", type=str, help="目的地名称，用逗号分隔，例如：天府广场,宽窄巷子,武侯祠")
    parser.add_argument("--preference", type=str, choices=["shortest", "green", "balanced"], default="balanced",
                        help="路线偏好: shortest(最短距离), green(最绿色), balanced(均衡，默认)")
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA, help="距离权重（仅对balanced模式有效）")
    parser.add_argument("--beta", type=float, default=DEFAULT_BETA, help="AQI权重（仅对balanced模式有效）")
    return parser.parse_args()

def main():
    print("开始解析参数...")
    args = parse_args()
    print(f"解析成功: destinations={args.destinations}, preference={args.preference}, alpha={args.alpha}, beta={args.beta}")
    
    dest_names = [name.strip() for name in args.destinations.split(",")]
    if len(dest_names) > MAX_DESTINATIONS:
        print(f"错误：目的地数量不能超过 {MAX_DESTINATIONS}")
        sys.exit(1)
    print(f"目的地列表: {dest_names}")

    print("初始化 RoutePlanner...")
    planner = RoutePlanner()
    try:
        print("开始调用 planner.plan()...")
        # ✅ 关键修改：传递 preference 参数，让 plan 内部统一处理权重
        order, total_cost = planner.plan(
            destinations=dest_names,
            preference=args.preference,
            alpha=args.alpha,
            beta=args.beta
        )
        print("plan() 调用成功")
    except Exception as e:
        print(f"规划过程中发生异常: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("\n=== 路线规划结果 ===")
    print(f"目的地: {dest_names}")
    print(f"偏好: {args.preference}")
    print(f"最优访问顺序 (索引): {order}")
    print("顺序名称: " + " → ".join([dest_names[i] for i in order]))
    print(f"总综合代价: {total_cost:.4f}")
    sys.stdout.flush()

if __name__ == "__main__":
    main()