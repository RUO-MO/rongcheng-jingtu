# api_client.py
import requests
import time
from config import AMAP_API_KEY, REQUEST_TIMEOUT

class AMapClient:
    def __init__(self, api_key: str = AMAP_API_KEY):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3"
        self.last_request_time = 0
        self.request_interval = 0.1  # 100ms间隔
        self.cache = {}
        self.cache_expiry = 3600  # 缓存过期时间（秒）

    def geocode(self, address: str, city: str = "成都") -> tuple:
        """
        地址转坐标
        返回: (纬度, 经度)
        """
        # 生成缓存键
        cache_key = f"geocode:{address}:{city}"
        
        # 检查缓存
        current_time = time.time()
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if current_time - cached_data['timestamp'] < self.cache_expiry:
                return cached_data['result']
        
        # 请求节流
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        
        url = f"{self.base_url}/geocode/geo"
        params = {
            "key": self.api_key,
            "address": address,
            "city": city,
            "output": "json"
        }
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        self.last_request_time = time.time()
        
        data = resp.json()
        if data["status"] != "1" or not data["geocodes"]:
            raise Exception(f"地理编码失败: {data.get('info')}")
        location = data["geocodes"][0]["location"]  # "经度,纬度"
        lng, lat = map(float, location.split(","))
        result = (lat, lng)
        
        # 缓存结果
        self.cache[cache_key] = {
            'result': result,
            'timestamp': current_time
        }
        
        return result

    def get_driving_distance(self, origin: tuple, destination: tuple, strategy: int = 0) -> float:
        """
        计算两点间驾车距离（米）
        origin/destination: (纬度, 经度)
        strategy: 路线策略（0: 最快, 2: 最短, 4: 最经济）
        """
        # 生成缓存键
        cache_key = f"distance:{origin[0]}:{origin[1]}:{destination[0]}:{destination[1]}:{strategy}"
        
        # 检查缓存
        current_time = time.time()
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if current_time - cached_data['timestamp'] < self.cache_expiry:
                return cached_data['result']
        
        # 请求节流
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        
        url = f"{self.base_url}/direction/driving"
        origin_str = f"{origin[1]},{origin[0]}"  # 经度,纬度
        dest_str = f"{destination[1]},{destination[0]}"
        params = {
            "key": self.api_key,
            "origin": origin_str,
            "destination": dest_str,
            "strategy": strategy,
            "output": "json"
        }
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        self.last_request_time = time.time()
        
        data = resp.json()
        if data["status"] != "1":
            raise Exception(f"路径规划失败: {data.get('info')}")
        result = float(data["route"]["paths"][0]["distance"])
        
        # 缓存结果
        self.cache[cache_key] = {
            'result': result,
            'timestamp': current_time
        }
        
        return result

    def distance_matrix(self, origins: list, destinations: list = None) -> list:
        """
        计算多个起点到多个目的地的距离矩阵（米）
        origins: 起点坐标列表 [(lat, lng), ...]
        destinations: 终点坐标列表，若为 None 则等于 origins
        返回二维列表 matrix[i][j] 表示第 i 个起点到第 j 个终点的距离
        """
        if destinations is None:
            destinations = origins
        n = len(origins)
        m = len(destinations)
        matrix = [[0.0] * m for _ in range(n)]
        for i, o in enumerate(origins):
            for j, d in enumerate(destinations):
                if i == j and origins is destinations:  # 同一点距离为0
                    matrix[i][j] = 0.0
                else:
                    try:
                        dist = self.get_driving_distance(o, d)
                        matrix[i][j] = dist
                        time.sleep(0.1)  # 避免触发频率限制
                    except Exception as e:
                        print(f"获取距离失败 ({o} -> {d}): {e}")
                        matrix[i][j] = float('inf')
        return matrix

    def get_traffic_condition(self, origin: tuple, destination: tuple) -> dict:
        """
        获取两点间交通状况
        origin/destination: (纬度, 经度)
        返回交通状况信息
        """
        url = f"{self.base_url}/direction/driving"
        origin_str = f"{origin[1]},{origin[0]}"  # 经度,纬度
        dest_str = f"{destination[1]},{destination[0]}"
        params = {
            "key": self.api_key,
            "origin": origin_str,
            "destination": dest_str,
            "output": "json",
            "extensions": "all"  # 获取详细信息，包括交通状况
        }
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        if data["status"] != "1":
            raise Exception(f"交通状况查询失败: {data.get('info')}")
        
        path = data["route"]["paths"][0]
        return {
            "distance": float(path.get("distance", 0)),
            "duration": float(path.get("duration", 0)),
            "traffic_condition": path.get("traffic_condition", "未知"),
            "congestion_distance": float(path.get("congestion_distance", 0)),
            "congestion_time": float(path.get("congestion_time", 0))
        }

    def get_realtime_traffic(self, bounds: str) -> dict:
        """
        获取指定区域实时交通状况
        bounds: 矩形区域边界，格式为"西南角经度,西南角纬度,东北角经度,东北角纬度"
        """
        url = f"{self.base_url}/traffic/status/rectangle"
        params = {
            "key": self.api_key,
            "rectangle": bounds,
            "output": "json"
        }
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        if data["status"] != "1":
            raise Exception(f"实时交通查询失败: {data.get('info')}")
        
        return data.get("trafficinfo", {})