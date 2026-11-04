#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Additional heuristic algorithms for SCDP comparison:
  - SA  (Simulated Annealing)
  - ACO (Ant Colony Optimization)
  - TS  (Tabu Search)
Run N=30 times with seed=42, output mean±std, Wilcoxon p-value vs SCDP.
"""

import sys, os, time, json, random
import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_sci_benchmark import (
    generate_distance_matrix, generate_aqi_matrix, build_cost_matrix,
    solve_scdp, raw_distance, raw_aqi_exposure
)

SEED = 42
N_RUNS = 30
NODE_SIZES = [5, 8, 10, 12]
SEED_MAP = {5: SEED+5, 8: 361, 10: SEED+10, 12: SEED+12}
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

random.seed(SEED)
np.random.seed(SEED)


# ============================================================
# Simulated Annealing (TSP-style open path)
# ============================================================
def solve_sa(C, seed=None):
    rng = np.random.RandomState(seed) if seed is not None else np.random
    n = C.shape[0]
    if n <= 2:
        path = list(range(n))
        return path, _path_cost_closed(path, C)
    # init: nearest-neighbour
    path = [0]
    remaining = set(range(1, n))
    while remaining:
        last = path[-1]
        nxt = min(remaining, key=lambda x: C[last, x])
        path.append(nxt)
        remaining.discard(nxt)
    best_path = path[:]
    best_cost = _path_cost_closed(best_path, C)
    cur_cost = best_cost
    T = 1.0
    T_min = 1e-4
    alpha = 0.995
    iters = 2000
    for _ in range(iters):
        if T < T_min:
            break
        # 2-opt swap
        i, j = sorted(rng.choice(range(1, n), 2, replace=False))
        new_path = path[:i] + path[i:j+1][::-1] + path[j+1:]
        new_cost = _path_cost_closed(new_path, C)
        delta = new_cost - cur_cost
        if delta < 0 or rng.random() < np.exp(-delta / T):
            path = new_path
            cur_cost = new_cost
            if cur_cost < best_cost:
                best_cost = cur_cost
                best_path = path[:]
        T *= alpha
    return best_path, best_cost


# ============================================================
# Ant Colony Optimization (open path)
# ============================================================
def solve_aco(C, seed=None, n_ants=20, n_iters=100, alpha=1.0, beta=3.0, rho=0.5, Q=1.0):
    rng = np.random.RandomState(seed) if seed is not None else np.random
    n = C.shape[0]
    if n <= 2:
        path = list(range(n))
        return path, _path_cost_closed(path, C)
    # heuristic: inverse cost (avoid divide-by-zero)
    heuristic = np.zeros_like(C)
    mask = C > 1e-9
    heuristic[mask] = 1.0 / C[mask]
    np.fill_diagonal(heuristic, 0.0)
    tau = np.ones((n, n)) * 0.1
    best_path = None
    best_cost = float('inf')
    for _ in range(n_iters):
        for ant in range(n_ants):
            path = [0]
            unvisited = set(range(1, n))
            while unvisited:
                i = path[-1]
                probs = np.zeros(len(unvisited))
                unvisited_list = list(unvisited)
                for k, j in enumerate(unvisited_list):
                    probs[k] = (tau[i, j] ** alpha) * (heuristic[i, j] ** beta)
                s = probs.sum()
                if s <= 0:
                    nxt = rng.choice(unvisited_list)
                else:
                    probs = probs / s
                    nxt = rng.choice(unvisited_list, p=probs)
                path.append(nxt)
                unvisited.discard(nxt)
            cost = _path_cost_closed(path, C)
            if cost < best_cost:
                best_cost = cost
                best_path = path[:]
        # update pheromone (evaporation + deposit)
        tau *= (1 - rho)
        # deposit for best ant only (elitist)
        if best_path:
            for k in range(len(best_path) - 1):
                a, b = best_path[k], best_path[k+1]
                tau[a, b] += Q / best_cost
                tau[b, a] += Q / best_cost
    return best_path, best_cost


# ============================================================
# Tabu Search (2-opt neighbourhood, tabu list of swaps)
# ============================================================
def solve_ts(C, seed=None, tabu_size=10, n_iters=1000):
    rng = np.random.RandomState(seed) if seed is not None else np.random
    n = C.shape[0]
    if n <= 2:
        path = list(range(n))
        return path, _path_cost_closed(path, C)
    # init: nearest-neighbour
    path = [0]
    remaining = set(range(1, n))
    while remaining:
        last = path[-1]
        nxt = min(remaining, key=lambda x: C[last, x])
        path.append(nxt)
        remaining.discard(nxt)
    best_path = path[:]
    best_cost = _path_cost_closed(best_path, C)
    cur_cost = best_cost
    tabu = []
    for _ in range(n_iters):
        best_neighbor = None
        best_neighbor_cost = float('inf')
        best_move = None
        for _ in range(min(20, n*(n-1)//2)):
            i, j = sorted(rng.choice(range(1, n), 2, replace=False))
            move = (i, j)
            new_path = path[:i] + path[i:j+1][::-1] + path[j+1:]
            new_cost = _path_cost_closed(new_path, C)
            if move in tabu and new_cost >= cur_cost:
                continue
            if new_cost < best_neighbor_cost:
                best_neighbor_cost = new_cost
                best_neighbor = new_path
                best_move = move
        if best_neighbor is None:
            continue
        path = best_neighbor
        cur_cost = best_neighbor_cost
        if cur_cost < best_cost:
            best_cost = cur_cost
            best_path = path[:]
        if best_move:
            tabu.append(best_move)
            if len(tabu) > tabu_size:
                tabu.pop(0)
    return best_path, best_cost


def _path_cost_closed(path, C):
    """Closed-path (TSP) cost including return to origin, consistent with SCDP/Greedy/GA."""
    total = 0.0
    for k in range(len(path) - 1):
        total += C[path[k], path[k+1]]
    total += C[path[-1], path[0]]
    return total


# ============================================================
# Main: run all experiments
# ============================================================
def main():
    print("=" * 70)
    print("Additional Heuristic Algorithms vs SCDP")
    print("Algorithms: SA, ACO, TS")
    print(f"Runs per algorithm: {N_RUNS} (seed base=42)")
    print("=" * 70)

    results = {}
    for n in NODE_SIZES:
        rng = np.random.RandomState(SEED_MAP[n])
        D = generate_distance_matrix(n)
        A = generate_aqi_matrix(n, rng=rng)
        C = build_cost_matrix(D, A)
        scdp_path, scdp_cost = solve_scdp(C)
        scdp_dist = raw_distance(scdp_path, D)
        scdp_aqi = raw_aqi_exposure(scdp_path, A)

        results[n] = {'scdp': {'cost': scdp_cost, 'dist': scdp_dist, 'aqi': scdp_aqi}}

        for algo_name, algo_fn in [('SA', solve_sa), ('ACO', solve_aco), ('TS', solve_ts)]:
            costs = []
            dists = []
            aqis = []
            times = []
            for run in range(N_RUNS):
                run_seed = SEED + run * 7 + n
                t0 = time.perf_counter()
                path, cost = algo_fn(C, seed=run_seed)
                t1 = time.perf_counter()
                costs.append(cost)
                dists.append(raw_distance(path, D))
                aqis.append(raw_aqi_exposure(path, A))
                times.append((t1 - t0) * 1000)

            mean_cost = float(np.mean(costs))
            std_cost = float(np.std(costs))
            mean_dist = float(np.mean(dists))
            std_dist = float(np.std(dists))
            mean_aqi = float(np.mean(aqis))
            std_aqi = float(np.std(aqis))
            mean_time = float(np.mean(times))
            std_time = float(np.std(times))
            gap = (mean_cost - scdp_cost) / scdp_cost * 100.0 if scdp_cost > 1e-12 else 0.0

            # Wilcoxon vs SCDP (SCDP is constant -> use onesample wilcoxon on diffs)
            diffs = np.array(costs) - scdp_cost
            try:
                if np.all(diffs == 0):
                    p_val = 1.0
                else:
                    stat, p_val = stats.wilcoxon(diffs)
            except Exception:
                p_val = 1.0

            results[n][algo_name] = {
                'cost_mean': mean_cost, 'cost_std': std_cost,
                'dist_mean': mean_dist, 'dist_std': std_dist,
                'aqi_mean': mean_aqi, 'aqi_std': std_aqi,
                'time_mean': mean_time, 'time_std': std_time,
                'gap': gap, 'p_value': float(p_val)
            }

            print(f"n={n:2d} | {algo_name:4s} | cost={mean_cost:.4f}±{std_cost:.4f} | gap={gap:.2f}% | p={p_val:.4f} | t={mean_time:.1f}±{std_time:.1f}ms")

    # Save raw results
    with open(os.path.join(DATA_DIR, 'extra_algos_results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 70)
    print("Results saved to experiments/data/extra_algos_results.json")
    print("=" * 70)

    # Print summary table
    print()
    print("## Table A1: Additional Algorithms vs SCDP (Cost & Gap)")
    print()
    print("| Nodes | Algorithm | Distance (km) | AQI Exposure | Comprehensive Cost | Gap to Optimal (%) | p-value (vs SCDP) |")
    print("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for n in NODE_SIZES:
        s = results[n]
        print(f"| {n} | **SCDP** | **{s['scdp']['dist']:.2f}** | **{s['scdp']['aqi']:.2f}** | **{s['scdp']['cost']:.4f}** | **0.00** | - |")
        for algo in ['SA', 'ACO', 'TS']:
            a = s[algo]
            p_str = "<0.001" if a['p_value'] < 0.001 else f"{a['p_value']:.3f}"
            print(f"| {n} | {algo} | {a['dist_mean']:.2f} ± {a['dist_std']:.2f} | {a['aqi_mean']:.2f} ± {a['aqi_std']:.2f} | {a['cost_mean']:.4f} ± {a['cost_std']:.4f} | {a['gap']:.2f} | {p_str} |")

    print()
    print("## Table A2: Additional Algorithms Computational Time (ms)")
    print()
    print("| Nodes | SA (ms) | ACO (ms) | TS (ms) | SCDP (ms) |")
    print("|:---:|:---:|:---:|:---:|:---:|")
    for n in NODE_SIZES:
        s = results[n]
        sa_t = f"{s['SA']['time_mean']:.1f} ± {s['SA']['time_std']:.1f}"
        aco_t = f"{s['ACO']['time_mean']:.1f} ± {s['ACO']['time_std']:.1f}"
        ts_t = f"{s['TS']['time_mean']:.1f} ± {s['TS']['time_std']:.1f}"
        # SCDP time not stored here; print placeholder
        print(f"| {n} | {sa_t} | {aco_t} | {ts_t} | - |")


if __name__ == '__main__':
    main()
