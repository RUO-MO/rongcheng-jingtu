# AI辅助生成：DeepSeek-R1, 2026-03-10 - 系统架构设计
# AI辅助生成：DeepSeek-R1, 2026-03-25 - 路线规划核心逻辑

"""
route_planner.py
智能路线规划核心模块
"""

import sys
import time
import logging
from typing import List, Tuple, Optional, Dict
import threading

# 配置模块日志
logger = logging.getLogger(__name__)

# 尝试导入配置（如果失败使用默认值）
try:
    from config import DEFAULT_ALPHA, DEFAULT_BETA, MAX_DESTINATIONS
except ImportError:
    logger.warning("config模块未找到，使用默认值")
    DEFAULT_ALPHA = 1.0
    DEFAULT_BETA = 0.5
    MAX_DESTINATIONS = 7

# 尝试导入API客户端
try:
    from api_client import AMapClient
except ImportError:
    logger.error("api_client模块未找到！")
    raise

# 尝试导入工具函数
try:
    from utils import estimate_aqi
except ImportError as e:
    logger.error(f"utils模块导入失败: {e}")
    raise

# 尝试导入 C++ 模块
try:
    import _core
    HAS_CPP = True
    logger.info("使用 C++ TSP 求解器")
except ImportError:
    HAS_CPP = False
    logger.warning("C++ 模块未找到，使用 Python 求解器")


class RoutePlanner:
    """路线规划器 - 线程安全"""
    
    def __init__(self):
        try:
            self.client = AMapClient()
            logger.info("AMapClient 初始化成功")
        except Exception as e:
            logger.error(f"AMapClient 初始化失败: {e}")
            raise
        
        self._cache_lock = threading.RLock()
        self._distance_cache: Dict[str, List[List[float]]] = {}
        self._aqi_cache: Dict[str, int] = {}
        self._stats = {
            'total_plans': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _get_cache_key(self, coords: List[Tuple[float, float]]) -> str:
        """生成坐标列表的缓存键"""
        return '|'.join(f"{lat:.5f},{lng:.5f}" for lat, lng in coords)
    
    def geocode_destinations(self, names: List[str]) -> List[Tuple[float, float]]:
        """将目的地名称转换为坐标列表"""
        coords = []
        failed = []
        
        for idx, name in enumerate(names):
            try:
                logger.info(f"地理编码 [{idx}]: {name}")
                lat, lng = self.client.geocode(name)
                
                if lat is None or lng is None:
                    raise ValueError(f"返回空坐标")
                
                # 验证坐标范围
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    raise ValueError(f"坐标超出有效范围: ({lat}, {lng})")
                
                coords.append((lat, lng))
                logger.info(f"  成功: ({lat:.5f}, {lng:.5f})")
                
            except Exception as e:
                logger.error(f"  失败: {str(e)}")
                failed.append((idx, name, str(e)))
        
        if failed:
            error_msg = "; ".join(f"[{i}] {n}: {e}" for i, n, e in failed)
            raise ValueError(f"地点解析失败: {error_msg}")
        
        return coords

    def _get_distance_matrix(self, coords: List[Tuple[float, float]]) -> List[List[float]]:
        """获取距离矩阵（带缓存）"""
        cache_key = self._get_cache_key(coords)
        
        with self._cache_lock:
            if cache_key in self._distance_cache:
                self._stats['cache_hits'] += 1
                logger.info("距离矩阵缓存命中")
                return self._distance_cache[cache_key]
            self._stats['cache_misses'] += 1
        
        logger.info(f"请求距离矩阵: {len(coords)}个地点")
        start_time = time.time()
        
        try:
            dist_matrix = self.client.distance_matrix(coords)
        except Exception as e:
            logger.error(f"距离矩阵请求失败: {e}")
            raise
        
        elapsed = time.time() - start_time
        logger.info(f"距离矩阵计算完成: {elapsed:.2f}s")
        
        # 验证矩阵
        n = len(coords)
        if len(dist_matrix) != n:
            raise ValueError(f"矩阵维度错误: 期望{n}行, 实际{len(dist_matrix)}行")
        
        for i, row in enumerate(dist_matrix):
            if len(row) != n:
                raise ValueError(f"矩阵第{i}行维度错误: 期望{n}列, 实际{len(row)}列")
        
        with self._cache_lock:
            self._distance_cache[cache_key] = dist_matrix
        
        return dist_matrix

    def _get_aqi_list(self, coords: List[Tuple[float, float]]) -> List[int]:
        """批量获取AQI列表（带缓存）"""
        aqi_list = []
        
        for lat, lng in coords:
            cache_key = f"{lat:.4f},{lng:.4f}"
            
            with self._cache_lock:
                if cache_key in self._aqi_cache:
                    aqi_list.append(self._aqi_cache[cache_key])
                    continue
            
            try:
                aqi_float = estimate_aqi(lat, lng)
                aqi = int(aqi_float) if aqi_float is not None else 100
                
                with self._cache_lock:
                    self._aqi_cache[cache_key] = aqi
                aqi_list.append(aqi)
                
            except Exception as e:
                logger.error(f"AQI获取失败 ({lat}, {lng}): {e}, 使用默认值100")
                aqi_list.append(100)
        
        return aqi_list

    def build_cost_matrix(
        self, 
        coords: List[Tuple[float, float]], 
        alpha: float, 
        beta: float,
        preference: str = 'balanced'
    ) -> Tuple[List[List[float]], List[int]]:
        """构建综合代价矩阵（距离和AQI）"""
        n = len(coords)
        if n == 0:
            return [], []
        
        dist_matrix = self._get_distance_matrix(coords)
        aqi_list = self._get_aqi_list(coords)
        
        # 计算归一化因子
        max_dist = max(max(row) for row in dist_matrix) if n > 0 else 1.0
        max_aqi = max(aqi_list) if aqi_list else 1.0
        min_aqi = min(aqi_list) if aqi_list else 0
        
        if max_dist < 0.001:
            max_dist = 0.001
        if max_aqi < 1:
            max_aqi = 1
        
        # 构建代价矩阵
        cost_matrix = [[0.0] * n for _ in range(n)]
        
        # 调试日志：显示AQI值和模式
        logger.info(f"[{preference}] 模式 AQI列表: {aqi_list}, max={max_aqi}, min={min_aqi}")
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    cost_matrix[i][j] = 0.0
                else:
                    d_norm = dist_matrix[i][j] / max_dist
                    
                    # 根据模式调整AQI计算
                    if preference == 'green':
                        # 绿色模式：完全忽略距离，只考虑AQI
                        # 使用反转AQI值，AQI越低代价越小
                        aqi_range = max_aqi - min_aqi if max_aqi > min_aqi else 1
                        # 反转：AQI越低，代价越小（越优先）
                        a_norm = (max_aqi - aqi_list[j]) / aqi_range
                        # 绿色模式下，距离权重为0，只使用AQI
                        d_norm = 0
                    else:
                        a_norm = aqi_list[j] / max_aqi
                    
                    cost_matrix[i][j] = alpha * d_norm + beta * a_norm
        
        # 调试日志：显示代价矩阵
        logger.info(f"[{preference}] 代价矩阵第一行: {cost_matrix[0]}")
        
        return cost_matrix, aqi_list

    def _get_traffic_matrix(self, coords: List[Tuple[float, float]]) -> List[List[float]]:
        """获取交通状况矩阵"""
        n = len(coords)
        traffic_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    traffic_matrix[i][j] = 0.0
                else:
                    try:
                        traffic_info = self.client.get_traffic_condition(coords[i], coords[j])
                        # 使用拥堵时间作为交通状况指标
                        traffic_matrix[i][j] = traffic_info.get('congestion_time', 0)
                    except Exception as e:
                        logger.error(f"获取交通状况失败 ({i} -> {j}): {e}")
                        traffic_matrix[i][j] = 0.0
        
        return traffic_matrix

    def solve_tsp(self, cost_matrix: List[List[float]]) -> List[int]:
        """调用 C++ 或 Python 的 TSP 求解器"""
        n = len(cost_matrix)
        
        if n == 0:
            return []
        if n == 1:
            return [0]
        
        if n <= 10 and HAS_CPP:
            logger.info(f"使用C++求解器 (n={n})")
            try:
                # 尝试调用简单接口
                return _core.solve_tsp(cost_matrix)
            except Exception as e:
                logger.warning(f"简单接口失败: {e}, 尝试加权接口")
                try:
                    # 如果简单接口失败，尝试使用加权接口
                    # 创建一个假的AQI矩阵（全0），使用默认权重
                    aqi_matrix = [[0.0] * n for _ in range(n)]
                    result = _core.solve_tsp_weighted(cost_matrix, aqi_matrix, 1.0, 0.0)
                    return result.path if hasattr(result, 'path') else result
                except Exception as e2:
                    logger.error(f"C++求解器完全失败: {e2}, 回退到Python")
                    if n <= 8:
                        return self._solve_tsp_dp(cost_matrix)
                    else:
                        return self._solve_tsp_heuristic(cost_matrix)
        elif n <= 8:
            logger.info(f"使用Python DP (n={n})")
            return self._solve_tsp_dp(cost_matrix)
        else:
            logger.info(f"使用启发式算法 (n={n})")
            return self._solve_tsp_heuristic(cost_matrix)
    
    def solve_tsp_fixed_end(self, cost_matrix: List[List[float]]) -> List[int]:
        """求解固定终点的TSP（终点必须是最后一个点，不需要返回起点）"""
        n = len(cost_matrix)
        
        if n == 0:
            return []
        if n == 1:
            return [0]
        if n == 2:
            return [0, 1]  # 起点->终点
        
        # 固定终点是最后一个节点 (n-1)
        # 起点是0，终点是n-1
        # 需要优化中间节点(1到n-2)的顺序
        fixed_start = 0
        fixed_end = n - 1
        middle_nodes = list(range(1, n - 1))
        m = len(middle_nodes)
        
        if m == 0:
            return [fixed_start, fixed_end]
        
        if m <= 7:
            # 使用动态规划求解中间节点的最优顺序
            return self._solve_tsp_fixed_end_dp(cost_matrix, fixed_start, fixed_end, middle_nodes)
        else:
            # 使用启发式算法
            return self._solve_tsp_fixed_end_heuristic(cost_matrix, fixed_start, fixed_end, middle_nodes)

    def _solve_tsp_dp(self, cost_matrix: List[List[float]]) -> List[int]:
        """Python 实现的 TSP 动态规划"""
        n = len(cost_matrix)
        INF = float('inf')
        
        dp = [[INF] * n for _ in range(1 << n)]
        parent = [[-1] * n for _ in range(1 << n)]
        dp[1][0] = 0
        
        for mask in range(1 << n):
            for i in range(n):
                if not (mask & (1 << i)) or dp[mask][i] == INF:
                    continue
                for j in range(n):
                    if mask & (1 << j):
                        continue
                    new_mask = mask | (1 << j)
                    new_cost = dp[mask][i] + cost_matrix[i][j]
                    if new_cost < dp[new_mask][j]:
                        dp[new_mask][j] = new_cost
                        parent[new_mask][j] = i
        
        full_mask = (1 << n) - 1
        best_cost = INF
        last = -1
        
        for i in range(1, n):
            if dp[full_mask][i] + cost_matrix[i][0] < best_cost:
                best_cost = dp[full_mask][i] + cost_matrix[i][0]
                last = i
        
        order = []
        mask = full_mask
        cur = last if last != -1 else 0
        
        while cur != -1:
            order.append(cur)
            nxt = parent[mask][cur]
            mask &= ~(1 << cur)
            cur = nxt
        
        order.reverse()
        return order if order else [0]

    def _solve_tsp_heuristic(self, cost_matrix: List[List[float]]) -> List[int]:
        """启发式TSP求解：最近邻 + 2-opt优化"""
        n = len(cost_matrix)
        
        unvisited = set(range(1, n))
        order = [0]
        current = 0
        
        while unvisited:
            nearest = min(unvisited, key=lambda j: cost_matrix[current][j])
            order.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        # 2-opt优化
        improved = True
        iteration = 0
        max_iterations = 100
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    if j + 1 < n:
                        old_cost = (cost_matrix[order[i-1]][order[i]] + 
                                   cost_matrix[order[j]][order[j+1]])
                        new_cost = (cost_matrix[order[i-1]][order[j]] + 
                                   cost_matrix[order[i]][order[j+1]])
                    else:
                        old_cost = (cost_matrix[order[i-1]][order[i]] + 
                                   cost_matrix[order[j]][order[0]])
                        new_cost = (cost_matrix[order[i-1]][order[j]] + 
                                   cost_matrix[order[i]][order[0]])
                    
                    if new_cost < old_cost - 0.001:
                        order[i:j+1] = list(reversed(order[i:j+1]))
                        improved = True
                        break
                if improved:
                    break
        
        return order

    def _solve_tsp_fixed_end_dp(self, cost_matrix: List[List[float]], fixed_start: int, fixed_end: int, middle_nodes: List[int]) -> List[int]:
        """固定终点的TSP动态规划求解"""
        m = len(middle_nodes)
        if m == 0:
            return [fixed_start, fixed_end]
        
        INF = float('inf')
        # dp[mask][i] 表示从fixed_start出发，经过mask中的节点，到达middle_nodes[i]的最小代价
        dp = [[INF] * m for _ in range(1 << m)]
        parent = [[-1] * m for _ in range(1 << m)]
        
        # 初始化：从fixed_start到各个中间节点
        for i in range(m):
            node_i = middle_nodes[i]
            dp[1 << i][i] = cost_matrix[fixed_start][node_i]
        
        # 状态转移
        for mask in range(1 << m):
            for i in range(m):
                if not (mask & (1 << i)) or dp[mask][i] == INF:
                    continue
                node_i = middle_nodes[i]
                for j in range(m):
                    if mask & (1 << j):
                        continue
                    node_j = middle_nodes[j]
                    new_mask = mask | (1 << j)
                    new_cost = dp[mask][i] + cost_matrix[node_i][node_j]
                    if new_cost < dp[new_mask][j]:
                        dp[new_mask][j] = new_cost
                        parent[new_mask][j] = i
        
        # 找到以fixed_end结束的最优路径
        full_mask = (1 << m) - 1
        best_cost = INF
        last_middle_idx = -1
        
        for i in range(m):
            if dp[full_mask][i] == INF:
                continue
            node_i = middle_nodes[i]
            total_cost = dp[full_mask][i] + cost_matrix[node_i][fixed_end]
            if total_cost < best_cost:
                best_cost = total_cost
                last_middle_idx = i
        
        # 重建路径
        order = [fixed_end]
        mask = full_mask
        cur_idx = last_middle_idx
        
        while cur_idx != -1:
            order.append(middle_nodes[cur_idx])
            next_idx = parent[mask][cur_idx]
            mask &= ~(1 << cur_idx)
            cur_idx = next_idx
        
        order.append(fixed_start)
        order.reverse()
        
        return order

    def _solve_tsp_fixed_end_heuristic(self, cost_matrix: List[List[float]], fixed_start: int, fixed_end: int, middle_nodes: List[int]) -> List[int]:
        """固定终点的TSP启发式求解（最近邻+2-opt）"""
        m = len(middle_nodes)
        if m == 0:
            return [fixed_start, fixed_end]
        
        # 最近邻构造初始解
        unvisited = set(middle_nodes)
        order = [fixed_start]
        current = fixed_start
        
        while unvisited:
            nearest = min(unvisited, key=lambda j: cost_matrix[current][j])
            order.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        order.append(fixed_end)
        
        # 2-opt优化（不交换起点和终点）
        improved = True
        iteration = 0
        max_iterations = 100
        n = len(order)
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            for i in range(1, n - 2):  # 不交换起点
                for j in range(i + 1, n - 1):  # 不交换终点
                    old_cost = (cost_matrix[order[i-1]][order[i]] + 
                               cost_matrix[order[j]][order[j+1]])
                    new_cost = (cost_matrix[order[i-1]][order[j]] + 
                               cost_matrix[order[i]][order[j+1]])
                    
                    if new_cost < old_cost - 0.001:
                        order[i:j+1] = list(reversed(order[i:j+1]))
                        improved = True
                        break
                if improved:
                    break
        
        return order

    def plan(self, destinations, preference='balanced', alpha=None, beta=None):
        """
        主接口：输入目的地名称列表和偏好，返回最优规划结果
        
        返回: (order, total_cost, aqi_list) 元组
        """
        start_time = time.time()
        self._stats['total_plans'] += 1
        
        # 参数验证
        if not isinstance(destinations, list):
            raise TypeError(f"destinations必须是列表，实际是{type(destinations)}")
        
        if len(destinations) == 0:
            raise ValueError("目的地列表不能为空")
        
        if len(destinations) > MAX_DESTINATIONS:
            raise ValueError(f"目的地数量不能超过{MAX_DESTINATIONS}，当前{len(destinations)}个")
        
        # 设置权重
        if preference == 'shortest':
            alpha_used, beta_used = 1.0, 0  # 只考虑距离
        elif preference == 'green':
            alpha_used, beta_used = 0, 1.0  # 只考虑空气质量
        elif preference == 'balanced':
            alpha_used = alpha if alpha is not None else DEFAULT_ALPHA
            beta_used = beta if beta is not None else DEFAULT_BETA
        else:
            raise ValueError(f"未知偏好模式: {preference}")
        
        logger.info(f"开始规划: {len(destinations)}个地点, 偏好={preference}, α={alpha_used}, β={beta_used}")
        
        # 步骤1: 地理编码
        try:
            coords = self.geocode_destinations(destinations)
        except Exception as e:
            logger.error(f"地理编码失败: {e}")
            raise ValueError(f"地点解析失败: {str(e)}")
        
        # 步骤2: 构建代价矩阵
        try:
            cost_matrix, aqi_list = self.build_cost_matrix(coords, alpha_used, beta_used, preference)
        except Exception as e:
            logger.error(f"构建代价矩阵失败: {e}")
            raise RuntimeError(f"构建代价矩阵失败: {str(e)}")
        
        # 步骤3: 求解TSP
        try:
            order = self.solve_tsp(cost_matrix)
        except Exception as e:
            logger.error(f"TSP求解失败: {e}")
            raise RuntimeError(f"路线求解失败: {str(e)}")
        
        # 步骤4: 计算总代价
        total_cost = 0.0
        for k in range(len(order) - 1):
            i, j = order[k], order[k + 1]
            total_cost += cost_matrix[i][j]
        
        if len(order) > 1:
            total_cost += cost_matrix[order[-1]][order[0]]
        
        elapsed = time.time() - start_time
        
        # 按访问顺序整理AQI
        ordered_aqi = [aqi_list[i] for i in order]
        
        logger.info(f"规划完成: 总代价={total_cost:.4f}, 顺序={order}, 耗时={elapsed:.3f}s")
        
        return order, total_cost, ordered_aqi


# 向后兼容
def plan_route(destinations, preference='balanced', alpha=None, beta=None):
    planner = RoutePlanner()
    return planner.plan(destinations, preference, alpha, beta)


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    planner = RoutePlanner()
    test = ["天府广场", "宽窄巷子", "武侯祠"]
    
    try:
        order, cost, aqi = planner.plan(test, "balanced")
        print(f"\n成功! 顺序: {order}")
        print(f"地点: {[test[i] for i in order]}")
        print(f"代价: {cost:.4f}, AQI: {aqi}")
    except Exception as e:
        print(f"\n失败: {e}")
        import traceback
        traceback.print_exc()