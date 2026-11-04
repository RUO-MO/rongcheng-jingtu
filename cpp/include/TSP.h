#ifndef TSP_H
#define TSP_H

#include <vector>
#include <string>
#include <stdexcept>

namespace tsp {

/**
 * @brief TSP 求解结果结构体
 */
struct Result {
    std::vector<int> path;      // 最优路径的索引序列 (例如: 0 -> 2 -> 1)
    double total_cost;          // 总综合代价
};

/**
 * @brief 基于状态压缩动态规划求解 TSP (Open TSP: 不强制回到起点)
 * 
 * @param cost_matrix N x N 的代价矩阵。cost_matrix[i][j] 表示从点 i 到点 j 的代价。
 *                    该矩阵应由上层根据“距离”和“AQI”及“策略权重”计算好后传入。
 * @return Result 包含最优路径和总代价
 * @throws std::invalid_argument 当节点数 N > 7 或 N == 0 时抛出异常
 */
Result solve(const std::vector<std::vector<double>>& cost_matrix);

// 如果你还需要保留原来的简单接口，可以保留下面这行；否则可以删除。
std::vector<int> solve_tsp(const std::vector<std::vector<double>>& distance_matrix);

} // namespace tsp

#endif // TSP_H