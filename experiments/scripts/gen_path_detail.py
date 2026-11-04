#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick path table generator - only computes what's needed for the appendix table."""
import sys
import os
import json
import random
import numpy as np
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DATA_DIR = os.path.join(os.path.dirname(HERE), "data")

from run_sci_benchmark import (
    SEED, NODE_SIZES, ALPHA, BETA,
    generate_distance_matrix, generate_aqi_matrix, build_cost_matrix,
    solve_scdp, solve_greedy, solve_ga,
    raw_distance, raw_aqi_exposure,
)

N_REPS = 30

def main():
    # Match original global seed (run_sci_benchmark.py L34-35)
    np.random.seed(SEED)
    random.seed(SEED)

    # Match original SEED_MAP exactly
    SEED_MAP = {5: SEED + 5, 8: 361, 10: SEED + 10, 12: SEED + 12, 15: SEED + 15}

    # Step 1: Generate all data FIRST (same order as original: n=5,8,10,12,15)
    data = {}
    for n in NODE_SIZES:
        rng = np.random.RandomState(SEED_MAP[n])
        D = generate_distance_matrix(n)    # uses global np.random state (NOT reset per n)
        A = generate_aqi_matrix(n, rng=rng)  # uses local rng with SEED_MAP[n]
        C = build_cost_matrix(D, A)
        data[n] = {"D": D, "A": A, "C": C}

    results = {}

    for n in NODE_SIZES:
        print(f"\n=== n={n} (seed={SEED_MAP[n]}) ===", flush=True)
        D = data[n]["D"]
        A = data[n]["A"]
        C = data[n]["C"]

        # SCDP
        scdp_path, scdp_cost = (None, None)
        if n <= 12:
            print(f"  SCDP...", end=" ", flush=True)
            scdp_path, scdp_cost = solve_scdp(C)
            print(f"done (cost={scdp_cost:.4f})", flush=True)

        # Greedy (30 reps)
        print(f"  Greedy (30 reps)...", end=" ", flush=True)
        greedy_paths = []
        greedy_costs = []
        greedy_start_nodes = []
        start_nodes = list(range(n)) * ((N_REPS + n - 1) // n)
        random.shuffle(start_nodes)
        start_nodes = start_nodes[:N_REPS]
        for rep in range(N_REPS):
            p, c = solve_greedy(C, start=start_nodes[rep])
            greedy_paths.append(p)
            greedy_costs.append(c)
            greedy_start_nodes.append(start_nodes[rep])
        print(f"done (mean={np.mean(greedy_costs):.4f})", flush=True)

        # GA (30 reps)
        print(f"  GA (30 reps)...", end=" ", flush=True)
        ga_paths = []
        ga_costs = []
        for rep in range(N_REPS):
            p, c = solve_ga(C, seed_offset=rep * 1000)
            ga_paths.append(p)
            ga_costs.append(c)
        print(f"done (mean={np.mean(ga_costs):.4f})", flush=True)

        results[n] = {
            "D": D.tolist(),
            "A": A.tolist(),
            "scdp_path": [int(x) for x in scdp_path] if scdp_path else None,
            "scdp_cost": float(scdp_cost) if scdp_cost is not None else None,
            "scdp_raw_dist": float(raw_distance(scdp_path, D)) if scdp_path else None,
            "scdp_raw_aqi": float(raw_aqi_exposure(scdp_path, A)) if scdp_path else None,
            "greedy_start_nodes": [int(x) for x in greedy_start_nodes],
            "greedy_paths": [[int(x) for x in p] for p in greedy_paths],
            "greedy_costs": [float(x) for x in greedy_costs],
            "ga_paths": [[int(x) for x in p] for p in ga_paths],
            "ga_costs": [float(x) for x in ga_costs],
        }

    # Save
    out_path = os.path.join(DATA_DIR, "path_details.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {out_path}", flush=True)

    # Print Markdown table
    print("\n" + "=" * 80)
    print("# 附录表：各算法路径详情（节点访问顺序）")
    print("=" * 80)
    print()
    print("> 注：路径为闭合路径（TSP），末节点自动回到起点。")
    print("> SCDP 为确定性精确算法，结果唯一；Greedy/GA 各独立运行 30 次，表中列出第 1、15、30 次代表性路径。")
    print()

    for n in sorted(results.keys()):
        r = results[n]
        D = r["D"]
        A = r["A"]

        print(f"## 场景 A{n}：{n} 个节点")
        print()

        # 距离矩阵
        print(f"### 距离矩阵 D（单位：km）")
        print()
        hdr = "| 节点 | " + " | ".join(f"{i}" for i in range(n)) + " |"
        sep = "|:---:|" + "|".join([":---:"] * n) + "|"
        print(hdr)
        print(sep)
        for i in range(n):
            row = f"| **{i}** | " + " | ".join(f"{D[i][j]:.2f}" for j in range(n)) + " |"
            print(row)
        print()

        # AQI 矩阵
        print(f"### AQI 暴露矩阵 A")
        print()
        print(hdr)
        print(sep)
        for i in range(n):
            row = f"| **{i}** | " + " | ".join(f"{A[i][j]:.1f}" for j in range(n)) + " |"
            print(row)
        print()

        # SCDP
        scdp_p = r["scdp_path"]
        if scdp_p:
            scdp_str = " → ".join(str(x) for x in scdp_p) + f" → {scdp_p[0]}"
            print(f"### SCDP（全局最优路径）")
            print()
            print(f"- **路径**：{scdp_str}")
            print(f"- **综合成本**：{r['scdp_cost']:.4f}")
            print(f"- **原始距离**：{r['scdp_raw_dist']:.2f} km")
            print(f"- **原始 AQI 暴露**：{r['scdp_raw_aqi']:.2f}")
            print()

        # Greedy
        g_paths = r["greedy_paths"]
        g_starts = r["greedy_start_nodes"]
        g_costs = r["greedy_costs"]
        if g_paths:
            print(f"### Greedy（代表性路径）")
            print()
            for idx in [0, 14, 29]:
                if idx < len(g_paths):
                    p = g_paths[idx]
                    s = g_starts[idx]
                    c = g_costs[idx]
                    pstr = " → ".join(str(x) for x in p) + f" → {p[0]}"
                    print(f"- **第 {idx+1} 次**（起点 {s}）：{pstr}，综合成本 = {c:.4f}")
            print()

        # GA
        ga_p = r["ga_paths"]
        ga_c = r["ga_costs"]
        if ga_p:
            print(f"### GA（代表性路径）")
            print()
            for idx in [0, 14, 29]:
                if idx < len(ga_p):
                    p = ga_p[idx]
                    c = ga_c[idx]
                    pstr = " → ".join(str(x) for x in p) + f" → {p[0]}"
                    print(f"- **第 {idx+1} 次**：{pstr}，综合成本 = {c:.4f}")
            print()

    print("---")
    print()
    print("*注：所有结果基于固定随机种子 SEED=42，可完全复现。距离矩阵 D 满足对称性；AQI 矩阵 A 具有空间自相关性（聚类生成）。*")

if __name__ == "__main__":
    main()
