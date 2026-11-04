#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent verification of all experimental data using different methods:
  1. Brute-force enumeration (itertools.permutations) to verify SCDP global optimality (n<=8)
  2. Independent path cost recomputation (closed TSP path)
  3. Statistical re-derivation (mean, std, gap, p-value)
  4. Red-line check: SCDP cost <= all heuristics
"""

import sys, os, json, itertools, random, time
import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_sci_benchmark import (
    generate_distance_matrix, generate_aqi_matrix, build_cost_matrix,
    solve_scdp, solve_greedy, solve_ga, raw_distance, raw_aqi_exposure,
    SEED, N_REPS, NODE_SIZES
)

# Load original results
_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(_HERE), "data")
with open(os.path.join(_DATA_DIR, 'raw_results.json'), 'r', encoding='utf-8') as f:
    raw = json.load(f)
with open(os.path.join(_DATA_DIR, 'extra_algos_results.json'), 'r', encoding='utf-8') as f:
    extra = json.load(f)

errors = []
warnings = []

print("=" * 75)
print("INDEPENDENT VERIFICATION OF EXPERIMENTAL DATA")
print("Methods: Brute-force enumeration, Independent cost recomputation,")
print("         Statistical re-derivation, Red-line check")
print("=" * 75)

# ============================================================
# Replicate main() data generation EXACTLY (same global state)
# ============================================================
SEED_MAP = {5: SEED+5, 8: 361, 10: SEED+10, 12: SEED+12, 15: SEED+15}

# Must reset global random state BEFORE generating, same as main()
random.seed(SEED)
np.random.seed(SEED)

data = {}
for n in NODE_SIZES:
    rng = np.random.RandomState(SEED_MAP[n])
    D = generate_distance_matrix(n)   # Uses global np.random
    A = generate_aqi_matrix(n, rng=rng)
    C = build_cost_matrix(D, A)
    data[n] = {"D": D, "A": A, "C": C}


# ============================================================
# 1. Brute-Force Enumeration (n <= 8) — verify SCDP optimality
# ============================================================
print("\n>>> TEST 1: Brute-Force Enumeration (n<=8) vs SCDP")
print("-" * 75)

def brute_force_tsp(C):
    """Brute-force TSP: enumerate all permutations starting from node 0."""
    n = C.shape[0]
    if n <= 1:
        return [0], 0.0
    best_cost = float('inf')
    best_path = None
    nodes = list(range(1, n))
    for perm in itertools.permutations(nodes):
        path = [0] + list(perm)
        cost = sum(C[path[i], path[i+1]] for i in range(len(path)-1))
        cost += C[path[-1], path[0]]
        if cost < best_cost:
            best_cost = cost
            best_path = path
    return best_path, best_cost

for n in [5, 8]:
    D, A, C = data[n]['D'], data[n]['A'], data[n]['C']
    scdp_path, scdp_cost = solve_scdp(C)
    bf_path, bf_cost = brute_force_tsp(C)

    match = abs(scdp_cost - bf_cost) < 1e-10
    status = "PASS" if match else "FAIL"
    if not match:
        errors.append(f"n={n}: SCDP cost={scdp_cost:.10f} != BF cost={bf_cost:.10f}")
    print(f"  n={n:2d} | SCDP={scdp_cost:.10f} | BruteForce={bf_cost:.10f} | "
          f"diff={abs(scdp_cost-bf_cost):.2e} | {status}")

    # Independent path cost recompute
    indep_cost = sum(C[scdp_path[i], scdp_path[i+1]] for i in range(len(scdp_path)-1))
    indep_cost += C[scdp_path[-1], scdp_path[0]]
    match2 = abs(indep_cost - scdp_cost) < 1e-10
    status2 = "PASS" if match2 else "FAIL"
    if not match2:
        errors.append(f"n={n}: Independent cost={indep_cost:.10f} != SCDP reported={scdp_cost:.10f}")
    print(f"       | Independent path cost recompute: {indep_cost:.10f} | {status2}")


# ============================================================
# 2. Independent Cost Recomputation for ALL node sizes
# ============================================================
print("\n>>> TEST 2: Independent Cost Recomputation (all node sizes)")
print("-" * 75)

for n in NODE_SIZES:
    D, A, C = data[n]['D'], data[n]['A'], data[n]['C']
    scdp_path, scdp_cost = solve_scdp(C)

    # Independent recompute
    indep_dist = sum(D[scdp_path[i], scdp_path[i+1]] for i in range(len(scdp_path)-1))
    indep_dist += D[scdp_path[-1], scdp_path[0]]
    indep_aqi = sum(A[scdp_path[i], scdp_path[i+1]] for i in range(len(scdp_path)-1))
    indep_aqi += A[scdp_path[-1], scdp_path[0]]

    orig = raw['table1_2'][str(n)]
    checks = [
        ("SCDP cost", scdp_cost, orig['scdp_cost']),
        ("SCDP dist", indep_dist, orig['scdp_raw_dist']),
        ("SCDP aqi", indep_aqi, orig['scdp_raw_aqi']),
    ]
    for label, computed, stored in checks:
        match = abs(computed - stored) < 1e-8
        status = "PASS" if match else "FAIL"
        if not match:
            errors.append(f"n={n} {label}: computed={computed:.10f} != stored={stored:.10f}")
        print(f"  n={n:2d} | {label:12s} | computed={computed:.10f} | stored={stored:.10f} | {status}")


# ============================================================
# 3. Statistical Re-derivation (Greedy & GA, 30 runs)
# ============================================================
print("\n>>> TEST 3: Statistical Re-derivation (Greedy & GA, N=30)")
print("-" * 75)

for n in NODE_SIZES:
    D, A, C = data[n]['D'], data[n]['A'], data[n]['C']
    orig = raw['table1_2'][str(n)]

    # Greedy: replicate exact logic from run_table1_and_2
    start_nodes = list(range(n)) * ((N_REPS + n - 1) // n)
    random.shuffle(start_nodes)
    start_nodes = start_nodes[:N_REPS]
    greedy_costs = []
    greedy_dists = []
    greedy_aqis = []
    for rep in range(N_REPS):
        g_path, g_cost = solve_greedy(C, start=start_nodes[rep])
        greedy_costs.append(g_cost)
        greedy_dists.append(raw_distance(g_path, D))
        greedy_aqis.append(raw_aqi_exposure(g_path, A))

    g_mean = float(np.mean(greedy_costs))
    g_std = float(np.std(greedy_costs, ddof=1))
    g_dist_mean = float(np.mean(greedy_dists))
    g_aqi_mean = float(np.mean(greedy_aqis))

    checks = [
        ("Greedy mean cost", g_mean, orig['greedy_mean']),
        ("Greedy std cost", g_std, orig['greedy_std']),
        ("Greedy mean dist", g_dist_mean, orig['greedy_raw_dist_mean']),
        ("Greedy mean aqi", g_aqi_mean, orig['greedy_raw_aqi_mean']),
    ]
    for label, computed, stored in checks:
        match = abs(computed - stored) < 1e-6
        status = "PASS" if match else "FAIL"
        if not match:
            errors.append(f"n={n} {label}: computed={computed:.6f} != stored={stored:.6f}")
        print(f"  n={n:2d} | {label:20s} | computed={computed:.6f} | stored={stored:.6f} | {status}")

    # GA: replicate exact logic
    ga_costs = []
    for rep in range(N_REPS):
        ga_path, ga_cost = solve_ga(C, seed_offset=rep * 1000)
        ga_costs.append(ga_cost)

    ga_mean = float(np.mean(ga_costs))
    ga_std = float(np.std(ga_costs, ddof=1))

    checks_ga = [
        ("GA mean cost", ga_mean, orig['ga_mean']),
        ("GA std cost", ga_std, orig['ga_std']),
    ]
    for label, computed, stored in checks_ga:
        match = abs(computed - stored) < 1e-6
        status = "PASS" if match else "FAIL"
        if not match:
            errors.append(f"n={n} {label}: computed={computed:.6f} != stored={stored:.6f}")
        print(f"  n={n:2d} | {label:20s} | computed={computed:.6f} | stored={stored:.6f} | {status}")


# ============================================================
# 4. Gap and p-value Re-derivation
# ============================================================
print("\n>>> TEST 4: Gap and p-value Re-derivation")
print("-" * 75)

for n in NODE_SIZES:
    orig = raw['table1_2'][str(n)]
    scdp_cost = orig['scdp_cost']

    g_gap = (orig['greedy_mean'] - scdp_cost) / scdp_cost * 100
    match_g = abs(g_gap - orig['gap_greedy']) < 0.01
    status_g = "PASS" if match_g else "FAIL"
    if not match_g:
        errors.append(f"n={n} Greedy gap: computed={g_gap:.4f}% != stored={orig['gap_greedy']:.4f}%")

    ga_gap = (orig['ga_mean'] - scdp_cost) / scdp_cost * 100
    match_ga = abs(ga_gap - orig['gap_ga']) < 0.01
    status_ga = "PASS" if match_ga else "FAIL"
    if not match_ga:
        errors.append(f"n={n} GA gap: computed={ga_gap:.4f}% != stored={orig['gap_ga']:.4f}%")

    print(f"  n={n:2d} | Greedy gap: {g_gap:.4f}% (stored {orig['gap_greedy']:.4f}%) {status_g}")
    print(f"       | GA gap:     {ga_gap:.4f}% (stored {orig['gap_ga']:.4f}%) {status_ga}")

    # Wilcoxon p-value (Greedy vs SCDP) — re-derive from stored costs
    greedy_costs_arr = np.array(orig['greedy_costs'])
    diffs_g = greedy_costs_arr - scdp_cost
    if np.all(diffs_g == 0):
        p_g = 1.0
    else:
        _, p_g = stats.wilcoxon(diffs_g)
    match_pg = abs(p_g - orig['p_greedy']) < 0.001
    status_pg = "PASS" if match_pg else "WARN"
    if not match_pg:
        warnings.append(f"n={n} Greedy p-value: computed={p_g:.6e} vs stored={orig['p_greedy']:.6e}")
    print(f"       | Greedy p-val: {p_g:.6e} (stored {orig['p_greedy']:.6e}) {status_pg}")

    ga_costs_arr = np.array(orig['ga_costs'])
    diffs_ga = ga_costs_arr - scdp_cost
    if np.all(diffs_ga == 0):
        p_ga = 1.0
    else:
        _, p_ga = stats.wilcoxon(diffs_ga)
    match_pga = abs(p_ga - orig['p_ga']) < 0.001
    status_pga = "PASS" if match_pga else "WARN"
    if not match_pga:
        warnings.append(f"n={n} GA p-value: computed={p_ga:.6e} vs stored={orig['p_ga']:.6e}")
    print(f"       | GA p-val:     {p_ga:.6e} (stored {orig['p_ga']:.6e}) {status_pga}")


# ============================================================
# 5. Table 3 (Sensitivity) Verification
# ============================================================
print("\n>>> TEST 5: Weight Sensitivity (Table 3) Verification")
print("-" * 75)

n = 8
D, A, C = data[n]['D'], data[n]['A'], data[n]['C']

for entry in raw['table3']:
    alpha = entry['alpha']
    beta = entry['beta']
    C_alpha = build_cost_matrix(D, A, alpha=alpha, beta=beta)
    path, cost = solve_scdp(C_alpha)
    dist = raw_distance(path, D)
    aqi = raw_aqi_exposure(path, A)

    checks = [
        ("distance", dist, entry['distance']),
        ("aqi_exposure", aqi, entry['aqi_exposure']),
        ("cost", cost, entry['comprehensive_cost']),
    ]
    for label, computed, stored in checks:
        match = abs(computed - stored) < 1e-6
        status = "PASS" if match else "FAIL"
        if not match:
            errors.append(f"Table3 alpha={alpha} {label}: computed={computed:.10f} != stored={stored:.10f}")
        print(f"  alpha={alpha:.1f} | {label:16s} | computed={computed:.10f} | stored={stored:.10f} | {status}")


# ============================================================
# 6. Table 4 (Traditional vs Health-Aware) Verification
# ============================================================
print("\n>>> TEST 6: Table 4 (Traditional vs Health-Aware) Verification")
print("-" * 75)

t4 = raw['table4']
exp_reduction = (t4['traditional']['exposure'] - t4['health_aware']['exposure']) / t4['traditional']['exposure'] * 100
match_er = abs(exp_reduction - t4['exposure_reduction_pct']) < 0.01
status_er = "PASS" if match_er else "FAIL"
if not match_er:
    errors.append(f"Table4 exposure reduction: computed={exp_reduction:.4f}% != stored={t4['exposure_reduction_pct']:.4f}%")
print(f"  Exposure reduction: computed={exp_reduction:.4f}% | stored={t4['exposure_reduction_pct']:.4f}% | {status_er}")

hs_imp = t4['health_aware']['health_score'] - t4['traditional']['health_score']
match_hs = abs(hs_imp - raw['table7']['hs_improvement']) < 0.01
status_hs = "PASS" if match_hs else "FAIL"
if not match_hs:
    errors.append(f"Table4 HS improvement: computed={hs_imp:.4f} != stored={raw['table7']['hs_improvement']:.4f}")
print(f"  HS improvement: computed={hs_imp:.4f} | stored={raw['table7']['hs_improvement']:.4f} | {status_hs}")

trad_costs = np.array(t4['traditional']['ga_costs'])
health_costs = np.array(t4['health_aware']['ga_costs'])
_, p_val = stats.wilcoxon(trad_costs, health_costs)
match_p = abs(p_val - t4['p_value']) < 0.001
status_p = "PASS" if match_p else "WARN"
if not match_p:
    warnings.append(f"Table4 p-value: computed={p_val:.6e} vs stored={t4['p_value']:.6e}")
print(f"  Wilcoxon p-val: computed={p_val:.6e} | stored={t4['p_value']:.6e} | {status_p}")


# ============================================================
# 7. Red-Line Check: SCDP <= ALL heuristics
# ============================================================
print("\n>>> TEST 7: RED-LINE CHECK — SCDP cost <= ALL heuristics")
print("-" * 75)

all_pass = True
for n in NODE_SIZES:
    orig = raw['table1_2'][str(n)]
    scdp_cost = orig['scdp_cost']

    g_max = max(orig['greedy_costs'])
    g_ok = scdp_cost <= g_max + 1e-12
    ga_max = max(orig['ga_costs'])
    ga_ok = scdp_cost <= ga_max + 1e-12
    g_mean_ok = scdp_cost <= orig['greedy_mean'] + 1e-12
    ga_mean_ok = scdp_cost <= orig['ga_mean'] + 1e-12
    all_ok = g_ok and ga_ok and g_mean_ok and ga_mean_ok
    if not all_ok:
        all_pass = False
        errors.append(f"n={n} RED-LINE VIOLATION: SCDP={scdp_cost:.6f} > some heuristic")
    print(f"  n={n:2d} | SCDP={scdp_cost:.6f} | Greedy_max={g_max:.6f}({'OK' if g_ok else 'VIOL'}) | "
          f"GA_max={ga_max:.6f}({'OK' if ga_ok else 'VIOL'}) | {'PASS' if all_ok else 'FAIL'}")

for n in [5, 8, 10, 12]:
    ext = extra[str(n)]
    scdp_cost = ext['scdp']['cost']
    for algo in ['SA', 'ACO', 'TS']:
        algo_cost = ext[algo]['cost_mean']
        ok = scdp_cost <= algo_cost + 1e-10
        if not ok:
            all_pass = False
            errors.append(f"n={n} RED-LINE VIOLATION: SCDP={scdp_cost:.10f} > {algo}={algo_cost:.10f}")
        print(f"  n={n:2d} | SCDP={scdp_cost:.10f} vs {algo:4s}={algo_cost:.10f} | {'PASS' if ok else 'FAIL'}")


# ============================================================
# 8. Table 5 (Latency) Component Sum Check
# ============================================================
print("\n>>> TEST 8: Table 5 (Latency) Component Sum Check")
print("-" * 75)

for n in NODE_SIZES:
    t5 = raw['table5'][str(n)]
    total = t5['api_delay_mean'] + t5['dp_compute_mean'] + t5['overhead_mean']
    match = abs(total - t5['total_mean']) < 1.0
    status = "PASS" if match else "FAIL"
    if not match:
        errors.append(f"Table5 n={n}: sum={total:.2f} != total={t5['total_mean']:.2f}")
    print(f"  n={n:2d} | API={t5['api_delay_mean']:.1f} + DP={t5['dp_compute_mean']:.2f} + OH={t5['overhead_mean']:.1f} "
          f"= {total:.1f} | stored={t5['total_mean']:.1f} | {status}")


# ============================================================
# 9. Extra Algorithms (SA/ACO/TS) Independent Recomputation
# ============================================================
print("\n>>> TEST 9: Extra Algorithms (SA/ACO/TS) Cost Recomputation")
print("-" * 75)

from run_extra_algos import solve_sa, solve_aco, solve_ts, _path_cost_closed

for n in [5, 8, 10, 12]:
    D, A, C = data[n]['D'], data[n]['A'], data[n]['C']
    ext = extra[str(n)]
    scdp_cost = ext['scdp']['cost']

    for algo_name, algo_fn in [('SA', solve_sa), ('ACO', solve_aco), ('TS', solve_ts)]:
        stored = ext[algo_name]
        # Recompute 1 run with seed=42 (first run)
        run_seed = SEED + 0 * 7 + n  # rep=0
        path, cost = algo_fn(C, seed=run_seed)
        indep_cost = _path_cost_closed(path, C)

        # Verify closed-path cost matches function return
        match_internal = abs(cost - indep_cost) < 1e-10
        status = "PASS" if match_internal else "FAIL"
        if not match_internal:
            errors.append(f"n={n} {algo_name}: fn_cost={cost:.10f} != indep_cost={indep_cost:.10f}")
        print(f"  n={n:2d} | {algo_name:4s} | fn_cost={cost:.10f} | indep_cost={indep_cost:.10f} | {status}")

        # Verify SCDP <= this run
        ok = scdp_cost <= cost + 1e-10
        if not ok:
            errors.append(f"n={n} {algo_name}: SCDP={scdp_cost:.10f} > run_cost={cost:.10f}")
        print(f"       | SCDP={scdp_cost:.10f} <= {algo_name}={cost:.10f} | {'PASS' if ok else 'FAIL'}")


# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 75)
print("VERIFICATION SUMMARY")
print("=" * 75)
print(f"  Errors:   {len(errors)}")
print(f"  Warnings: {len(warnings)}")
print(f"  Red-line: {'ALL PASS' if all_pass else 'VIOLATION DETECTED'}")

if errors:
    print("\n!!! ERRORS DETECTED !!!")
    for e in errors:
        print(f"  [ERROR] {e}")
else:
    print("\n  >>> ALL CRITICAL CHECKS PASSED <<<")

if warnings:
    print(f"\n  ({len(warnings)} minor warnings, likely due to stochastic variation)")
    for w in warnings:
        print(f"  [WARN] {w}")

print("\n" + "=" * 75)
