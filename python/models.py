# models.py
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Location:
    """地点信息"""
    name: str
    lat: float
    lng: float
    aqi: Optional[float] = None   # 可选，该点的空气质量指数

@dataclass
class Route:
    """路线规划结果"""
    order: List[int]               # 目的地索引顺序（按访问顺序）
    total_cost: float               # 总综合代价
    destinations: List[Location]    # 目的地列表
    # 可选的详细矩阵
    distance_matrix: Optional[List[List[float]]] = None
    cost_matrix: Optional[List[List[float]]] = None
    # 路线几何信息（可选，供前端展示）
    path_geojson: Optional[dict] = None