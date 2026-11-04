"""
utils.py
工具函数集合
"""

from fetch_aqi_openmeteo import fetch_aqi_by_location

def estimate_aqi(lat: float, lng: float) -> float:
    """
    通过 Open-Meteo API 获取指定坐标的实时 AQI
    如果失败，返回默认值 50.0
    """
    aqi = fetch_aqi_by_location(lat, lng)
    return float(aqi) if aqi is not None else 50.0