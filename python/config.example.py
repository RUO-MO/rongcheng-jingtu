"""项目配置示例 - 蓉城净途

复制本文件为同目录下的 config.py 后填入自己的密钥：
    copy python\\config.example.py python\\config.py   (Windows)
    cp python/config.example.py python/config.py       (Linux / macOS)

config.py 已被 .gitignore 忽略，请勿将其提交到版本库。
"""

# 高德地图 Web 服务 API Key（后端使用）
# 注意：前端所需的 JS API 安全密钥配置在 frontend/.env，不放在此处
AMAP_API_KEY = ""

# 最大目的地数量（不含起点）
MAX_DESTINATIONS = 7

# 默认权重参数（balanced 模式）
DEFAULT_ALPHA = 0.5  # 距离权重
DEFAULT_BETA = 0.5   # AQI 权重

# 高德接口请求超时时间（秒）
REQUEST_TIMEOUT = 5
