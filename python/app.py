# AI辅助生成：DeepSeek-R1, 2026-03-10 - 系统架构设计
# AI辅助生成：DeepSeek-R1, 2026-03-25 - Flask后端框架

#import sys
#import os
#sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
"""
app.py
蓉城净途 - 智能健康导航后端服务
"""

import os
import sys
import time
import uuid
import logging
import math
import traceback

from flask import Flask, request, jsonify, render_template, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.exceptions import BadRequest

from route_planner import RoutePlanner
from config import MAX_DESTINATIONS, DEFAULT_ALPHA, DEFAULT_BETA

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG查看详细信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 创建应用
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rongcheng-jingtu-dev-secret')

CORS(app, resources={r"/api/*": {"origins": "*"}})

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins='*')

# 初始化规划器
try:
    planner = RoutePlanner()
    logger.info("✓ RoutePlanner 初始化完成")
except Exception as e:
    logger.error(f"✗ RoutePlanner 初始化失败: {e}")
    logger.error(traceback.format_exc())
    raise

@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())[:8]
    g.start_time = time.time()
    logger.info(f"→ {request.method} {request.path} | ID: {g.request_id}")

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    logger.info(f"← {request.method} {request.path} | {response.status_code} | {duration:.3f}s")
    response.headers['X-Request-ID'] = g.request_id
    return response

@app.route('/api/plan', methods=['POST'])
def plan_route():
    request_id = g.request_id
    logger.info(f"收到规划请求 | ID: {request_id}")
    
    try:
        # 解析请求
        data = request.get_json(force=True)
        logger.debug(f"请求数据: {data}")
    except Exception as e:
        logger.error(f"JSON解析失败: {e}")
        return jsonify({'error': 'JSON格式错误', 'request_id': request_id}), 400
    
    # 验证参数
    destinations = data.get('destinations', [])
    if not isinstance(destinations, list) or len(destinations) == 0:
        logger.warning(f"参数错误: destinations无效")
        return jsonify({'error': 'destinations必须是有效数组', 'request_id': request_id}), 400
    
    if len(destinations) > MAX_DESTINATIONS:
        return jsonify({'error': f'目的地不能超过{MAX_DESTINATIONS}个', 'request_id': request_id}), 400
    
    # 检查是否直接传递坐标
    coordinates = data.get('coordinates', [])
    
    preference = data.get('preference', 'balanced')
    # 根据preference设置alpha和beta
    if preference == 'shortest':
        alpha = 1.0
        beta = 0.0
    elif preference == 'green':
        alpha = 0.0
        beta = 1.0
    else:  # balanced
        try:
            alpha = float(data.get('alpha', DEFAULT_ALPHA))
            beta = float(data.get('beta', DEFAULT_BETA))
        except (ValueError, TypeError):
            return jsonify({'error': 'alpha/beta必须是数字', 'request_id': request_id}), 400
    
    # 执行规划
    try:
        if coordinates and len(coordinates) == len(destinations):
            # 使用直接传递的坐标
            logger.info(f"开始规划: 使用直接传递的坐标 | 偏好={preference}")
            # 转换坐标格式为 (lat, lng)
            coords = []
            for coord in coordinates:
                if isinstance(coord, list) and len(coord) == 2:
                    try:
                        coords.append((float(coord[1]), float(coord[0])))
                    except (ValueError, TypeError):
                        return jsonify({'error': '坐标格式错误', 'request_id': request_id}), 400
                else:
                    return jsonify({'error': '坐标格式错误', 'request_id': request_id}), 400
            
            # 构建代价矩阵
            cost_matrix, aqi_list = planner.build_cost_matrix(coords, alpha, beta, preference)
            # 求解TSP
            order = planner.solve_tsp(cost_matrix)
            total_cost = 0.0
            for k in range(len(order) - 1):
                i, j = order[k], order[k + 1]
                total_cost += cost_matrix[i][j]
            if len(order) > 1:
                total_cost += cost_matrix[order[-1]][order[0]]
            names = destinations
            ordered_coords = [coords[i] for i in order]
        else:
            # 使用地点名称
            destinations = [d.strip() for d in destinations if isinstance(d, str) and d.strip()]
            logger.info(f"开始规划: {destinations} | 偏好={preference}")
            
            order, total_cost, aqi_list = planner.plan(
                destinations, 
                preference=preference, 
                alpha=alpha, 
                beta=beta
            )
            
            names = [destinations[i] for i in order]
            
            logger.info(f"规划成功: 顺序={order}, 代价={total_cost:.4f}")
            
            # 获取坐标数据
            coords = planner.geocode_destinations(destinations)
            ordered_coords = [coords[i] for i in order]
        
        # 转换为前端需要的格式 [lng, lat]
        formatted_coords = [[lng, lat] for lat, lng in ordered_coords]
        
        # 计算实际距离
        total_distance = 0.0
        # 映射偏好到路线策略
        strategy_map = {
            'shortest': 2,  # 最短距离
            'green': 0,      # 最绿色路线基于后端AQI计算，这里使用最快路线
            'balanced': 0    # 最快
        }
        strategy = strategy_map.get(preference, 0)
        
        for i in range(len(ordered_coords) - 1):
            try:
                distance = planner.client.get_driving_distance(ordered_coords[i], ordered_coords[i+1], strategy)
                total_distance += distance
            except Exception as e:
                logger.error(f"计算距离失败: {e}")
        
        # 转换为公里
        distance_km = round(total_distance / 1000, 2)
        
        # 计算健康评分，基于AQI和距离综合评估
        # 健康分 = 100 - (平均AQI / 2) - (距离惩罚)
        avg_aqi = sum(aqi_list) / len(aqi_list) if aqi_list else 50
        # 距离惩罚：每10km扣5分
        distance_penalty = min(distance_km / 2, 30)  # 最多扣30分
        # AQI惩罚：AQI越高扣分越多
        aqi_penalty = min(avg_aqi / 2, 50)  # 最多扣50分
        
        health_score = max(0, min(100, round(100 - aqi_penalty - distance_penalty, 1)))
        
        # 构建地点顺序详情（包含起点）
        route_stops = []
        for idx, (name, aqi, coord) in enumerate(zip(names, aqi_list, formatted_coords)):
            route_stops.append({
                'index': idx,
                'name': name,
                'aqi': aqi,
                'coordinate': coord,
                'is_start': idx == 0
            })
        
        # 确保所有数值都是合法的JSON值（替换NaN和inf）
        def sanitize_json_value(value):
            if isinstance(value, (int, float)):
                if math.isnan(value):
                    return 0.0
                elif math.isinf(value):
                    return float('1e308') if value > 0 else float('-1e308')
            return value
        
        return jsonify({
            'order': order,
            'names': names,
            'route_stops': route_stops,
            'total_cost': sanitize_json_value(round(total_cost, 4)),
            'health_score': sanitize_json_value(health_score),
            'avg_aqi': sanitize_json_value(round(avg_aqi, 1)),
            'aqi': [sanitize_json_value(aqi) for aqi in aqi_list],
            'coordinates': formatted_coords,
            'distance': f"{distance_km} km",
            'distance_km': sanitize_json_value(distance_km),
            'total_distance': sanitize_json_value(total_distance),
            'preference': preference,
            'message': 'success',
            'request_id': request_id
        }), 200
        
    except Exception as e:
        logger.exception(f"规划失败: {str(e)}")
        return jsonify({
            'error': '规划服务异常',
            'message': str(e),
            'type': type(e).__name__,
            'request_id': request_id
        }), 500

@app.route('/api/navigate', methods=['POST'])
def start_navigation():
    """开始导航"""
    request_id = g.request_id
    logger.info(f"收到导航请求 | ID: {request_id}")
    
    try:
        data = request.get_json(force=True)
        logger.debug(f"导航请求数据: {data}")
    except Exception as e:
        logger.error(f"JSON解析失败: {e}")
        return jsonify({'error': 'JSON格式错误', 'request_id': request_id}), 400
    
    # 验证参数
    route_id = data.get('route_id')
    current_location = data.get('current_location')
    
    if not route_id:
        return jsonify({'error': 'route_id不能为空', 'request_id': request_id}), 400
    
    if not current_location or not isinstance(current_location, list) or len(current_location) != 2:
        return jsonify({'error': 'current_location必须是[longitude, latitude]格式', 'request_id': request_id}), 400
    
    try:
        # 实际项目中，这里应该从数据库或缓存中获取路线数据
        # 这里使用模拟数据，但结构与真实数据一致
        navigation_data = {
            'route_id': route_id,
            'status': 'started',
            'current_location': current_location,
            'estimated_time': 1800,  # 30分钟
            'estimated_distance': 5000,  # 5公里
            'next_turn': '前方100米右转',
            'distance_to_next': 100,
            'message': '导航已开始',
            'request_id': request_id
        }
        
        logger.info(f"导航开始: {route_id}")
        return jsonify(navigation_data), 200
        
    except Exception as e:
        logger.exception(f"导航启动失败: {str(e)}")
        return jsonify({
            'error': '导航服务异常',
            'message': str(e),
            'type': type(e).__name__,
            'request_id': request_id
        }), 500

@app.route('/api/navigate/update', methods=['POST'])
def update_navigation():
    """更新导航位置"""
    request_id = g.request_id
    logger.info(f"收到导航更新请求 | ID: {request_id}")
    
    try:
        data = request.get_json(force=True)
        logger.debug(f"导航更新数据: {data}")
    except Exception as e:
        logger.error(f"JSON解析失败: {e}")
        return jsonify({'error': 'JSON格式错误', 'request_id': request_id}), 400
    
    # 验证参数
    route_id = data.get('route_id')
    current_location = data.get('current_location')
    
    if not route_id:
        return jsonify({'error': 'route_id不能为空', 'request_id': request_id}), 400
    
    if not current_location or not isinstance(current_location, list) or len(current_location) != 2:
        return jsonify({'error': 'current_location必须是[longitude, latitude]格式', 'request_id': request_id}), 400
    
    try:
        # 实际项目中，这里应该根据当前位置计算导航状态
        # 这里使用模拟数据，但结构与真实数据一致
        import random
        
        # 模拟导航状态更新
        turns = ['前方100米右转', '前方200米左转', '前方300米直行', '前方50米右转']
        next_turn = random.choice(turns)
        distance_to_next = random.randint(50, 300)
        estimated_time_remaining = random.randint(1200, 1800)
        estimated_distance_remaining = random.randint(3000, 5000)
        
        navigation_update = {
            'route_id': route_id,
            'status': 'navigating',
            'current_location': current_location,
            'next_turn': next_turn,
            'distance_to_next': distance_to_next,
            'estimated_time_remaining': estimated_time_remaining,
            'estimated_distance_remaining': estimated_distance_remaining,
            'message': '导航更新成功',
            'request_id': request_id
        }
        
        logger.info(f"导航更新: {route_id}")
        return jsonify(navigation_update), 200
        
    except Exception as e:
        logger.exception(f"导航更新失败: {str(e)}")
        return jsonify({
            'error': '导航服务异常',
            'message': str(e),
            'type': type(e).__name__,
            'request_id': request_id
        }), 500

@app.route('/api/navigate/cancel', methods=['POST'])
def cancel_navigation():
    """取消导航"""
    request_id = g.request_id
    logger.info(f"收到导航取消请求 | ID: {request_id}")
    
    try:
        data = request.get_json(force=True)
        logger.debug(f"导航取消数据: {data}")
    except Exception as e:
        logger.error(f"JSON解析失败: {e}")
        return jsonify({'error': 'JSON格式错误', 'request_id': request_id}), 400
    
    # 验证参数
    route_id = data.get('route_id')
    
    if not route_id:
        return jsonify({'error': 'route_id不能为空', 'request_id': request_id}), 400
    
    try:
        # 模拟导航取消
        cancel_data = {
            'route_id': route_id,
            'status': 'cancelled',
            'message': '导航已取消',
            'request_id': request_id
        }
        
        logger.info(f"导航取消: {route_id}")
        return jsonify(cancel_data), 200
        
    except Exception as e:
        logger.exception(f"导航取消失败: {str(e)}")
        return jsonify({
            'error': '导航服务异常',
            'message': str(e),
            'type': type(e).__name__,
            'request_id': request_id
        }), 500

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    """处理客户端连接"""
    client_id = request.sid
    logger.info(f"客户端连接: {client_id}")
    emit('connected', {'message': '连接成功', 'client_id': client_id})

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接"""
    client_id = request.sid
    logger.info(f"客户端断开: {client_id}")

@socketio.on('start_navigation')
def handle_start_navigation(data):
    """处理开始导航请求"""
    client_id = request.sid
    route_id = data.get('route_id')
    current_location = data.get('current_location')
    
    logger.info(f"WebSocket导航开始: {route_id} | 客户端: {client_id}")
    
    # 模拟导航数据
    navigation_data = {
        'route_id': route_id,
        'status': 'started',
        'estimated_time': 1800,
        'estimated_distance': 5000,
        'message': '导航已开始',
        'client_id': client_id
    }
    
    emit('navigation_started', navigation_data)

@socketio.on('update_position')
def handle_update_position(data):
    """处理位置更新"""
    client_id = request.sid
    route_id = data.get('route_id')
    current_location = data.get('current_location')
    
    logger.info(f"WebSocket位置更新: {route_id} | 客户端: {client_id}")
    
    # 模拟导航更新
    navigation_update = {
        'route_id': route_id,
        'status': 'navigating',
        'current_location': current_location,
        'next_turn': '前方100米右转',
        'distance_to_next': 100,
        'estimated_time_remaining': 1500,
        'estimated_distance_remaining': 4000,
        'message': '导航更新成功',
        'client_id': client_id
    }
    
    emit('navigation_updated', navigation_update)

@socketio.on('stop_navigation')
def handle_stop_navigation(data):
    """处理停止导航请求"""
    client_id = request.sid
    route_id = data.get('route_id')
    
    logger.info(f"WebSocket导航停止: {route_id} | 客户端: {client_id}")
    
    # 模拟导航取消
    cancel_data = {
        'route_id': route_id,
        'status': 'cancelled',
        'message': '导航已停止',
        'client_id': client_id
    }
    
    emit('navigation_stopped', cancel_data)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'planner_initialized': planner is not None,
        'timestamp': time.time(),
        'request_id': getattr(g, 'request_id', 'N/A')
    }), 200

@app.route('/')
def index():
    return jsonify({
        'message': '蓉城净途后端服务',
        'version': '1.0.0',
        'status': 'running'
    })

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("启动 蓉城净途 服务")
    logger.info("=" * 50)
    
    socketio.run(
        app,
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=True
    )