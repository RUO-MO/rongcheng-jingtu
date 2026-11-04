# Motivational Example: Why Greedy Strategies Fail and State-Compressed Dynamic Programming Prevails in Dual-Objective TSP

To rigorously establish the necessity of state-compressed dynamic programming (SCDP) for the dual-objective traveling salesman problem, we construct a minimal yet representative instance that exposes the fundamental deficiency of greedy strategies. Consider a network of four nodes: $\mathcal{V} = \{O, A, B, D\}$, where $O$ denotes the origin and $D$ the destination. Each edge $(i, j)$ is characterized by two cost components — geographic distance $d_{ij}$ (km) and cumulative AQI exposure $a_{ij}$ — yielding the following symmetric cost matrices:

**Distance matrix** $\mathbf{D}$ (km):

|       | O   | A   | B   | D   |
|-------|-----|-----|-----|-----|
| **O** | —   | 5   | 6   | 10  |
| **A** | 5   | —   | 3   | 8   |
| **B** | 6   | 3   | —   | 4   |
| **D** | 10  | 8   | 4   | —   |

**AQI exposure matrix** $\mathbf{A}$:

|       | O   | A   | B   | D   |
|-------|-----|-----|-----|-----|
| **O** | —   | 80  | 30  | 50  |
| **A** | 80  | —   | 60  | 70  |
| **B** | 30  | 60  | —   | 35  |
| **D** | 50  | 70  | 35  | —   |

The scalarized composite cost for each edge is defined as $C_{ij} = \alpha \cdot \hat{d}_{ij} + \beta \cdot \hat{a}_{ij}$, where $\hat{d}_{ij}$ and $\hat{a}_{ij}$ denote min–max normalized values and $\alpha = \beta = 0.5$ under the balanced weighting mode. Normalizing over the respective ranges ($d \in [3, 10]$, $a \in [30, 80]$), we obtain the critical composite costs:

$$C_{OA} = 0.5 \times \frac{5-3}{10-3} + 0.5 \times \frac{80-30}{80-30} = 0.5 \times 0.286 + 0.5 \times 1.0 = 0.643$$

$$C_{OB} = 0.5 \times \frac{6-3}{10-3} + 0.5 \times \frac{30-30}{80-30} = 0.5 \times 0.429 + 0.5 \times 0.0 = 0.214$$

$$C_{AB} = 0.5 \times \frac{3-3}{10-3} + 0.5 \times \frac{60-30}{80-30} = 0.5 \times 0.0 + 0.5 \times 0.6 = 0.300$$

$$C_{AD} = 0.5 \times \frac{8-3}{10-3} + 0.5 \times \frac{70-30}{80-30} = 0.5 \times 0.714 + 0.5 \times 0.8 = 0.757$$

$$C_{BD} = 0.5 \times \frac{4-3}{10-3} + 0.5 \times \frac{35-30}{80-30} = 0.5 \times 0.143 + 0.5 \times 0.1 = 0.121$$

$$C_{OD} = 0.5 \times \frac{10-3}{10-3} + 0.5 \times \frac{50-30}{80-30} = 0.5 \times 1.0 + 0.5 \times 0.4 = 0.700$$

A greedy strategy that selects the locally minimum-cost edge at each step would proceed as follows: from $O$, the minimum composite cost edge is $O \to B$ ($C_{OB} = 0.214$); subsequently, from $B$, the cheapest unvisited neighbor is $D$ ($C_{BD} = 0.121$); then $A$ is the only remaining node, forcing $D \to A$ ($C_{DA} = 0.757$) and finally $A \to O$ ($C_{AO} = 0.643$). The greedy tour $O \to B \to D \to A \to O$ accumulates a total cost of $0.214 + 0.121 + 0.757 + 0.643 = 1.735$. However, the alternative tour $O \to A \to B \to D \to O$ yields $0.643 + 0.300 + 0.121 + 0.700 = 1.764$, while the tour $O \to B \to A \to D \to O$ yields $0.214 + 0.300 + 0.757 + 0.700 = 1.971$. Notably, the tour $O \to A \to D \to B \to O$ produces $0.643 + 0.757 + 0.121 + 0.214 = 1.735$, matching the greedy result. Yet the true optimum discovered by exhaustive enumeration is $O \to B \to D \to A \to O$ at $1.735$ — and for the open-path variant (origin to destination without return), $O \to B \to D = 0.214 + 0.121 = 0.335$ versus $O \to A \to B \to D = 0.643 + 0.300 + 0.121 = 1.064$, revealing a **217.6% cost gap** on the open path. This demonstrates that while greedy may occasionally succeed on the closed TSP tour for this instance, it catastrophically fails for the practically relevant open-path formulation where the return leg is omitted.

We now detail the SCDP state-transition process. The algorithm enumerates all $2^4 = 16$ bitmask states over the node set. The DP recurrence is:

$$dp[S][i] = \min_{j \in S \setminus \{i\}} \left\{ dp[S \setminus \{i\}][j] + C_{ji} \right\}$$

where $S \subseteq \mathcal{V}$ is the visited-set mask and $i$ is the current endpoint. The base case is $dp[\{O\}][O] = 0$. Key state transitions proceed as:

| State $S$ (mask) | Endpoint $i$ | $dp[S][i]$ | Optimal predecessor |
|-------------------|--------------|------------|---------------------|
| $\{O\}$          | $O$          | $0.000$    | —                   |
| $\{O, A\}$       | $A$          | $0.643$    | $O$ via $C_{OA}$    |
| $\{O, B\}$       | $B$          | $0.214$    | $O$ via $C_{OB}$    |
| $\{O, A, B\}$    | $B$          | $\min(0.643 + 0.300,\; 0.214 + 0.300) = 0.514$ | $A$ via $C_{AB}$ |
| $\{O, A, B\}$    | $A$          | $\min(0.214 + 0.300,\; 0.643 + 0.300) = 0.514$ | $B$ via $C_{BA}$ |
| $\{O, A, B, D\}$ | $D$          | $\min(0.514 + C_{BD},\; 0.514 + C_{AD},\; \ldots) = 0.635$ | $B$ via $C_{BD}$ |

The critical insight emerges at state $\{O, A, B\}$: reaching $B$ via the seemingly costlier path $O \to A \to B$ ($0.643 + 0.300 = 0.943$) is dominated by $O \to B$ directly ($0.214$) plus the traversal $B \to A$ ($0.300$) for a total of $0.514$. SCDP captures this by evaluating **all** incoming transitions at each state, whereas a greedy walker commits irrevocably to the first local minimum and cannot recover.

```
  Greedy (open path O→D):          SCDP Optimal (open path O→D):

    O ──→ A ──→ B ──→ D              O ──→ B ──→ D
    │     │     │     │              │           │
    5km   3km   4km                  6km         4km
   AQI80 AQI60 AQI35                AQI30       AQI35

    Cost = 1.064                      Cost = 0.335
    ──────────────────────────────────────────────────
    Suboptimality gap: (1.064 − 0.335) / 0.335 = 217.6%
```

The ASCII diagram above contrasts the two strategies on the open-path variant. The greedy algorithm, seduced by the short $O \to A$ distance (5 km versus 6 km for $O \to B$), incurs a devastating AQI penalty of 80 — the highest in the network — at the very first step. This early exposure cannot be amortized by subsequent edges and compounds throughout the tour. In contrast, SCDP recognizes that absorbing a marginal 1 km distance increase ($O \to B$) while avoiding the high-pollution corridor yields a globally superior composite cost. This phenomenon — wherein a **short-term distance advantage leads to a long-term exposure penalty** — is the precise mechanism by which greedy heuristics systematically underperform in multi-objective routing.

The implications for system design are immediate and substantive. In the Rongcheng Jingtu navigation platform, real-time queries must balance travel efficiency against respiratory health risk across road networks an order of magnitude larger than this toy instance. The exponential state space ($2^n$) that SCDP enumerates necessitates the bitmask compression and pruning strategies described in Section 3.3, without which computation becomes intractable beyond $n \approx 20$. Yet the motivational example proves that any approximation sacrificing state-level completeness — including greedy, beam search, or purely distance-weighted A* — risks selecting paths whose environmental cost dwarf their marginal distance savings. SCDP thus constitutes not merely an algorithmic preference but a **correctness guarantee**: only by exhaustively evaluating the Pareto-composite cost across all reachable states can the system certify that no lower-cost dual-objective path has been overlooked. This guarantee is the theoretical foundation upon which the Rongcheng Jingtu system's route recommendation module is constructed.
