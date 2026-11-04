#include "TSP.h"   // ← 改成这样
#include <limits>
#include <algorithm>

namespace tsp {

Result solve(const std::vector<std::vector<double>>& cost_matrix) {
    int n = static_cast<int>(cost_matrix.size());

    // 1. 边界检查
    if (n == 0) {
        return {{}, 0.0};
    }
    if (n > 10) {
        throw std::invalid_argument("TSP Solver limit exceeded: max 10 destinations allowed (Current: " + std::to_string(n) + ").");
    }
    if (n == 1) {
        return {{0}, 0.0};
    }

    // 2. 初始化 DP 表
    // dp[mask][i]: 访问过 mask 集合中的点，且最后停留在点 i 的最小代价
    int limit = 1 << n;
    const double INF = std::numeric_limits<double>::max() / 2.0; // 防止加法溢出

    std::vector<std::vector<double>> dp(limit, std::vector<double>(n, INF));
    std::vector<std::vector<int>> parent(limit, std::vector<int>(n, -1));

    // 3. 初始状态：假设从索引 0 出发 (起点固定为第一个节点)
    dp[1][0] = 0.0;

    // 4. 状态转移 (DP 核心)
    for (int mask = 1; mask < limit; ++mask) {
        for (int i = 0; i < n; ++i) {
            // 如果点 i 不在当前 mask 中，或者当前状态不可达，跳过
            if (!(mask & (1 << i)) || dp[mask][i] >= INF) continue;

            // 尝试从 i 走到下一个点 j
            for (int j = 0; j < n; ++j) {
                // 如果 j 已经在 mask 中，跳过 (不能重复访问)
                if (mask & (1 << j)) continue;

                int next_mask = mask | (1 << j);
                double new_cost = dp[mask][i] + cost_matrix[i][j];

                if (new_cost < dp[next_mask][j]) {
                    dp[next_mask][j] = new_cost;
                    parent[next_mask][j] = i; // 记录前驱节点，用于回溯
                }
            }
        }
    }

    // 5. 寻找最优解 (Open TSP: 不回到起点)
    // 在所有访问了全部点 (mask = limit - 1) 的状态中，找代价最小的终点
    int full_mask = limit - 1;
    double min_total_cost = INF;
    int last_node = -1;

    for (int i = 0; i < n; ++i) {
        if (dp[full_mask][i] < min_total_cost) {
            min_total_cost = dp[full_mask][i];
            last_node = i;
        }
    }

    // 6. 检查是否存在可行路径
    if (min_total_cost >= INF) {
        throw std::runtime_error("No feasible path exists for the given cost matrix (graph may be disconnected)");
    }

    // 7. 路径回溯
    std::vector<int> path;
    int curr = last_node;
    int curr_mask = full_mask;

    while (curr != -1) {
        path.push_back(curr);
        int prev = parent[curr_mask][curr];
        curr_mask ^= (1 << curr); // 从 mask 中移除当前点
        curr = prev;
    }
    std::reverse(path.begin(), path.end()); // 反转得到从起点到终点的顺序

    return {path, min_total_cost};
}

} // namespace tsp