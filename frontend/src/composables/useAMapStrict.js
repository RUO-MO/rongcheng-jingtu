// AI辅助生成：DeepSeek-R1, 2026-03-25 - 高德地图功能封装
// AI辅助生成：Kimi K2.5, 2026-04-15 - 实时导航功能
import { shallowRef, onUnmounted } from 'vue'

export function useAMapStrict(containerId) {
  // 关键：使用纯闭包变量，不在 Vue 的任何响应式结构中暴露
  let mapInstance = null
  let drivingInstance = null
  let navigationInstance = null
  let geolocationInstance = null
  let currentMarker = null
  
  // 只有这些业务数据是响应式的
  const routeInfo = shallowRef(null)
  const loading = shallowRef(false)
  const error = shallowRef(null)
  const navigationStatus = shallowRef('idle') // idle, navigating, paused

  const init = (options = {}) => {
    if (!window.AMap) {
      error.value = new Error('SDK not loaded')
      return false
    }

    try {
      // 直接实例化，不经过任何 Vue 的 ref/reactive
      mapInstance = new window.AMap.Map(containerId, {
        zoom: 13,
        center: [104.0668, 30.5728],
        ...options
      })

      // 关键：使用更安全的隔离方式，而不是完全冻结
      // 避免在高德地图2.0版本中冻结对象导致属性修改失败
      if (process.env.NODE_ENV === 'development') {
        // 只冻结部分可能引起问题的属性，而不是整个对象
        try {
          Object.defineProperty(mapInstance, '__vue_skip__', {
            value: true,
            writable: false,
            enumerable: false,
            configurable: false
          })
        } catch (e) {
          // 如果定义属性失败，使用更轻量的保护
          console.warn('无法设置防遍历属性，地图实例可能被Vue遍历')
        }
      }

      return true
    } catch (e) {
      error.value = e
      console.error('Map init error:', e)
      return false
    }
  }

  const searchRoute = async (start, end, waypoints = []) => {
    if (!mapInstance) {
      error.value = new Error('Map not initialized')
      return
    }

    loading.value = true
    error.value = null

    // 懒加载 Driving 插件，确保获取的是原始构造函数
    return new Promise((resolve, reject) => {
      window.AMap.plugin(['AMap.Driving'], () => {
        try {
          // 每次都创建新实例，避免状态累积
          if (drivingInstance) {
            drivingInstance.clear()
          }
          
          drivingInstance = new window.AMap.Driving({
            map: mapInstance,
            policy: window.AMap.DrivingPolicy.LEAST_TIME
          })

          // 强制将输入参数转换为纯数组，切断可能的 Proxy 链
          const startLngLat = Array.isArray(start) ? start : [start.lng, start.lat]
          const endLngLat = Array.isArray(end) ? end : [end.lng, end.lat]
          
          drivingInstance.search(
            startLngLat,
            endLngLat,
            { waypoints: waypoints.map(w => Array.isArray(w) ? w : [w.lng, w.lat]) },
            (status, result) => {
              loading.value = false
              
              if (status === 'complete') {
                // 立即提取纯 JSON 数据，不保留任何高德对象引用
                const route = result.routes?.[0]
                
                // 处理路径数据，展平所有步骤的路径点
                const allPathPoints = []
                const steps = route?.steps || []
                
                steps.forEach((step, index) => {
                  if (step.path && step.path.length > 0) {
                    step.path.forEach(point => {
                      allPathPoints.push({
                        lng: point.lng || point[0],
                        lat: point.lat || point[1],
                        stepIndex: index
                      })
                    })
                  }
                })
                
                routeInfo.value = {
                  distance: route?.distance,
                  time: route?.time,
                  // 深拷贝路径点，防止高德返回的 LngLat 对象被 Vue 代理
                  path: JSON.parse(JSON.stringify(route?.steps?.flatMap(s => s.path) || [])),
                  steps: JSON.parse(JSON.stringify(steps)),
                  allPathPoints: allPathPoints,
                  destination: endLngLat
                }
                resolve(routeInfo.value)
                
                // 路线显示后不清除，保持在地图上
                // 下次搜索时会自动清除
              } else {
                // 高德错误通常是字符串或简单对象
                const msg = typeof result === 'string' ? result : JSON.stringify(result)
                error.value = new Error(msg)
                reject(error.value)
                
                // 错误时清除实例
                drivingInstance?.clear()
                drivingInstance = null
              }
            }
          )
        } catch (e) {
          loading.value = false
          error.value = e
          reject(e)
        }
      })
    })
  }

  // 计算两点之间的距离（米）
  const calculateDistance = (point1, point2) => {
    const lng1 = point1.lng || point1[0]
    const lat1 = point1.lat || point1[1]
    const lng2 = point2.lng || point2[0]
    const lat2 = point2.lat || point2[1]
    
    const rad1 = lat1 * Math.PI / 180
    const rad2 = lat2 * Math.PI / 180
    const a = rad1 - rad2
    const b = lng1 * Math.PI / 180 - lng2 * Math.PI / 180
    const s = 2 * Math.asin(Math.sqrt(Math.pow(Math.sin(a/2), 2) + 
      Math.cos(rad1) * Math.cos(rad2) * Math.pow(Math.sin(b/2), 2)))
    return s * 6378137
  }

  // 计算点到线段的距离和投影点
  const pointToSegmentDistance = (point, segStart, segEnd) => {
    const x = point.lng || point[0]
    const y = point.lat || point[1]
    const x1 = segStart.lng || segStart[0]
    const y1 = segStart.lat || segStart[1]
    const x2 = segEnd.lng || segEnd[0]
    const y2 = segEnd.lat || segEnd[1]
    
    const A = x - x1
    const B = y - y1
    const C = x2 - x1
    const D = y2 - y1
    
    const dot = A * C + B * D
    const lenSq = C * C + D * D
    let param = -1
    
    if (lenSq !== 0) {
      param = dot / lenSq
    }
    
    let xx, yy
    
    if (param < 0) {
      xx = x1
      yy = y1
    } else if (param > 1) {
      xx = x2
      yy = y2
    } else {
      xx = x1 + param * C
      yy = y1 + param * D
    }
    
    const dx = x - xx
    const dy = y - yy
    
    return {
      distance: Math.sqrt(dx * dx + dy * dy) * 111320, // 转换为米（近似）
      projection: { lng: xx, lat: yy },
      param: param
    }
  }

  // 找到当前位置在路线上的最近点
  const findNearestPointOnRoute = (currentPos, pathPoints) => {
    if (!pathPoints || pathPoints.length < 2) {
      return { index: 0, distance: Infinity, projection: null }
    }
    
    let minDistance = Infinity
    let nearestIndex = 0
    let nearestProjection = null
    
    for (let i = 0; i < pathPoints.length - 1; i++) {
      const segStart = pathPoints[i]
      const segEnd = pathPoints[i + 1]
      
      const result = pointToSegmentDistance(currentPos, segStart, segEnd)
      
      if (result.distance < minDistance) {
        minDistance = result.distance
        nearestIndex = i
        nearestProjection = result.projection
      }
    }
    
    return {
      index: nearestIndex,
      distance: minDistance,
      projection: nearestProjection
    }
  }

  // 计算从当前位置到终点的剩余距离
  const calculateRemainingDistance = (currentIndex, pathPoints) => {
    if (!pathPoints || currentIndex >= pathPoints.length - 1) {
      return 0
    }
    
    let remaining = 0
    for (let i = currentIndex; i < pathPoints.length - 1; i++) {
      remaining += calculateDistance(pathPoints[i], pathPoints[i + 1])
    }
    return remaining
  }

  // 更新当前位置标记
  const updateCurrentPositionMarker = (position) => {
    if (!mapInstance) return
    
    try {
      if (currentMarker) {
        currentMarker.setPosition(position)
      } else {
        currentMarker = new window.AMap.Marker({
          position: position,
          map: mapInstance,
          icon: new window.AMap.Icon({
            size: new window.AMap.Size(24, 24),
            image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png',
            imageSize: new window.AMap.Size(24, 24)
          }),
          offset: new window.AMap.Pixel(-12, -24)
        })
      }
    } catch (e) {
      console.warn('更新位置标记失败:', e)
    }
  }

  const startNavigation = async (start, end, waypoints = []) => {
    if (!mapInstance) {
      error.value = new Error('Map not initialized')
      return Promise.reject(error.value)
    }

    return new Promise((resolve, reject) => {
      window.AMap.plugin(['AMap.Driving', 'AMap.Geolocation'], () => {
        try {
          // 初始化定位服务
          if (!geolocationInstance) {
            geolocationInstance = new window.AMap.Geolocation({
              enableHighAccuracy: true,
              timeout: 10000,
              maximumAge: 0,
              convert: true
            })
          }

          // 获取当前位置
          geolocationInstance.getCurrentPosition((status, result) => {
            if (status === 'complete') {
              const currentPosition = [result.position.lng, result.position.lat]
              
              // 创建导航实例
              if (navigationInstance) {
                navigationInstance.destroy()
              }

              navigationInstance = new window.AMap.Driving({
                map: mapInstance,
                policy: window.AMap.DrivingPolicy.LEAST_TIME,
                showTraffic: true
              })

              // 强制将输入参数转换为纯数组，切断可能的 Proxy 链
              const startLngLat = Array.isArray(start) ? start : [start.lng, start.lat]
              const endLngLat = Array.isArray(end) ? end : [end.lng, end.lat]
              
              navigationInstance.search(
                startLngLat,
                endLngLat,
                { waypoints: waypoints.map(w => Array.isArray(w) ? w : [w.lng, w.lat]) },
                (status, result) => {
                  if (status === 'complete') {
                    navigationStatus.value = 'navigating'
                    
                    // 提取导航信息
                    const route = result.routes?.[0]
                    const steps = route?.steps || []
                    
                    // 处理路径数据
                    const allPathPoints = []
                    steps.forEach((step, index) => {
                      if (step.path && step.path.length > 0) {
                        step.path.forEach(point => {
                          allPathPoints.push({
                            lng: point.lng || point[0],
                            lat: point.lat || point[1],
                            stepIndex: index
                          })
                        })
                      }
                    })
                    
                    const navigationInfo = {
                      distance: route?.distance,
                      time: route?.time,
                      steps: steps,
                      allPathPoints: allPathPoints,
                      currentStep: 0,
                      currentPosition: currentPosition,
                      destination: endLngLat,
                      lastUpdateTime: Date.now()
                    }
                    
                    // 更新路线信息
                    routeInfo.value = {
                      distance: route?.distance,
                      time: route?.time,
                      path: JSON.parse(JSON.stringify(route?.steps?.flatMap(s => s.path) || [])),
                      steps: JSON.parse(JSON.stringify(steps)),
                      allPathPoints: allPathPoints,
                      destination: endLngLat
                    }
                    
                    // 更新当前位置标记
                    updateCurrentPositionMarker(currentPosition)
                    
                    resolve(navigationInfo)
                  } else {
                    const msg = typeof result === 'string' ? result : JSON.stringify(result)
                    error.value = new Error(msg)
                    reject(error.value)
                  }
                }
              )
            } else {
              error.value = new Error('获取当前位置失败')
              reject(error.value)
            }
          })
        } catch (e) {
          error.value = e
          reject(e)
        }
      })
    })
  }

  const updateNavigation = (currentPosition) => {
    if (!routeInfo.value) {
      return null
    }

    try {
      const allPathPoints = routeInfo.value.allPathPoints
      const steps = routeInfo.value.steps
      
      if (!allPathPoints || allPathPoints.length < 2) {
        return null
      }

      // 找到当前位置在路线上的最近点
      const nearestResult = findNearestPointOnRoute(currentPosition, allPathPoints)
      
      // 偏离检测（距离路线超过50米认为偏离）
      const isOffRoute = nearestResult.distance > 50
      
      // 获取当前所在的步骤
      const currentStepIndex = allPathPoints[nearestResult.index]?.stepIndex || 0
      const currentStep = steps[currentStepIndex]
      const nextStep = steps[currentStepIndex + 1]
      
      // 计算剩余距离
      const remainingDistance = calculateRemainingDistance(nearestResult.index, allPathPoints)
      
      // 计算剩余时间（基于平均速度或默认速度）
      const avgSpeed = 30 // km/h，可以根据实际情况调整
      const remainingTime = Math.round((remainingDistance / 1000) / avgSpeed * 60) // 分钟
      
      // 获取下一个转向信息
      let nextTurnDirection = '直行'
      let nextTurnType = 'straight'
      let distanceToNext = remainingDistance
      
      if (nextStep) {
        nextTurnDirection = nextStep.action || '直行'
        nextTurnType = getTurnType(nextTurnDirection)
        
        // 计算到下一个转向点的距离
        const nextStepStartPoint = allPathPoints.find(p => p.stepIndex === currentStepIndex + 1)
        if (nextStepStartPoint) {
          const nextStepIndex = allPathPoints.findIndex(p => p.stepIndex === currentStepIndex + 1)
          distanceToNext = calculateRemainingDistance(nearestResult.index, allPathPoints.slice(0, nextStepIndex + 1))
        }
      }
      
      // 检测是否接近目的地（100米内）
      const destination = routeInfo.value.destination
      const distanceToDestination = destination ? calculateDistance(currentPosition, destination) : Infinity
      const isNearDestination = distanceToDestination < 100
      
      // 检测是否到达目的地（20米内）
      const isArrived = distanceToDestination < 20
      
      // 更新当前位置标记
      updateCurrentPositionMarker(currentPosition)
      
      return {
        currentStep: currentStepIndex,
        distanceToNext: Math.round(distanceToNext),
        nextTurnDirection,
        nextTurnType,
        remainingDistance: Math.round(remainingDistance),
        remainingTime,
        isOffRoute,
        isNearDestination,
        isArrived,
        offRouteDistance: Math.round(nearestResult.distance),
        currentPosition
      }
    } catch (e) {
      console.warn('Update navigation error:', e)
      return null
    }
  }

  const getTurnType = (action) => {
    if (!action) return 'straight'
    const actionLower = action.toLowerCase()
    if (actionLower.includes('右转')) return 'right'
    if (actionLower.includes('左转')) return 'left'
    if (actionLower.includes('掉头')) return 'u-turn'
    if (actionLower.includes('靠左')) return 'keep-left'
    if (actionLower.includes('靠右')) return 'keep-right'
    return 'straight'
  }

  const stopNavigation = () => {
    try {
      navigationInstance?.destroy()
      navigationInstance = null
      navigationStatus.value = 'idle'
      
      // 清除当前位置标记
      if (currentMarker) {
        currentMarker.setMap(null)
        currentMarker = null
      }
    } catch (e) {
      console.warn('Stop navigation error:', e)
    }
  }

  const setCenter = (lnglat, zoom = null) => {
    if (!mapInstance) {
      console.warn('Map not initialized')
      return
    }
    try {
      mapInstance.setCenter(lnglat)
      if (zoom !== null) {
        mapInstance.setZoom(zoom)
      }
    } catch (e) {
      console.warn('Set center error:', e)
    }
  }

  const fitBounds = (coordinates) => {
    if (!mapInstance || !coordinates || coordinates.length === 0) {
      console.warn('Map not initialized or coordinates empty')
      return
    }
    try {
      // 创建边界框
      const bounds = new window.AMap.Bounds(
        coordinates[0],
        coordinates[coordinates.length - 1]
      )
      mapInstance.setBounds(bounds)
    } catch (e) {
      console.warn('Fit bounds error:', e)
      // 降级方案：使用 setFitView
      try {
        const markers = coordinates.map(coord => new window.AMap.Marker({ position: coord }))
        mapInstance.setFitView(markers)
        // 清理临时标记
        setTimeout(() => markers.forEach(m => m.setMap(null)), 100)
      } catch (e2) {
        console.warn('Fallback fit bounds error:', e2)
      }
    }
  }

  const clearRoute = () => {
    try {
      drivingInstance?.clear()
      drivingInstance = null
      routeInfo.value = null
    } catch (e) {
      console.warn('Clear route error:', e)
    }
  }

  const destroy = () => {
    try {
      drivingInstance?.clear()
      navigationInstance?.destroy()
      geolocationInstance?.destroy()
      
      // 清除当前位置标记
      if (currentMarker) {
        currentMarker.setMap(null)
        currentMarker = null
      }
      
      mapInstance?.destroy()
      drivingInstance = null
      navigationInstance = null
      geolocationInstance = null
      mapInstance = null
    } catch (e) {
      console.warn('Cleanup error:', e)
    }
  }

  onUnmounted(destroy)

  // 绝不返回 mapInstance 或 drivingInstance！
  return {
    routeInfo,
    loading,
    error,
    navigationStatus,
    init,
    searchRoute,
    startNavigation,
    updateNavigation,
    stopNavigation,
    clearRoute,
    setCenter,
    fitBounds,
    destroy
  }
}
