# _core.pyi
from typing import List

def solve_tsp(cost_matrix: List[List[float]]) -> List[int]: ...

def solve_tsp_weighted(distance_matrix: List[List[float]], 
                      aqi_matrix: List[List[float]], 
                      alpha: float, 
                      beta: float) -> List[int]: ...