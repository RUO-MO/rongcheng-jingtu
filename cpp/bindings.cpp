#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <iostream>
#include "TSP.h"

namespace py = pybind11;

// 归一化辅助函数
std::vector<std::vector<double>> normalize_matrix(const std::vector<std::vector<double>>& matrix) {
    int n = matrix.size();
    if (n == 0) return {};
    
    double min_val = std::numeric_limits<double>::max();
    double max_val = std::numeric_limits<double>::lowest();
    
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i != j) {
                min_val = std::min(min_val, matrix[i][j]);
                max_val = std::max(max_val, matrix[i][j]);
            }
        }
    }
    
    std::vector<std::vector<double>> normalized(n, std::vector<double>(n, 0.0));
    double range = max_val - min_val;
    
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (range > 0) {
                normalized[i][j] = (matrix[i][j] - min_val) / range;
            } else {
                normalized[i][j] = 0.0;
            }
        }
    }
    
    return normalized;
}

// 加权TSP求解
tsp::Result solve_tsp_weighted(
    const std::vector<std::vector<double>>& distance_matrix,
    const std::vector<std::vector<double>>& aqi_matrix,
    double alpha,
    double beta
) {
    int n = distance_matrix.size();
    
    // 归一化
    auto norm_dist = normalize_matrix(distance_matrix);
    auto norm_aqi = normalize_matrix(aqi_matrix);
    
    // 构建加权代价矩阵
    std::vector<std::vector<double>> cost_matrix(n, std::vector<double>(n, 0.0));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            cost_matrix[i][j] = alpha * norm_dist[i][j] + beta * norm_aqi[i][j];
        }
    }
    
    return tsp::solve(cost_matrix);
}

// 简单TSP求解接口（兼容Python调用）
std::vector<int> solve_tsp_simple(const std::vector<std::vector<double>>& cost_matrix) {
    tsp::Result result = tsp::solve(cost_matrix);
    return result.path;
}

PYBIND11_MODULE(_core, m) {
    py::class_<tsp::Result>(m, "Result")
        .def_readwrite("path", &tsp::Result::path)
        .def_readwrite("total_cost", &tsp::Result::total_cost);
    
    // 简单接口：Python代码期望的调用方式
    m.def("solve_tsp", &solve_tsp_simple,
          "Simple TSP solver - returns path only",
          py::arg("cost_matrix"));
    
    m.def("solve_tsp_weighted", &solve_tsp_weighted,
          "Solve TSP with normalized weighted cost (distance + AQI)",
          py::arg("distance_matrix"),
          py::arg("aqi_matrix"),
          py::arg("alpha"),
          py::arg("beta"));
}