#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate path detail table from path_details.json."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DETAIL_PATH = os.path.join(os.path.dirname(HERE), "data", "path_details.json")

with open(DETAIL_PATH, "r", encoding="utf-8") as f:
    t1 = json.load(f)

print()
print("# 附录表：各算法路径详情（节点访问顺序）")
print()
print("> 注：路径为闭合路径（TSP），末节点自动回到起点。SCDP 为确定性精确算法，结果唯一；Greedy/GA 各独立运行 30 次，表中列出代表性路径（第 1 次、第 15 次、第 30 次）。")
print()

for n_str in sorted(t1.keys(), key=lambda x: int(x)):
    n = int(n_str)
    r = t1[n_str]
    D = r["D"]
    A = r["A"]

    print(f"## 场景 {n}：{n} 个节点")
    print()

    # 节点距离矩阵
    print(f"### 距离矩阵 D（单位：km）")
    print()
    header = "| 节点 | " + " | ".join(f"{i}" for i in range(n)) + " |"
    sep = "|:---:|" + "|".join([":---:"] * n) + "|"
    print(header)
    print(sep)
    for i in range(n):
        row = f"| **{i}** | " + " | ".join(f"{D[i][j]:.2f}" for j in range(n)) + " |"
        print(row)
    print()

    # AQI 矩阵
    print(f"### AQI 暴露矩阵 A")
    print()
    print(header)
    print(sep)
    for i in range(n):
        row = f"| **{i}** | " + " | ".join(f"{A[i][j]:.1f}" for j in range(n)) + " |"
        print(row)
    print()

    # SCDP 路径
    scdp_p = r.get("scdp_path")
    if scdp_p:
        scdp_path_str = " → ".join(str(x) for x in scdp_p) + f" → {scdp_p[0]}"
        print(f"### SCDP（最优路径）")
        print()
        print(f"- **路径**：{scdp_path_str}")
        print(f"- **综合成本**：{r['scdp_cost']:.4f}")
        print(f"- **原始距离**：{r['scdp_raw_dist']:.2f} km")
        print(f"- **原始 AQI 暴露**：{r['scdp_raw_aqi']:.2f}")
        print()

    # Greedy 代表性路径
    greedy_paths = r.get("greedy_paths", [])
    greedy_starts = r.get("greedy_start_nodes", [])
    if greedy_paths:
        print(f"### Greedy（代表性路径）")
        print()
        reps = [0, min(14, len(greedy_paths)-1), len(greedy_paths)-1]
        for rep in reps:
            p = greedy_paths[rep]
            start = greedy_starts[rep] if rep < len(greedy_starts) else "N/A"
            path_str = " → ".join(str(x) for x in p) + f" → {p[0]}"
            cost = r["greedy_costs"][rep] if rep < len(r.get("greedy_costs", [])) else "N/A"
            print(f"- **第 {rep+1} 次**（起点 {start}）：{path_str}，综合成本 = {cost:.4f}")
        print()

    # GA 代表性路径
    ga_paths = r.get("ga_paths", [])
    if ga_paths:
        print(f"### GA（代表性路径）")
        print()
        reps = [0, min(14, len(ga_paths)-1), len(ga_paths)-1]
        for rep in reps:
            p = ga_paths[rep]
            path_str = " → ".join(str(x) for x in p) + f" → {p[0]}"
            cost = r["ga_costs"][rep] if rep < len(r.get("ga_costs", [])) else "N/A"
            print(f"- **第 {rep+1} 次**：{path_str}，综合成本 = {cost:.4f}")
        print()

print("---")
print()
print("*生成时间：基于固定随机种子 SEED=42，结果可复现。*")
