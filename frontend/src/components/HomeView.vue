<template>
  <!-- AI辅助生成：DeepSeek-R1, 2026-03-25 - 基础Vue3组件框架 -->
  <!-- AI辅助生成：Kimi K2.5, 2026-04-14 - UI/UX优化 -->
  <!-- AI辅助生成：Kimi K2.5, 2026-04-15 - 实时导航功能 -->
  <div class="app-wrapper">
    <!-- 动态背景 -->
    <div class="ambient-bg">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div class="container">

      <!-- 主内容区 -->
      <div class="content-layout">
        <!-- 左侧面板 -->
        <aside class="left-panel" v-if="!isNavigating">
          <div class="panel-content glass-card">
            <!-- 起点输入 -->
            <div class="form-section">
              <div class="section-title">
                <span class="icon">📍</span>
                <span>{{ t('startPoint') }}</span>
              </div>
              <div class="input-group">
                <input 
                  type="text" 
                  v-model="start" 
                  id="start-input"
                  :placeholder="t('startPlaceholder')"
                  ref="startInput"
                />
                <button @click="getLocation" class="icon-btn locate-btn" :title="t('locate')">
                  <span>📡</span>
                </button>
              </div>
            </div>

            <!-- 目的地输入 -->
            <div class="form-section">
              <div class="section-title">
                <span class="icon">🎯</span>
                <span>{{ t('destination') }}</span>
                <span class="max-dest">{{ t('maxDest') }}</span>
              </div>
              <div class="input-group">
                <input 
                  type="text" 
                  v-model="newDest" 
                  @keyup.enter="addDest"
                  :placeholder="t('inputPlaceholder')"
                  ref="destInput"
                />
                <button @click="addDest" class="icon-btn add-btn" :disabled="!newDest.trim()" :title="t('add')">
                  <span>+</span>
                </button>
              </div>

              <!-- 目的地列表 -->
              <transition-group name="tag-list" tag="div" class="dest-tags" v-if="destinations.length">
                <div 
                  v-for="(item, index) in destinations" 
                  :key="`dest-${index}-${item}`"
                  class="dest-tag"
                >
                  <span class="tag-number">{{ index + 1 }}</span>
                  <span class="tag-text" :title="item">{{ item }}</span>
                  <button @click="removeDest(index)" class="tag-remove">×</button>
                </div>
              </transition-group>
              <div v-else class="empty-tip">{{ t('emptyDest') }}</div>
            </div>

            <!-- 固定终点输入 -->
            <div class="form-section">
              <div class="section-title">
                <span class="icon">🏁</span>
                <span>{{ t('fixedEnd') }}</span>
              </div>
              <div class="input-group">
                <input 
                  type="text" 
                  v-model="fixedEnd" 
                  :placeholder="t('inputPlaceholder')"
                />
              </div>
              <div v-if="fixedEnd" class="dest-tag fixed-end-tag">
                <span class="tag-number">终</span>
                <span class="tag-text" :title="fixedEnd">{{ fixedEnd }}</span>
                <button @click="fixedEnd = ''" class="tag-remove">×</button>
              </div>
            </div>

            <!-- 路线偏好 -->
            <div class="form-section">
              <div class="section-title">{{ t('modeTitle') }}</div>
              <div class="mode-selector">
                <button 
                  v-for="m in modes" 
                  :key="m.id"
                  :class="{ active: mode === m.id }"
                  @click="setMode(m.id)"
                  class="mode-btn"
                >
                  <span class="mode-icon">{{ m.icon }}</span>
                  <div class="mode-info">
                    <span class="mode-name">{{ m.name }}</span>
                    <span class="mode-desc">{{ m.desc }}</span>
                  </div>
                </button>
              </div>
            </div>

            <!-- 最优路线方案 -->
            <div class="form-section" v-if="routeResult?.routeStops?.length">
              <div class="section-title">
                <span class="icon">🗺️</span>
                <span>{{ t('routePlan') }}</span>
              </div>
              <div class="route-stops">
                <div class="stops-list">
                  <div 
                    v-for="(stop, index) in routeResult.routeStops" 
                    :key="index"
                    class="stop-item"
                    :class="{ 'start-point': stop.isStart }"
                  >
                    <div class="stop-marker">{{ index + 1 }}</div>
                    <div class="stop-info">
                      <span class="stop-name">{{ stop.name }}</span>
                      <span class="stop-aqi" :style="{ color: getAqiColor(stop.aqi) }">AQI {{ stop.aqi }}</span>
                    </div>
                    <div v-if="index < routeResult.routeStops.length - 1" class="stop-arrow">↓</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 规划按钮 -->
            <button 
              class="plan-btn" 
              @click="planRoute"
              :class="{ 'btn-pulse': canPlan, planning: isPlanning }"
              :disabled="!canPlan || isPlanning"
            >
              <span v-if="!isPlanning" class="btn-icon">🚀</span>
              <span v-else class="spinner"></span>
              <span>{{ isPlanning ? t('planning') : t('plan') }}</span>
            </button>
          </div>
        </aside>

        <!-- 右侧面板 -->
        <main class="right-panel">
          <!-- 地图容器 -->
          <div class="map-wrapper glass-card">
            <div id="map-container" class="map-container"></div>
            <div class="map-loading" v-if="!mapLoaded">
              <div class="loading-spinner"></div>
              <span>{{ t('loadingMap') }}</span>
            </div>
            
            <!-- 地图控制按钮 -->
            <div class="map-controls">
              <button class="map-control-btn" @click="resetMapView" title="重置视图">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                  <path d="M3 3v5h5"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- 导航控制提示 -->
          <transition name="slide-up">
            <div class="navigation-hint-card glass-card" v-if="canStartNavigation && !isNavigating">
              <div class="hint-content">
                <span class="hint-icon">✅</span>
                <div class="hint-text">
                  <div class="hint-title">{{ t('routeComplete') }}</div>
                  <div class="hint-subtitle">{{ t('destinationsCount', { count: destinations.length, distance: routeResult?.distance }) }}</div>
                </div>
              </div>
              <button class="navigate-btn" @click="startRealNavigation">
                <span>{{ t('startNav') }}</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </transition>

          <!-- 路线信息结果 -->
          <transition name="slide-up">
            <div class="route-result glass-card" v-if="routeResult && !isNavigating">
              <div class="result-header">
                <div class="route-badge" :class="mode">{{ routeResult.modeName }}</div>
                <div class="health-score">
                  <svg v-if="routeResult?.healthScore" viewBox="0 0 36 36" class="circular-chart">
                    <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                    <path class="circle" :stroke="getHealthScoreColor(routeResult.healthScore)" :stroke-dasharray="routeResult.healthScore + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                    <text x="18" y="20" class="percentage">{{ routeResult.healthScore }}</text>
                  </svg>
                  <span class="score-label">{{ t('healthScore') }}</span>
                </div>
              </div>

              <div class="stats-grid">
                <div class="stat-box">
                  <div class="stat-icon">📏</div>
                  <div class="stat-value">{{ routeResult.distance }}</div>
                  <div class="stat-label">{{ t('totalDistance') }}</div>
                </div>
                <div class="stat-box" :style="{ '--aqi-color': getAqiColor(routeResult.aqi) }">
                  <div class="stat-icon">🍃</div>
                  <div class="stat-value" :style="{ color: getAqiColor(routeResult.aqi) }">{{ routeResult.aqi }}</div>
                  <div class="stat-label">{{ t('avgAqi') }}</div>
                </div>
                <div class="stat-box">
                  <div class="stat-icon">⏱️</div>
                  <div class="stat-value">{{ routeResult.estimatedTime || '25' }}<small>min</small></div>
                  <div class="stat-label">{{ t('estimateTime') }}</div>
                </div>
              </div>

              <div class="health-tip" :class="{ 'good': routeResult.aqi <= 50, 'moderate': routeResult.aqi > 50 && routeResult.aqi <= 100, 'poor': routeResult.aqi > 100 }">
                <div class="tip-icon">💡</div>
                <div class="tip-text">{{ routeResult.tip }}</div>
              </div>
            </div>
          </transition>
        </main>
      </div>
    </div>

    <!-- 全屏导航界面 - 简化版 -->
    <transition name="fade-scale">
      <div class="simple-navigation-overlay" v-if="isNavigating">
        <!-- 顶部：退出按钮和AQI -->
        <div class="simple-nav-header">
          <button @click="stopNavigation" class="simple-close-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 18L18 6M6 6l12 12"/>
            </svg>
            <span>退出</span>
          </button>
          <div class="simple-aqi" :style="{ background: getAqiGradient(props.currentAqi) }">
            AQI {{ props.currentAqi }}
          </div>
        </div>

        <!-- 中央：大箭头转向提示 -->
        <div class="simple-turn-hint">
          <div class="big-arrow-container">
            <!-- 大箭头图标 - 可旋转并根据方向正确性变色 -->
            <div class="big-turn-arrow" 
                 :class="[nextTurnType, getArrowColorClass]"
                 :style="{ transform: 'rotate(' + arrowRotation + 'deg)' }">
              <svg v-if="nextTurnType === 'right'" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="6">
                <path d="M30 50 L70 50 M70 50 L55 35 M70 50 L55 65" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <svg v-else-if="nextTurnType === 'left'" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="6">
                <path d="M70 50 L30 50 M30 50 L45 35 M30 50 L45 65" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <svg v-else-if="nextTurnType === 'u-turn'" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="6">
                <path d="M65 70 L65 40 Q65 25 50 25 Q35 25 35 40 L35 55" stroke-linecap="round"/>
                <path d="M35 55 L25 45 M35 55 L45 45" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <svg v-else viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="6">
                <path d="M50 30 L50 70 M50 30 L35 45 M50 30 L65 45" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>
          
          <!-- 方向状态提示 -->
          <div class="direction-status" v-if="isCompassAvailable && nextTurnType !== 'straight'">
            <div class="status-dot" :class="getArrowColorClass"></div>
            <span class="status-text">{{ isDirectionCorrect ? '方向正确' : '请调整方向' }}</span>
          </div>
          
          <!-- 距离数字 - 根据距离显示不同颜色 -->
          <div class="big-distance" :class="getDistanceAlertLevel">
            <span class="distance-number">{{ nextTurnDistance }}</span>
            <span class="distance-unit">米</span>
          </div>
          
          <!-- 详细导航提示 -->
          <div class="navigation-hint" :class="getDistanceAlertLevel">
            {{ getNavigationHint }}
          </div>
          
          <!-- 转向文字 -->
          <div class="simple-turn-text">{{ nextTurnDirection }}</div>
        </div>

        <!-- 提前提示（400米和100米） -->
        <transition name="slide-down">
          <div v-if="shouldShowAdvanceNotice" class="advance-notice" :class="getDistanceAlertLevel">
            <span class="notice-icon">{{ getDistanceAlertLevel === 'urgent' ? '⚠️' : '📍' }}</span>
            <span class="notice-text">{{ getAdvanceNoticeText }}</span>
          </div>
        </transition>

        <!-- 底部：简洁信息栏 -->
        <div class="simple-nav-footer">
          <div class="simple-info-bar">
            <div class="simple-info-item">
              <span class="simple-label">剩余</span>
              <span class="simple-value">{{ remainingDistance }}km</span>
            </div>
            <div class="simple-divider"></div>
            <div class="simple-info-item">
              <span class="simple-label">预计</span>
              <span class="simple-value">{{ remainingTime }}分钟</span>
            </div>
            <div class="simple-divider"></div>
            <div class="simple-info-item">
              <span class="simple-label">速度</span>
              <span class="simple-value">{{ currentSpeed || 0 }}km/h</span>
            </div>
          </div>
        </div>

        <!-- 偏离路线提示（简化） -->
        <div v-if="isOffRoute" class="simple-warning">
          <span>⚠️ 已偏离路线</span>
        </div>

        <!-- 到达提示（简化） -->
        <div v-if="isArrived" class="simple-arrived">
          <span>🎉 已到达目的地</span>
        </div>
      </div>
    </transition>

    <!-- Toast 通知 -->
    <div class="toast-container">
      <transition-group name="toast">
        <div 
          v-for="toast in toasts" 
          :key="toast.id"
          class="toast"
          :class="toast.type"
        >
          {{ toast.message }}
        </div>
      </transition-group>
    </div>

    <!-- 备案号 -->
    <div class="icp-footer">
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">
        蜀ICP备2025134557号-2
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAMapStrict } from '../composables/useAMapStrict';

const { t, locale } = useI18n();

// 接收 props
// AI辅助生成：DeepSeek-R1, 2026-03-25 - 基础Vue3组件框架
// AI辅助生成：Kimi K2.5, 2026-04-14 - UI/UX优化
// AI辅助生成：Kimi K2.5, 2026-04-15 - 实时导航功能
const props = defineProps({
  currentAqi: {
    type: Number,
    default: null
  },
  lang: {
    type: String,
    default: 'zh'
  }
});

// 定义事件
const emit = defineEmits(['update:aqi', 'update:navigating']);

// 数据状态
const start = ref("");
const newDest = ref("");
const destinations = ref([]);
const fixedEnd = ref("");
const mode = ref("balance");
const mapLoaded = ref(false);
const isPlanning = ref(false);
const currentSpeed = ref(0);

// 节流和缓存相关
const routeCache = {};
let lastPlanTime = 0;

// 缓存清理函数
const clearRouteCache = (modeToClear = null) => {
  if (modeToClear) {
    // 清理特定模式的缓存
    Object.keys(routeCache).forEach(key => {
      try {
        const cacheData = JSON.parse(key);
        if (cacheData.mode === modeToClear) {
          delete routeCache[key];
          console.log('清理缓存:', key);
        }
      } catch (e) {
        // 如果解析失败，直接删除
        delete routeCache[key];
      }
    });
  } else {
    // 清理所有缓存
    Object.keys(routeCache).forEach(key => {
      delete routeCache[key];
    });
    console.log('清理所有缓存');
  }
};

const modes = computed(() => [
  { id: 'short', name: t('short'), icon: '⚡', desc: t('shortDesc') },
  { id: 'green', name: t('green'), icon: '🌿', desc: t('greenDesc') },
  { id: 'balance', name: t('balance'), icon: '⚖️', desc: t('balanceDesc') }
]);

// 结果状态
const routeResult = ref(null);
const toasts = ref([]);

// 地图相关
const { routeInfo, loading, error, init, searchRoute, startNavigation, updateNavigation, stopNavigation: stopMapNavigation, clearRoute, setCenter, fitBounds, destroy } = useAMapStrict('map-container');
let AMap = null; // 保存AMap实例
let currentPosition = null;
let watchId = null;

// 输入提示相关
const startInput = ref(null);
const destInput = ref(null);
let startAutoComplete = null;
let destAutoComplete = null;



// 导航状态
const isNavigating = ref(false);
const routeId = ref(null);
const nextTurnDirection = ref(t('turnRight'));
const nextTurnDistance = ref(150);
const nextTurnType = ref('right');
const remainingDistance = ref(4.2);
const remainingTime = ref(25);
const navigationInfo = ref(null);
const isOffRoute = ref(false);
const isNearDestination = ref(false);
const isArrived = ref(false);
const offRouteDistance = ref(0);
const currentStep = ref(0);
const totalSteps = ref(0);

// 指南针状态
const deviceOrientation = ref(0);
const compassHeading = ref(0);
const isCompassAvailable = ref(false);
let compassListener = null;


// 计算属性
const canPlan = computed(() => start.value && (destinations.value.length > 0 || fixedEnd.value));
const canStartNavigation = computed(() => routeResult.value !== null && !isNavigating.value);

// 相对转向角度计算
const relativeTurnAngle = computed(() => {
  if (!isCompassAvailable.value) return 0;
  
  // 根据转向类型计算目标角度
  let targetAngle = 0;
  switch (nextTurnType.value) {
    case 'left':
      targetAngle = -90; // 左转相对当前方向是-90度
      break;
    case 'right':
      targetAngle = 90; // 右转相对当前方向是+90度
      break;
    case 'u-turn':
      targetAngle = 180; // 掉头是180度
      break;
    default:
      targetAngle = 0; // 直行
  }
  
  return targetAngle;
});

// 获取转向指示文字
const getRelativeTurnInstruction = computed(() => {
  if (!isCompassAvailable.value) return nextTurnDirection.value;
  
  switch (nextTurnType.value) {
    case 'left':
      return '向左转';
    case 'right':
      return '向右转';
    case 'u-turn':
      return '掉头';
    default:
      return '直行';
  }
});

// 获取当前绝对朝向文字
const getCurrentAbsoluteDirection = computed(() => {
  if (!isCompassAvailable.value) return '';
  return getDirectionText(compassHeading.value);
});

// 计算转向后的绝对方向
const getTargetAbsoluteDirection = computed(() => {
  if (!isCompassAvailable.value) return '';
  
  let targetHeading = compassHeading.value + relativeTurnAngle.value;
  // 标准化到0-360度
  targetHeading = ((targetHeading % 360) + 360) % 360;
  
  return getDirectionText(targetHeading);
});

// 获取完整的转向说明
const getFullTurnInstruction = computed(() => {
  if (!isCompassAvailable.value) return nextTurnDirection.value;
  
  const currentDir = getCurrentAbsoluteDirection.value;
  const targetDir = getTargetAbsoluteDirection.value;
  const turnAction = getRelativeTurnInstruction.value;
  
  if (nextTurnType.value === 'straight') {
    return `保持${currentDir}方向直行`;
  }
  
  return `${turnAction}，面向${targetDir}方向`;
});

// 计算箭头应该旋转的角度（让箭头指向目标方向）
const arrowRotation = computed(() => {
  if (!isCompassAvailable.value) return 0;
  
  // 箭头应该指向目标转向方向
  // 例如：左转(-90度)，箭头应该指向左方
  // 我们使用 relativeTurnAngle 作为目标角度，并考虑设备当前朝向
  let baseRotation = relativeTurnAngle.value;
  
  // 如果设备指南针可用，我们让箭头保持指向绝对目标方向
  // 即：箭头指向 = 目标角度 - 设备朝向
  // 这样当用户转向时，箭头会反向旋转，保持指向目标
  let deviceHeading = compassHeading.value;
  
  // 计算箭头应该指向的角度
  // 目标方向 = 设备朝向 + 相对转向角度
  // 箭头旋转 = 目标方向 - 设备朝向 = 相对转向角度
  // 但我们希望箭头在屏幕上保持指向目标方向，所以需要反向
  let rotation = baseRotation - deviceHeading;
  
  return rotation;
});

// 计算方向偏差（判断用户是否朝向正确）
const directionDeviation = computed(() => {
  if (!isCompassAvailable.value || nextTurnType.value === 'straight') return 0;
  
  // 计算当前朝向与目标转向方向的偏差
  let deviation = Math.abs(relativeTurnAngle.value - 0); // 简化计算
  
  // 标准化到0-180度
  if (deviation > 180) deviation = 360 - deviation;
  
  return deviation;
});

// 判断方向是否正确（偏差小于30度认为正确）
const isDirectionCorrect = computed(() => {
  if (!isCompassAvailable.value) return true;
  if (nextTurnType.value === 'straight') return true;
  
  // 计算当前设备朝向与目标转向方向的偏差
  // 目标转向角度是相对当前方向的，所以偏差就是 compassHeading 与目标角度的差
  let deviceHeading = compassHeading.value;
  let targetAngle = relativeTurnAngle.value;
  
  // 将设备朝向标准化到相对坐标系
  // 如果目标左转(-90度)，设备应该朝向-90度方向
  // 我们计算设备当前朝向与目标朝向的偏差
  let diff = Math.abs(deviceHeading % 360 - (360 + targetAngle) % 360);
  if (diff > 180) diff = 360 - diff;
  
  return diff < 30; // 偏差小于30度认为方向正确
});

// 获取箭头颜色类
const getArrowColorClass = computed(() => {
  if (!isCompassAvailable.value) return 'neutral';
  if (nextTurnType.value === 'straight') return 'correct';
  
  return isDirectionCorrect.value ? 'correct' : 'wrong';
});

// 获取详细的导航提示文字
const getNavigationHint = computed(() => {
  if (!isCompassAvailable.value) {
    return `前方${nextTurnDistance.value}米${nextTurnDirection.value}`;
  }
  
  if (nextTurnType.value === 'straight') {
    return '保持当前方向直行';
  }
  
  // 根据距离给出不同提示
  const distance = nextTurnDistance.value;
  
  if (distance > 400) {
    // 距离还很远
    if (isDirectionCorrect.value) {
      return '方向正确，保持当前方向';
    } else {
      return `请调整方向，准备${nextTurnDirection.value}`;
    }
  } else if (distance > 100) {
    // 400米内提示
    if (isDirectionCorrect.value) {
      return `前方${distance}米路口，保持方向准备${nextTurnDirection.value}`;
    } else {
      return `前方${distance}米路口，请调整方向准备${nextTurnDirection.value}`;
    }
  } else {
    // 100米内，即将转向
    return `即将${nextTurnDirection.value}，请减速`;
  }
});

// 获取距离提示级别（用于显示不同的提示样式）
const getDistanceAlertLevel = computed(() => {
  const distance = nextTurnDistance.value;
  if (distance <= 100) return 'urgent';      // 100米内 - 紧急
  if (distance <= 400) return 'warning';     // 400米内 - 警告
  return 'normal';                           // 正常
});

// 是否需要显示提前提示（400米或100米）
const shouldShowAdvanceNotice = computed(() => {
  const distance = nextTurnDistance.value;
  return distance <= 400 && distance > 350 ||  // 400米提示窗口
         distance <= 100 && distance > 80;      // 100米提示窗口
});

// 获取提前提示文字
const getAdvanceNoticeText = computed(() => {
  const distance = nextTurnDistance.value;
  if (distance <= 100 && distance > 80) {
    return `⚠️ 注意：即将${nextTurnDirection.value}`;
  } else if (distance <= 400 && distance > 350) {
    return `📍 前方400米${nextTurnDirection.value}`;
  }
  return '';
});

// Toast 系统
const showToast = (message, type = 'info') => {
  const id = Date.now();
  toasts.value.push({ id, message, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id);
  }, 3000);
};

// 初始化地图
  const initMapWrapper = async () => {
    try {
      await nextTick();
      const mapContainer = document.getElementById('map-container');
      if (!mapContainer) {
        console.error('地图容器不存在');
        return;
      }
      
      // 强制等待容器尺寸稳定
      const checkSize = () => {
        const rect = mapContainer.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) {
          console.log('容器尺寸为0，等待100ms...');
          setTimeout(checkSize, 100);
          return;
        }
        console.log('容器尺寸稳定:', rect.width, rect.height);
        loadMap();
      };
      
      const loadMap = async () => {
        // 通过 URL 判断语言，而不是依赖 props
        const isEnglishPage = window.location.pathname.includes('index_en.html') || 
                              window.location.href.includes('index_en.html');
        
        console.log('当前页面:', window.location.href);
        console.log('isEnglishPage:', isEnglishPage);
        console.log('props.lang:', props.lang);
        
        // 使用 URL 判断，不依赖 props
        const isEnglish = isEnglishPage;

        // 统一使用 AMapLoader 加载 2.0 版本
        if (window.AMapLoader) {
          const AMapInstance = await window.AMapLoader.load({
            key: '5cb36dd9372284a13a125603a0a2efa4',
            version: '2.0',
            plugins: ['AMap.Scale', 'AMap.ToolBar', 'AMap.Geocoder', 'AMap.Driving', 'AMap.AutoComplete']
          });
          AMap = AMapInstance;
          console.log(isEnglish ? '英文版' : '中文版', 'AMap 2.0 加载成功');
        } else {
          console.error('AMapLoader 未加载');
          showToast('地图 SDK 加载失败', 'error');
          return;
        }
        
        // 隐私合规
        if (AMap.updatePrivacyShow && AMap.updatePrivacyAgree) {
          AMap.updatePrivacyShow(true, true);
          AMap.updatePrivacyAgree(true, true);
        }
        
        // 使用统一的地图配置，全部使用中文底图
        const mapOptions = {
          center: [104.0668, 30.5728],
          zoom: 13,
          resizeEnable: true
          // 移除语言设置，全部使用中文底图避免权限错误
        };

        // 初始化地图
        const initSuccess = init(mapOptions);
        if (!initSuccess) {
          console.error('地图初始化失败');
          showToast('地图初始化失败', 'error');
          return;
        }

        mapLoaded.value = true;
        
        // 初始化输入提示服务
        initAutoComplete();
      };
      
      checkSize();
    } catch (err) {
      console.error('地图初始化失败', err);
      showToast('地图加载失败：' + err.message, 'error');
    }
  };

// 初始化输入提示服务
const initAutoComplete = () => {
  if (!AMap || !startInput.value || !destInput.value) {
    console.log('等待输入框或AMap加载');
    setTimeout(initAutoComplete, 100);
    return;
  }

  try {
    // 检查 AMap.AutoComplete 是否可用
    if (!AMap.AutoComplete) {
      console.error('AMap.AutoComplete 插件未加载，尝试动态加载');
      
      // 尝试动态加载 AutoComplete 插件
      AMap.plugin(['AMap.AutoComplete'], () => {
        console.log('AMap.AutoComplete 插件动态加载成功');
        initAutoComplete(); // 重新初始化
      });
      return;
    }

    // 初始化起点输入提示
    startAutoComplete = new AMap.AutoComplete({
      input: startInput.value,
      city: '成都',
      citylimit: true
    });

    // 起点输入提示选择事件
    if (AMap.event && AMap.event.addListener) {
      AMap.event.addListener(startAutoComplete, 'select', (e) => {
        if (e.poi && e.poi.name) {
          start.value = e.poi.name; // 填充完整地址到输入框
        }
      });
    } else {
      // 高德 2.0 版本的事件监听方式
      startAutoComplete.on('select', (e) => {
        if (e.poi && e.poi.name) {
          start.value = e.poi.name; // 填充完整地址到输入框
        }
      });
    }

    // 初始化目的地输入提示
    destAutoComplete = new AMap.AutoComplete({
      input: destInput.value,
      city: '成都',
      citylimit: true
    });

    // 目的地输入提示选择事件
    if (AMap.event && AMap.event.addListener) {
      AMap.event.addListener(destAutoComplete, 'select', (e) => {
        if (e.poi && e.poi.name) {
          newDest.value = e.poi.name; // 填充完整地址到输入框
        }
      });
    } else {
      // 高德 2.0 版本的事件监听方式
      destAutoComplete.on('select', (e) => {
        if (e.poi && e.poi.name) {
          newDest.value = e.poi.name; // 填充完整地址到输入框
        }
      });
    }

    console.log('输入提示服务初始化成功');
  } catch (error) {
    console.error('输入提示服务初始化失败:', error);
  }
};

// 获取当前位置
const getLocation = () => {
  if (!navigator.geolocation) {
    showToast('浏览器不支持地理定位', 'error');
    return;
  }
  
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords;
      currentPosition = [longitude, latitude];
      
      // 移动地图到当前位置
      setCenter([longitude, latitude], 15);
      
      const geocoder = new AMap.Geocoder({ radius: 1000, extensions: "all" });
      geocoder.getAddress([longitude, latitude], (status, result) => {
        if (status === 'complete' && result.regeocode) {
          start.value = result.regeocode.formattedAddress;
          showToast(t('toast_locSuccess'), 'success');
        }
      });
    },
    () => showToast(t('toast_locFail'), 'error')
  );
};

// 地理编码
const geocodeAddress = (address) => {
  return new Promise((resolve, reject) => {
    if (!AMap) {
      reject(new Error('地图未初始化'));
      return;
    }

    // 特殊处理：成都东站 -> 成都东客站
    let finalAddress = address;
    if (address.includes('成都东站')) {
      finalAddress = '成都东客站';
      console.log('地址转换:', address, '->', finalAddress);
    }

    const geocoder = new AMap.Geocoder({ city: '成都市' });
    let settled = false;

    // 超时保护：8秒后自动 reject，防止回调不触发导致卡死
    const timer = setTimeout(() => {
      if (!settled) {
        settled = true;
        reject(new Error('地理编码超时'));
      }
    }, 8000);

    geocoder.getLocation(finalAddress, (status, result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (status === 'complete' && result.info === 'OK') {
        // 高德 1.4.15 和 2.0 返回格式不同
        let location;
        if (result.geocodes && result.geocodes.length > 0) {
          // 2.0 版本
          location = result.geocodes[0].location;
        } else if (result.location) {
          // 1.4.15 版本
          location = result.location;
        }

        if (location) {
          // 兼容 LngLat 对象和普通数组
          const lng = location.getLng ? location.getLng() : location.lng;
          const lat = location.getLat ? location.getLat() : location.lat;
          resolve([lng, lat]);
        } else {
          reject(new Error('地理编码失败：无法获取位置'));
        }
      } else {
        reject(new Error('地理编码失败'));
      }
    });
  });
};

// 添加目的地
const addDest = () => {
  const val = newDest.value.trim();
  if (!val) return showToast(t('toast_emptyInput'), 'warning');
  if (destinations.value.length >= 7) return showToast(t('toast_maxDest'), 'warning');
  destinations.value.push(val);
  newDest.value = "";
  showToast(t('toast_addDest'), 'success');
};

// 删除目的地
const removeDest = (index) => {
  destinations.value.splice(index, 1);
  routeResult.value = null;
  showToast(t('toast_delDest'), 'info');
};

// 选择模式
const setMode = (m) => {
  // 清理旧模式的缓存
  if (mode.value && mode.value !== m) {
    clearRouteCache(mode.value);
  }
  
  mode.value = m;
  routeResult.value = null;
  
  // 如果正在导航，停止导航
  if (isNavigating.value) {
    stopNavigation();
  }
  
  console.log('切换到模式:', m, '已清理旧模式缓存');
};

// 规划路线
const planRoute = async () => {
  // 1. 节流：每秒最多一次
  const now = Date.now();
  if (now - lastPlanTime < 1000) {
    showToast('操作过于频繁，请稍后再试', 'warning');
    return;
  }
  lastPlanTime = now;

  // 清除旧路线
  clearRoute();

  // 2. 缓存检查
  const cacheKey = JSON.stringify({
    start: start.value,
    destinations: destinations.value,
    fixedEnd: fixedEnd.value,
    mode: mode.value,
    hasFixedEnd: !!fixedEnd.value,  // 使用 !! 转换为布尔值
    preference: mode.value === 'short' ? 'shortest' : mode.value === 'green' ? 'green' : 'balanced'
  });
  
  console.log('缓存键:', cacheKey, '缓存内容:', Object.keys(routeCache));
  
  if (routeCache[cacheKey]) {
    console.log('使用缓存路线，模式:', mode.value);
    routeResult.value = routeCache[cacheKey];
    if (routeResult.value.coordinates) {
      showRouteOnMap(routeResult.value.coordinates);
    }
    showToast(t('toast_planSuccess'), 'success');
    return;
  }

  if (!canPlan.value) return;
  isPlanning.value = true;
  
  try {
    let coordinates = [];
    let allDestinations = [];
    let hasFixedEnd = !!fixedEnd.value;
    let fixedEndCoord = null;
    let useBackendGeocode = false;

    // 处理起点
    if (currentPosition && start.value) {
      // 如果既有当前位置又有起点地址，优先使用当前位置
      coordinates.push(currentPosition);
      allDestinations.push(start.value || '当前位置');
    } else if (start.value) {
      // 只有起点地址，进行地理编码
      try {
        const startCoord = await geocodeAddress(start.value);
        coordinates.push(startCoord);
        allDestinations.push(start.value);
      } catch (error) {
        console.warn('前端起点地理编码失败，回退到后端:', error.message);
        useBackendGeocode = true;
        allDestinations.push(start.value);
      }
    } else {
      showToast('请输入起点', 'error');
      isPlanning.value = false;
      return;
    }

    // 添加其他目的地
    allDestinations.push(...destinations.value);

    if (!useBackendGeocode) {
      for (let i = 0; i < destinations.value.length; i++) {
        try {
          const destCoord = await geocodeAddress(destinations.value[i]);
          coordinates.push(destCoord);
        } catch (error) {
          console.warn(`前端目的地地理编码失败，回退到后端: ${destinations.value[i]}`);
          useBackendGeocode = true;
          break;
        }
      }
    }
    
    const requestBody = {
      destinations: allDestinations,
      preference: mode.value === 'short' ? 'shortest' : mode.value === 'green' ? 'green' : 'balanced'
    };
    // 仅当前端地理编码全部成功时才发送坐标，否则让后端做地理编码
    if (!useBackendGeocode && coordinates.length === allDestinations.length) {
      requestBody.coordinates = coordinates;
    }

    const response = await fetch('/api/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) throw new Error('API调用失败');
    
    // 更健壮的JSON解析，处理可能的NaN/inf值
    const responseText = await response.text();
    let data;
    try {
      data = JSON.parse(responseText, (key, value) => {
        // 处理NaN和Infinity值
        if (typeof value === 'number' && (isNaN(value) || !isFinite(value))) {
          console.warn(`检测到非法数值: ${key} = ${value}, 替换为0`);
          return 0;
        }
        return value;
      });
    } catch (jsonError) {
      console.error('JSON解析失败:', jsonError, '响应文本:', responseText);
      throw new Error(`数据解析失败: ${jsonError.message}`);
    }

    const modeNames = { short: t('short'), green: t('green'), balance: t('balance') };
    const avgAqi = data.aqi ? Math.round(data.aqi.reduce((a, b) => a + b, 0) / data.aqi.length) : 50;
    const distance = data.distance || (2 + Math.random() * 8).toFixed(1) + " km";

    let tip = "";
    if (data.aqi && data.aqi.length > 0) {
      const avgAqiValue = data.aqi.reduce((sum, aqi) => sum + aqi, 0) / data.aqi.length;
      if (avgAqiValue <= 50) tip = "🌿 " + t('tip_good');
      else if (avgAqiValue <= 100) tip = "🌤️ " + t('tip_moderate');
      else if (avgAqiValue <= 150) tip = "😷 " + t('tip_poor');
      else tip = "⚠️ " + t('tip_bad');
    }

    // 处理固定终点 - 路线规划完成后，再追加固定终点
    let finalCoordinates = data.coordinates || coordinates;
    let finalDestinations = [...allDestinations];
    let finalRouteStops = data.route_stops || [];
    
    // 如果有固定终点，在规划完成后追加到路线末尾
    if (hasFixedEnd && fixedEnd.value) {
      try {
        // 对固定终点进行地理编码
        fixedEndCoord = await geocodeAddress(fixedEnd.value);
        
        // 追加固定终点到路线
        finalCoordinates = [...finalCoordinates, fixedEndCoord];
        finalDestinations = [...finalDestinations, fixedEnd.value];
        
        // 更新路线站点 - 添加固定终点作为最后一站
        finalRouteStops.push({
          name: fixedEnd.value,
          aqi: 50, // 默认AQI值
          isStart: false
        });
        
        showToast(`已添加固定终点: ${fixedEnd.value}`, 'success');
      } catch (error) {
        console.error('固定终点地理编码失败:', error);
        showToast(`固定终点 "${fixedEnd.value}" 地址解析失败，将跳过`, 'warning');
      }
    }
    
    routeResult.value = {
      modeName: modeNames[mode.value],
      distance: data.distance || distance,
      aqi: Math.round(data.avg_aqi) || avgAqi,
      healthScore: Math.round(data.health_score) || 80,
      estimatedTime: Math.floor((data.distance_km || parseFloat(distance.replace(/[^0-9.]/g, ''))) * 3 + 15),
      tip: tip,
      coordinates: finalCoordinates,
      routeStops: finalRouteStops,
      preference: data.preference
    };

    // 3. 存入缓存
    routeCache[cacheKey] = routeResult.value;

    if (finalCoordinates.length) currentPosition = finalCoordinates[0];
    showRouteOnMap(finalCoordinates);
    showToast(t('toast_planSuccess'), 'success');
  } catch (error) {
    console.error('规划失败:', error);
    showToast('规划失败: ' + error.message, 'error');
  } finally {
    isPlanning.value = false;
  }
};

// 在地图上显示路线
const showRouteOnMap = (coordinates) => {
  if (!coordinates || coordinates.length < 2) return;

  // 使用第一个坐标作为起点，最后一个作为终点
  const start = coordinates[0];
  const end = coordinates[coordinates.length - 1];
  const waypoints = coordinates.slice(1, -1);

  // 调用 searchRoute 规划路线
  searchRoute(start, end, waypoints).then(() => {
    // 调整地图视野以显示完整路线
    fitBounds(coordinates);
  }).catch(err => {
    console.error('路线显示失败:', err);
  });
};

// 开始导航
const startRealNavigation = async () => {
  if (!routeResult.value) return;
  isNavigating.value = true;
  emit('update:navigating', true);
  showToast(t('toast_navStart'), 'success');

  try {
    // 检查是否支持地理位置
    if (!navigator.geolocation) {
      showToast('浏览器不支持地理位置', 'error');
      isNavigating.value = false;
      return;
    }

    // 获取路线坐标
    const coordinates = routeResult.value.coordinates;
    if (!coordinates || coordinates.length < 2) {
      showToast('路线数据不完整', 'error');
      isNavigating.value = false;
      return;
    }

    // 提取起点、终点和途经点
    const startPoint = coordinates[0];
    const endPoint = coordinates[coordinates.length - 1];
    const waypoints = coordinates.slice(1, -1);

    // 启动导航
    try {
      navigationInfo.value = await startNavigation(startPoint, endPoint, waypoints);
      if (navigationInfo.value) {
        // 更新初始导航信息
        remainingDistance.value = (navigationInfo.value.distance / 1000).toFixed(1);
        remainingTime.value = Math.round(navigationInfo.value.time / 60);
        totalSteps.value = navigationInfo.value.steps?.length || 0;
      }
    } catch (navError) {
      console.error('导航初始化失败:', navError);
      showToast('导航初始化失败: ' + navError.message, 'error');
      isNavigating.value = false;
      return;
    }

    // 获取初始位置并移动地图
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        currentPosition = [longitude, latitude];
        // 移动地图到当前位置
        setCenter([longitude, latitude], 16);
      },
      (error) => {
        console.warn('获取位置失败:', error);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );

    // 持续监听位置变化
    watchId = navigator.geolocation.watchPosition(
      (position) => {
        const { latitude, longitude, speed } = position.coords;
        currentPosition = [longitude, latitude];
        currentSpeed.value = Math.round((speed || 0) * 3.6); // 转换为 km/h

        // 移动地图跟随当前位置
        setCenter([longitude, latitude]);

        // 更新导航信息
        if (navigationInfo.value) {
          const navUpdate = updateNavigation([longitude, latitude]);
          if (navUpdate) {
            nextTurnDirection.value = navUpdate.nextTurnDirection;
            nextTurnDistance.value = navUpdate.distanceToNext;
            nextTurnType.value = navUpdate.nextTurnType;
            remainingDistance.value = (navUpdate.remainingDistance / 1000).toFixed(1);
            remainingTime.value = navUpdate.remainingTime;
            
            // 更新导航状态
            isOffRoute.value = navUpdate.isOffRoute;
            isNearDestination.value = navUpdate.isNearDestination;
            isArrived.value = navUpdate.isArrived;
            offRouteDistance.value = navUpdate.offRouteDistance;
            currentStep.value = navUpdate.currentStep;
            
            // 偏离路线警告
            if (navUpdate.isOffRoute && navUpdate.offRouteDistance > 100) {
              showToast(`已偏离路线 ${navUpdate.offRouteDistance} 米，正在重新规划...`, 'warning');
              // 可以在这里触发重新规划
            }
            
            // 接近目的地提示
            if (navUpdate.isNearDestination && !navUpdate.isArrived) {
              showToast('即将到达目的地', 'info');
            }
            
            // 到达目的地
            if (navUpdate.isArrived) {
              showToast('已到达目的地！', 'success');
              stopNavigation();
            }
          }
        }
      },
      (error) => {
        console.warn('位置监听失败:', error);
      },
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
    );
    
    // 启动指南针
    initCompass();

  } catch (error) {
    console.error('导航启动失败:', error);
    showToast('导航启动失败: ' + error.message, 'error');
    isNavigating.value = false;
  }
};

// 停止导航
const stopNavigation = () => {
  isNavigating.value = false;
  emit('update:navigating', false);

  // 停止地图导航
  stopMapNavigation();
  navigationInfo.value = null;

  // 停止定位
  if (watchId) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }

  // 重置导航状态
  isOffRoute.value = false;
  isNearDestination.value = false;
  isArrived.value = false;
  offRouteDistance.value = 0;
  currentStep.value = 0;
  totalSteps.value = 0;
  currentSpeed.value = 0;
  
  // 停止指南针
  stopCompass();

  showToast(t('toast_navStop'), 'info');
};

// 重置地图视图
const resetMapView = () => {
  setCenter([104.0668, 30.5728], 13);
  showToast('地图已重置', 'info');
};

// 指南针功能
const initCompass = () => {
  if (window.DeviceOrientationEvent) {
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
      DeviceOrientationEvent.requestPermission()
        .then(permissionState => {
          if (permissionState === 'granted') {
            startCompassListener();
          } else {
            console.warn('指南针权限被拒绝');
            isCompassAvailable.value = false;
          }
        })
        .catch(console.error);
    } else {
      startCompassListener();
    }
  } else {
    console.warn('设备不支持指南针功能');
    isCompassAvailable.value = false;
  }
};

const startCompassListener = () => {
  isCompassAvailable.value = true;
  compassListener = (event) => {
    let heading = 0;
    if (event.webkitCompassHeading) {
      heading = event.webkitCompassHeading;
    } else if (event.alpha !== null) {
      heading = 360 - event.alpha;
    }
    deviceOrientation.value = heading;
    compassHeading.value = Math.round(heading);
  };
  window.addEventListener('deviceorientation', compassListener);
};

const stopCompass = () => {
  if (compassListener) {
    window.removeEventListener('deviceorientation', compassListener);
    compassListener = null;
  }
  isCompassAvailable.value = false;
};

const getDirectionText = (heading) => {
  const directions = ['北', '东北', '东', '东南', '南', '西南', '西', '西北'];
  const index = Math.round(heading / 45) % 8;
  return directions[index];
};

// 颜色工具
const getAqiColor = (aqi) => {
  if (aqi <= 50) return "#10B981";
  if (aqi <= 100) return "#F59E0B";
  return "#EF4444";
};

const getAqiGradient = (aqi) => {
  if (aqi <= 50) return "linear-gradient(135deg, #10B981 0%, #34D399 100%)";
  if (aqi <= 100) return "linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)";
  return "linear-gradient(135deg, #EF4444 0%, #F87171 100%)";
};

const getHealthScoreColor = (score) => {
  if (score >= 90) return "#10B981";
  if (score >= 70) return "#3B82F6";
  if (score >= 50) return "#F59E0B";
  return "#EF4444";
};

// 计算两点之间的距离（米）
const getDistance = (point1, point2) => {
  const [lng1, lat1] = point1;
  const [lng2, lat2] = point2;
  
  const rad1 = lat1 * Math.PI / 180;
  const rad2 = lat2 * Math.PI / 180;
  const a = rad1 - rad2;
  const b = lng1 * Math.PI / 180 - lng2 * Math.PI / 180;
  const s = 2 * Math.asin(Math.sqrt(Math.pow(Math.sin(a/2), 2) + 
    Math.cos(rad1) * Math.cos(rad2) * Math.pow(Math.sin(b/2), 2)));
  return s * 6378137;
};

let initMapTimer = null;
onMounted(() => {
  initMapTimer = setTimeout(initMapWrapper, 100);
});
onUnmounted(() => {
  if (initMapTimer) {
    clearTimeout(initMapTimer);
    initMapTimer = null;
  }
  if (watchId) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }
  // 清理地图实例
  destroy();
});

// 移除自动语言监听，改为手动调用
// 当需要切换语言时，通过调用 updateMapLanguage 方法手动更新



</script>

<style>
/* ==================== 全局重置与基础优化 ==================== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%);
  overflow-x: hidden;
  /* 全局美化滚动条 */
  scrollbar-width: thin;
  scrollbar-color: rgba(0,0,0,0.1) transparent;
}

/* 全局滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.1);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0,0,0,0.2);
}

/* 动态背景 */
.ambient-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
  animation: float 20s infinite ease-in-out;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.4) 0%, transparent 60%);
  top: -200px;
  right: -100px;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 60%);
  bottom: 10%;
  left: -100px;
  animation-delay: -7s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 60%);
  top: 40%;
  right: 20%;
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}

/* 玻璃拟态统一规范 */
.glass-card {
  background: rgba(248, 250, 252, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.06);
  border-radius: 24px;
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 容器布局修复 */
.container {
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  width: 100%;
}

/* 头部样式优化 */
.glass-header {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  border-radius: 20px;
  padding: 20px 30px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  position: relative;
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #10B981, #059669);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.pulse-ring {
  position: absolute;
  inset: 0;
  border-radius: 16px;
  background: rgba(16, 185, 129, 0.4);
  animation: pulse 2s infinite;
  z-index: -1;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1.4); opacity: 0; }
}

.title-text h1 {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}

.subtitle {
  font-size: 13px;
  color: #4b5563;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.aqi-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
  border-radius: 16px;
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  min-width: 70px;
}

.aqi-value {
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
}

.aqi-label {
  font-size: 10px;
  opacity: 0.9;
}

/* 双栏布局修复 */
.content-layout {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 24px;
  align-items: start;
  width: 100%;
}

/* 左侧面板修复：粘性定位+滚动优化 */
.left-panel {
  position: sticky;
  top: 24px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(0,0,0,0.2) transparent;
}

/* 滚动条美化 */
.left-panel::-webkit-scrollbar {
  width: 6px;
}

.left-panel::-webkit-scrollbar-track {
  background: transparent;
}

.left-panel::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 3px;
}

.left-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25);
}

.panel-content {
  padding: 28px 28px 40px 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 表单样式统一 */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.section-title small {
  color: #9ca3af;
  font-weight: 400;
  font-size: 13px;
}

.section-title .icon {
  font-size: 18px;
}

.input-group {
  display: flex;
  gap: 10px;
  width: 100%;
}

.input-group input {
  flex: 1;
  padding: 16px 20px;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  font-size: 15px;
  outline: none;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
  color: #1f2937;
  min-width: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.input-group input::placeholder {
  color: #d1d5db;
}

.input-group input:focus {
  border-color: #10B981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
  transform: translateY(-1px);
}

/* 按钮样式修复：禁用状态+交互 */
.icon-btn {
  width: 50px;
  height: 50px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  transition: all 0.3s ease;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.locate-btn {
  background: rgba(139, 92, 246, 0.1);
  color: #8B5CF6;
}

.locate-btn:hover {
  background: #8B5CF6;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.add-btn {
  background: rgba(16, 185, 129, 0.1);
  color: #10B981;
  font-size: 20px;
}

.add-btn:disabled {
  background: rgba(255, 255, 255, 0.5);
  color: #9ca3af;
  cursor: not-allowed;
  opacity: 0.7;
  transform: none;
  box-shadow: none;
}

.add-btn:not(:disabled):hover {
  background: #10B981;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

/* 目的地标签优化：换行+间距 */
.dest-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 100%;
}

.dest-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 20px;
  font-size: 14px;
  animation: tagIn 0.3s ease;
  transition: all 0.2s;
  max-width: 100%;
}

.dest-tag:hover {
  border-color: #10B981;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

@keyframes tagIn {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

.tag-number {
  width: 20px;
  height: 20px;
  background: #10B981;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.tag-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tag-remove {
  width: 18px;
  height: 18px;
  border: none;
  background: #fee2e2;
  color: #ef4444;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  transition: all 0.2s;
  flex-shrink: 0;
}

.tag-remove:hover {
  background: #ef4444;
  color: white;
  transform: rotate(90deg);
}

.fixed-end-tag {
  background: linear-gradient(135deg, #EF4444, #DC2626);
  color: white;
  border-color: #EF4444;
}

.fixed-end-tag .tag-number {
  background: rgba(255, 255, 255, 0.2);
}

.empty-tip {
  color: #6b7280;
  font-size: 13px;
  font-weight: 500;
  padding: 8px 0;
}

/* 模式选择器优化 */
.mode-selector {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
  width: 100%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.mode-btn:hover {
  border-color: #10B981;
  transform: translateX(4px) translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.mode-btn.active {
  background: linear-gradient(135deg, #10B981, #059669);
  color: white;
  border-color: transparent;
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.3);
  transform: translateY(-2px);
}

.mode-icon {
  font-size: 24px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.05);
  border-radius: 12px;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.mode-btn.active .mode-icon {
  background: rgba(255,255,255,0.2);
  transform: scale(1.05);
}

.mode-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.mode-name {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
  line-height: 1.4;
}

.mode-desc {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.3;
}

.mode-btn.active .mode-name,
.mode-btn.active .mode-desc {
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* 规划按钮优化 */
.plan-btn {
  width: 100%;
  padding: 20px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(135deg, #10B981, #059669);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
  margin-top: auto;
  height: 60px;
  font-family: inherit;
}

.plan-btn:disabled {
  background: rgba(209, 213, 219, 0.7);
  color: #6b7280;
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.7;
  transform: none;
}

.plan-btn:not(:disabled):hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
  background: linear-gradient(135deg, #059669, #047857);
}

.plan-btn:not(:disabled):active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-pulse:not(:disabled) {
  animation: btnPulse 2s infinite;
}

@keyframes btnPulse {
  0%, 100% { box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3); }
  50% { box-shadow: 0 4px 24px rgba(16, 185, 129, 0.5); }
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 右侧面板优化 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

/* 地图容器修复：高度+层级 */
.map-wrapper {
  position: relative;
  height: calc(100vh - 200px);
  min-height: 300px;
  max-height: 600px;
  overflow: hidden;
  width: 100%;
  border-radius: 24px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.map-wrapper:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.map-container {
  width: 100%;
  height: 100%;
  z-index: 1;
}

.map-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.9);
  gap: 12px;
  color: #6b7280;
  z-index: 10;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #10B981;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.map-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 5;
}

.map-control-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: none;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4b5563;
  transition: all 0.2s;
}

.map-control-btn:hover {
  background: #10B981;
  color: white;
  transform: scale(1.1);
}

/* 高德地图自定义标记修复：优先级 */
.custom-marker {
  width: 32px !important;
  height: 32px !important;
  border-radius: 50% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  color: white !important;
  font-weight: 700 !important;
  font-size: 14px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
  border: 3px solid white !important;
}
.custom-marker.start { background: #10B981 !important; }
.custom-marker.end { background: #EF4444 !important; }
.custom-marker.waypoint { background: #3B82F6 !important; }

/* 导航提示卡片优化 */
.navigation-hint-card {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: nowrap;
}

.hint-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 200px;
}

.hint-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.hint-text {
  display: flex;
  flex-direction: column;
}

.hint-title {
  font-weight: 600;
  color: #1f2937;
}

.hint-subtitle {
  font-size: 13px;
  color: #6b7280;
}

.navigate-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #1f2937, #111827);
  color: white;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
  white-space: nowrap;
}

.navigate-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(31, 41, 55, 0.3);
}

/* 路线结果卡片优化 */
.route-result {
  padding: 24px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.route-badge {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.route-badge.short { background: linear-gradient(135deg, #3B82F6, #2563EB); }
.route-badge.green { background: linear-gradient(135deg, #10B981, #059669); }
.route-badge.balance { background: linear-gradient(135deg, #8B5CF6, #7C3AED); }

.health-score {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.circular-chart {
  width: 50px;
  height: 50px;
}

.circle-bg {
  fill: none;
  stroke: #e5e7eb;
  stroke-width: 3;
}

.circle {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 1s ease;
}

.percentage {
  fill: #1f2937;
  font-size: 14px;
  font-weight: 800;
  text-anchor: middle;
  dominant-baseline: middle;
}

.score-label {
  font-size: 11px;
  color: #4b5563;
  margin-top: 4px;
  font-weight: 600;
}

/* 统计网格响应式优化：平板2列，手机1列 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-box {
  background: white;
  padding: 16px;
  border-radius: 12px;
  text-align: center;
  border: 2px solid #f3f4f6;
  transition: all 0.2s;
}

.stat-box:hover {
  border-color: #e5e7eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}



.stat-icon {
  font-size: 20px;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.stat-value small {
  font-size: 11px;
  color: #6b7280;
  margin-left: 2px;
}

.stat-label {
  font-size: 12px;
  color: #4b5563;
  margin-top: 4px;
  font-weight: 500;
}

/* 健康建议优化 */
.health-tip {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: white;
  border-left: 4px solid;
}

.health-tip.good { border-left-color: #10B981; background: #f0fdf4; }
.health-tip.moderate { border-left-color: #F59E0B; background: #fffbeb; }
.health-tip.poor { border-left-color: #EF4444; background: #fef2f2; }

.tip-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.tip-text {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  font-weight: 500;
}

/* 最优路线方案 */
.route-stops {
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
}

.stops-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stop-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: white;
  border-radius: 10px;
  border: 2px solid #e5e7eb;
  transition: all 0.2s;
  position: relative;
  margin-bottom: 8px;
}

.stop-item:hover {
  border-color: #10B981;
  transform: translateX(4px);
}

.stop-item.start-point {
  border-color: #10B981;
  background: #f0fdf4;
}

.stop-marker {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #3B82F6, #2563EB);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.stop-item.start-point .stop-marker {
  background: linear-gradient(135deg, #10B981, #059669);
}

.stop-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.stop-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stop-aqi {
  font-size: 12px;
  font-weight: 500;
}

.stop-item:last-child {
  margin-bottom: 0;
}

.stop-arrow {
  position: absolute;
  left: 26px;
  bottom: -12px;
  font-size: 14px;
  color: #9ca3af;
  font-weight: 700;
  z-index: 1;
}

/* 全屏导航界面修复 */
.navigation-overlay {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  color: white;
}

.glass-effect {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-header {
  padding: 20px 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.close-nav-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-nav-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: rotate(90deg);
}

.nav-title {
  font-size: 18px;
  font-weight: 600;
}

.nav-aqi {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.nav-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px;
  text-align: center;
}

.turn-indicator {
  margin-bottom: 60px;
}

.turn-icon-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  border: 4px solid;
  animation: breathe 2s infinite;
}

.turn-icon-large.right { border-color: #3B82F6; color: #3B82F6; }
.turn-icon-large.left { border-color: #F59E0B; color: #F59E0B; }
.turn-icon-large.straight { border-color: #10B981; color: #10B981; }

@keyframes breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.turn-distance {
  font-size: clamp(36px, 10vw, 72px);
  font-weight: 700;
  line-height: 1;
  margin-bottom: 8px;
  color: #ffffff;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.turn-distance small {
  font-size: clamp(18px, 3vw, 24px);
  opacity: 0.9;
  font-weight: 500;
}

.turn-direction {
  font-size: clamp(18px, 5vw, 24px);
  color: #ffffff;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.nav-footer {
  padding: 24px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.nav-stat {
  text-align: center;
  min-width: 80px;
}

.nav-stat-label {
  display: block;
  font-size: 12px;
  color: rgba(255,255,255,0.85);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 500;
}

.nav-stat-value {
  font-size: clamp(20px, 4vw, 28px);
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.nav-stat-value small {
  font-size: 14px;
  color: rgba(255,255,255,0.8);
  margin-left: 4px;
  font-weight: 500;
}

.nav-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
}

/* Toast 修复：位置+响应式 */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
  max-width: calc(100% - 40px);
}

.toast {
  pointer-events: auto;
  padding: 16px 24px;
  border-radius: 12px;
  color: white;
  font-size: 14px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease;
  min-width: 280px;
  width: fit-content;
  word-break: break-word;
}

.toast.success { background: linear-gradient(135deg, #10B981, #059669); }
.toast.error { background: linear-gradient(135deg, #EF4444, #DC2626); }
.toast.warning { background: linear-gradient(135deg, #F59E0B, #D97706); }

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* 过渡动画优化 */
.tag-list-enter-active, .tag-list-leave-active {
  transition: all 0.3s ease;
}
.tag-list-enter-from, .tag-list-leave-to {
  opacity: 0; transform: scale(0.8);
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.4s ease;
}
.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0; transform: translateY(20px);
}

.fade-scale-enter-active, .fade-scale-leave-active {
  transition: all 0.3s ease;
}
.fade-scale-enter-from, .fade-scale-leave-to {
  opacity: 0; transform: scale(0.95);
}

/* ==================== 响应式终极修复 ==================== */
/* 平板端 (768px - 1024px) */
@media (max-width: 1024px) {
  .content-layout {
    grid-template-columns: 1fr;
  }
  .left-panel {
    position: relative;
    height: auto;
    top: 0;
    order: 2;
  }
  .right-panel {
    order: 1;
  }
  .map-wrapper {
    height: 400px;
  }
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 手机端 (<768px) */
@media (max-width: 768px) {
  .container {
    padding: 12px;
  }
  .glass-header {
    padding: 16px 20px;
    margin-bottom: 16px;
  }
  .title-text h1 {
    font-size: 20px;
  }
  .panel-content {
    padding: 20px;
  }
  .map-wrapper {
    height: 300px;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .navigation-hint-card {
    flex-direction: column;
    text-align: center;
  }
  .nav-footer {
    flex-direction: column;
  }
  .nav-divider {
    width: 40px;
    height: 1px;
  }
  /* 手机端Toast居中 */
  .toast-container {
    left: 50%;
    transform: translateX(-50%);
    right: auto;
    top: 12px;
  }
  .toast {
    min-width: auto;
    width: 90vw;
  }
  /* 手机端文字可读性优化 */
  .mode-name {
    font-size: 16px;
    color: #111827;
  }
  .mode-desc {
    font-size: 13px;
    color: #374151;
  }
  .stat-value {
    font-size: 20px;
  }
  .stat-label {
    font-size: 13px;
    color: #374151;
  }
  .section-title {
    color: #1f2937;
  }
  .hint-title {
    font-size: 16px;
    color: #111827;
  }
  .hint-subtitle {
    font-size: 14px;
    color: #4b5563;
  }
  
  /* 手机端导航界面优化 - 使用clamp实现自适应 */
  .simple-navigation-overlay {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  }
  
  .simple-nav-header {
    padding: 10px 14px;
    padding-top: max(10px, env(safe-area-inset-top));
  }
  
  .simple-close-btn {
    padding: 6px 12px;
    font-size: 12px;
  }
  
  .simple-close-btn svg {
    width: 14px;
    height: 14px;
  }
  
  .simple-aqi {
    padding: 5px 10px;
    font-size: 11px;
  }
  
  .simple-turn-hint {
    gap: clamp(6px, 1.5vh, 12px);
    padding: 12px 14px;
  }
  
  .big-arrow-container {
    width: clamp(90px, 25vw, 130px);
    height: clamp(90px, 25vw, 130px);
  }
  
  .big-turn-arrow {
    width: 55%;
    height: 55%;
  }
  
  .big-turn-arrow svg {
    width: 100%;
    height: 100%;
  }
  
  .big-distance {
    gap: 6px;
  }
  
  .distance-number {
    font-size: clamp(40px, 10vw, 64px);
  }
  
  .distance-unit {
    font-size: clamp(16px, 3.5vw, 22px);
  }
  
  .direction-status {
    padding: 6px 12px;
    gap: 6px;
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
  }
  
  .status-text {
    font-size: 12px;
  }
  
  .navigation-hint {
    font-size: clamp(12px, 3vw, 15px);
    padding: 8px 14px;
    max-width: 92%;
  }
  
  .simple-turn-text {
    font-size: clamp(18px, 4.5vw, 24px);
  }
  
  .simple-nav-footer {
    padding: 12px 14px;
    padding-bottom: max(12px, env(safe-area-inset-bottom) + 4px);
  }
  
  .simple-info-bar {
    padding: 12px 14px;
    border-radius: 14px;
  }
  
  .simple-info-item {
    gap: 2px;
  }
  
  .simple-label {
    font-size: 10px;
  }
  
  .simple-value {
    font-size: 16px;
  }
  
  .simple-divider {
    height: 32px;
  }
  
  /* 手机端提前提示 */
  .advance-notice {
    top: 70px;
    padding: 10px 16px;
    font-size: 14px;
  }
  
  .notice-icon {
    font-size: 16px;
  }
  
  /* 手机端警告和到达提示 */
  .simple-warning {
    top: 60px;
    padding: 10px 16px;
    font-size: 13px;
  }
  
  .simple-arrived {
    padding: 20px 32px;
    font-size: 20px;
  }
  
  /* 手机端备案号 */
  .icp-footer {
    padding: 10px;
  }
  
  .icp-footer a {
    font-size: 11px;
  }
}

/* 小屏幕手机端 (< 375px) */
@media (max-width: 375px) {
  .simple-turn-hint {
    gap: 5px;
    padding: 8px 10px;
  }
  
  .big-arrow-container {
    width: clamp(75px, 22vw, 100px);
    height: clamp(75px, 22vw, 100px);
  }
  
  .big-turn-arrow {
    width: 55%;
    height: 55%;
  }
  
  .big-distance {
    gap: 4px;
  }
  
  .distance-number {
    font-size: clamp(32px, 9vw, 48px);
  }
  
  .distance-unit {
    font-size: clamp(14px, 3vw, 18px);
  }
  
  .simple-turn-text {
    font-size: clamp(16px, 4vw, 20px);
  }
  
  .navigation-hint {
    font-size: 11px;
    padding: 6px 10px;
  }
  
  .simple-info-bar {
    padding: 10px 12px;
  }
  
  .simple-value {
    font-size: 13px;
  }
  
  .simple-nav-header {
    padding: 8px 10px;
  }
  
  .simple-close-btn {
    padding: 5px 10px;
    font-size: 11px;
  }
  
  .simple-aqi {
    padding: 4px 8px;
    font-size: 10px;
  }
  
  .direction-status {
    padding: 5px 10px;
  }
  
  .status-text {
    font-size: 11px;
  }
  
  .simple-nav-footer {
    padding: 10px;
  }
  
  .simple-label {
    font-size: 9px;
  }
  
  .advance-notice {
    top: 55px;
    padding: 6px 10px;
    font-size: 11px;
  }
  
  .simple-warning {
    top: 50px;
    padding: 6px 10px;
    font-size: 11px;
  }
  
  .simple-arrived {
    padding: 14px 20px;
    font-size: 16px;
  }
}

/* 横屏手机端适配 */
@media (max-width: 768px) and (orientation: landscape) {
  .simple-nav-header {
    padding: 6px 12px;
    padding-top: max(6px, env(safe-area-inset-top));
  }
  
  .simple-turn-hint {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 12px;
    padding: 6px 16px;
  }
  
  .big-arrow-container {
    width: clamp(60px, 15vh, 90px);
    height: clamp(60px, 15vh, 90px);
    order: 1;
  }
  
  .big-turn-arrow {
    width: 55%;
    height: 55%;
  }
  
  .big-distance {
    order: 2;
  }
  
  .distance-number {
    font-size: clamp(28px, 8vh, 48px);
  }
  
  .distance-unit {
    font-size: clamp(12px, 3vh, 18px);
  }
  
  .simple-turn-text {
    font-size: clamp(14px, 4vh, 18px);
    order: 3;
    width: auto;
  }
  
  .navigation-hint {
    font-size: clamp(11px, 3vh, 14px);
    padding: 5px 10px;
    order: 4;
    width: 100%;
    max-width: 350px;
  }
  
  .direction-status {
    order: 5;
    padding: 5px 12px;
  }
  
  .simple-nav-footer {
    padding: 8px 16px;
    padding-bottom: max(40px, env(safe-area-inset-bottom) + 24px);
    flex-shrink: 0;
  }
  
  .simple-info-bar {
    flex-direction: row;
    padding: 8px 12px;
  }
  
  .simple-nav-footer {
    padding: 8px 12px;
  }
  
  .advance-notice {
    top: 45px;
  }
  
  .simple-warning {
    top: 40px;
  }
}

/* 高德地图输入提示样式优化 */
.amap-sug-result {
  border: none !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
  border-radius: 12px !important;
  background: white !important;
  overflow: hidden;
}

.amap-sug-result .auto-item {
  padding: 12px 16px !important;
  border-bottom: 1px solid #f3f4f6 !important;
  cursor: pointer;
  transition: background-color 0.2s ease;
  font-size: 14px;
  color: #374151;
}

.amap-sug-result .auto-item:hover {
  background-color: #f9fafb !important;
}

.amap-sug-result .auto-item:last-child {
  border-bottom: none !important;
}

.amap-sug-result .auto-item span {
  color: #6b7280 !important;
}

.amap-sug-result .auto-item .place {
  font-weight: 600;
  color: #111827 !important;
}

.amap-sug-result .auto-item .district {
  color: #9ca3af !important;
}

/* 偏离路线警告 */
.off-route-warning {
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  animation: slideDown 0.3s ease;
}

.warning-content {
  background: linear-gradient(135deg, #EF4444, #DC2626);
  color: white;
  padding: 12px 24px;
  border-radius: 50px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
  font-weight: 600;
  font-size: 14px;
}

.warning-icon {
  font-size: 18px;
}

/* 接近目的地提示 */
.near-destination-notice {
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  animation: slideDown 0.3s ease;
}

.notice-content {
  background: linear-gradient(135deg, #10B981, #059669);
  color: white;
  padding: 12px 24px;
  border-radius: 50px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
  font-weight: 600;
  font-size: 14px;
}

.notice-icon {
  font-size: 18px;
}

/* 到达提示 */
.arrived-notice {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 100;
  animation: scaleIn 0.5s ease;
}

.arrived-notice .notice-content {
  background: linear-gradient(135deg, #8B5CF6, #7C3AED);
  padding: 24px 48px;
  font-size: 24px;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4);
}

/* 导航进度条 */
.nav-progress {
  position: absolute;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  max-width: 400px;
  z-index: 10;
}

.progress-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10B981, #34D399);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-text {
  text-align: center;
  color: white;
  font-size: 12px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

/* 全屏导航界面优化 */
.navigation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.nav-map-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  opacity: 0.3;
}

/* 顶部信息栏 */
.nav-top-bar {
  position: relative;
  z-index: 10;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.close-nav-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.2);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.close-nav-btn:hover {
  background: rgba(239, 68, 68, 0.4);
  transform: scale(1.05);
}

.nav-title-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.nav-title {
  font-size: 18px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.nav-subtitle {
  font-size: 12px;
  color: rgba(255,255,255,0.7);
  font-weight: 500;
}

.nav-aqi-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  border-radius: 12px;
  color: white;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.aqi-label {
  font-size: 10px;
  opacity: 0.9;
}

.aqi-value {
  font-size: 16px;
}

/* 状态提示区域 */
.nav-status-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 50px;
  font-weight: 600;
  font-size: 14px;
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  animation: slideDown 0.3s ease;
}

.status-badge.warning {
  background: linear-gradient(135deg, #EF4444, #DC2626);
}

.status-badge.success {
  background: linear-gradient(135deg, #10B981, #059669);
}

.status-badge.arrived {
  background: linear-gradient(135deg, #8B5CF6, #7C3AED);
  padding: 16px 32px;
  font-size: 18px;
  animation: scaleIn 0.5s ease;
}

.status-icon {
  font-size: 16px;
}

/* 指南针包装器 */
.compass-wrapper {
  position: absolute;
  top: 100px;
  right: 20px;
  z-index: 10;
}

/* 指南针样式 */
.compass-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.compass {
  position: relative;
  width: 70px;
  height: 70px;
  transition: transform 0.3s ease;
}

.compass-outer {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(255,255,255,0.8));
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255,255,255,0.9);
  box-shadow: 0 4px 20px rgba(0,0,0,0.3), inset 0 2px 4px rgba(255,255,255,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.compass-inner {
  position: relative;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  border: 1px solid #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.compass-needle {
  position: absolute;
  width: 3px;
  height: 32px;
  background: linear-gradient(to bottom, #EF4444 50%, #3B82F6 50%);
  border-radius: 2px;
  transform-origin: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.compass-needle::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-bottom: 8px solid #EF4444;
}

.compass-center {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #1f2937;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.compass-directions {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.compass-directions span {
  position: absolute;
  font-size: 10px;
  font-weight: 700;
  color: #1f2937;
}

.direction-n { top: 3px; left: 50%; transform: translateX(-50%); color: #EF4444; }
.direction-e { right: 3px; top: 50%; transform: translateY(-50%); }
.direction-s { bottom: 3px; left: 50%; transform: translateX(-50%); }
.direction-w { left: 3px; top: 50%; transform: translateY(-50%); }

/* 中央内容区 */
.nav-center-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 20px;
  position: relative;
  z-index: 5;
}

/* 转向卡片 */
.turn-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px 48px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.turn-icon-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3B82F6, #2563EB);
  color: white;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
}

.turn-icon-wrapper.right {
  background: linear-gradient(135deg, #10B981, #059669);
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
}

.turn-icon-wrapper.left {
  background: linear-gradient(135deg, #F59E0B, #D97706);
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.4);
}

.turn-icon-wrapper.u-turn {
  background: linear-gradient(135deg, #EF4444, #DC2626);
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
}

.turn-details {
  text-align: center;
}

/* 方向指示器容器 */
.direction-indicator-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  animation: fadeIn 0.5s ease;
}

/* 完整方向罗盘 */
.full-direction-compass {
  position: relative;
  width: 150px;
  height: 150px;
}

.compass-face {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(255,255,255,0.8));
  backdrop-filter: blur(10px);
  border: 3px solid rgba(255,255,255,0.9);
  box-shadow: 0 4px 20px rgba(0,0,0,0.3), inset 0 2px 4px rgba(255,255,255,0.5);
  position: relative;
  transition: transform 0.3s ease;
}

.direction-mark {
  position: absolute;
  font-size: 16px;
  font-weight: 700;
}

.mark-label {
  color: #374151;
  text-shadow: 0 1px 2px rgba(255,255,255,0.8);
}

.mark-label.north {
  color: #DC2626;
  font-size: 20px;
}

.compass-center-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  background: #1f2937;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* 固定指针（指向前方/当前朝向） */
.fixed-pointer {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 10;
}

.pointer-triangle {
  width: 0;
  height: 0;
  border-left: 12px solid transparent;
  border-right: 12px solid transparent;
  border-top: 20px solid #3B82F6;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

.pointer-label {
  font-size: 14px;
  font-weight: 700;
  color: #3B82F6;
  margin-top: 4px;
  text-shadow: 0 1px 2px rgba(255,255,255,0.8);
}

/* 目标方向指针 */
.target-pointer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  transition: transform 0.5s ease;
}

.target-triangle {
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-top: 18px solid #EF4444;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

/* 方向信息面板 */
.direction-info-panel {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(10px);
  padding: 16px 24px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.1);
}

.current-direction-info,
.target-direction-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.info-label {
  font-size: 11px;
  color: rgba(255,255,255,0.6);
  font-weight: 500;
}

.info-value {
  font-size: 20px;
  font-weight: 700;
  color: white;
}

.info-value.highlight {
  color: #10B981;
  font-size: 24px;
}

.direction-arrow {
  font-size: 24px;
  color: rgba(255,255,255,0.8);
}

/* 转向指令 */
.turn-command {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.8), rgba(37, 99, 235, 0.8));
  backdrop-filter: blur(10px);
  padding: 16px 32px;
  border-radius: 50px;
  border: 2px solid rgba(255,255,255,0.2);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
}

.command-text {
  font-size: 20px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
  text-align: center;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.turn-distance-large {
  font-size: 56px;
  font-weight: 800;
  color: white;
  line-height: 1;
  text-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.turn-distance-large .unit {
  font-size: 24px;
  font-weight: 600;
  margin-left: 4px;
  opacity: 0.8;
}

.turn-direction-text {
  font-size: 20px;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  margin-top: 8px;
  text-shadow: 0 1px 4px rgba(0,0,0,0.2);
}

/* 进度环形指示器 */
.progress-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
}

.progress-ring {
  position: relative;
  width: 60px;
  height: 60px;
}

.progress-ring svg {
  transform: rotate(-90deg);
  width: 100%;
  height: 100%;
}

.progress-ring-bg {
  fill: none;
  stroke: rgba(255,255,255,0.2);
  stroke-width: 3;
}

.progress-ring-fill {
  fill: none;
  stroke: #10B981;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.5s ease;
}

.progress-ring .progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  font-weight: 700;
  color: white;
}

/* 底部信息栏 */
.nav-bottom-bar {
  position: relative;
  z-index: 10;
  padding: 16px;
  padding-bottom: 32px;
}

.nav-stats {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 16px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  font-size: 24px;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-stats .stat-label {
  font-size: 11px;
  color: rgba(255,255,255,0.6);
  font-weight: 500;
}

.nav-stats .stat-value {
  font-size: 20px;
  font-weight: 700;
  color: white;
}

.nav-stats .stat-value small {
  font-size: 12px;
  font-weight: 500;
  opacity: 0.7;
  margin-left: 2px;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255,255,255,0.2);
}

/* 动画 */
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.scale-in-enter-active, .scale-in-leave-active {
  transition: all 0.5s ease;
}

.scale-in-enter-from, .scale-in-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* 指南针动画 */
@keyframes compassPulse {
  0%, 100% {
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  }
  50% {
    box-shadow: 0 4px 30px rgba(59, 130, 246, 0.4);
  }
}

.compass-outer {
  animation: compassPulse 2s infinite;
}

/* 简化版导航界面 */
.simple-navigation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f0f23 100%);
  display: grid;
  grid-template-rows: auto 1fr auto;
  grid-template-areas: 
    "header"
    "content"
    "footer";
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

/* 顶部栏 */
.simple-nav-header {
  grid-area: header;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  padding-top: max(12px, env(safe-area-inset-top));
}

.simple-close-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.simple-close-btn:hover {
  background: rgba(255,255,255,0.2);
}

.simple-aqi {
  padding: 6px 12px;
  border-radius: 10px;
  color: white;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

/* 中央转向提示 */
.simple-turn-hint {
  grid-area: content;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: clamp(8px, 2vh, 20px);
  padding: 10px 16px;
  overflow-y: auto;
}

.big-arrow-container {
  width: clamp(100px, 28vw, 160px);
  height: clamp(100px, 28vw, 160px);
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05));
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  flex-shrink: 0;
}

.big-turn-arrow {
  width: 55%;
  height: 55%;
  color: white;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.big-turn-arrow svg {
  width: 100%;
  height: 100%;
}

/* 方向正确时的颜色 - 绿色/蓝色 */
.big-turn-arrow.correct {
  color: #10B981;
  filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.6));
}

/* 方向错误时的颜色 - 红色 */
.big-turn-arrow.wrong {
  color: #EF4444;
  filter: drop-shadow(0 0 20px rgba(239, 68, 68, 0.6));
  animation: pulse-red 1s infinite;
}

/* 中性颜色 */
.big-turn-arrow.neutral {
  color: #3B82F6;
}

@keyframes pulse-red {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

/* 方向状态提示 */
.direction-status {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(10px);
  padding: 8px 16px;
  border-radius: 50px;
  border: 1px solid rgba(255,255,255,0.1);
  flex-shrink: 0;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.status-dot.correct {
  background: #10B981;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.8);
}

.status-dot.wrong {
  background: #EF4444;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.8);
  animation: blink 1s infinite;
}

.status-dot.neutral {
  background: #3B82F6;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 13px;
  font-weight: 600;
  color: white;
}

/* 距离数字 */
.big-distance {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-shrink: 0;
}

.distance-number {
  font-size: clamp(48px, 12vw, 96px);
  font-weight: 800;
  color: white;
  line-height: 1;
  text-shadow: 0 4px 12px rgba(0,0,0,0.5);
  transition: all 0.3s ease;
}

.distance-unit {
  font-size: clamp(18px, 4vw, 32px);
  font-weight: 600;
  color: rgba(255,255,255,0.8);
}

/* 距离警告级别颜色 */
.big-distance.warning .distance-number {
  color: #F59E0B;
  text-shadow: 0 4px 12px rgba(245, 158, 11, 0.5);
}

.big-distance.urgent .distance-number {
  color: #EF4444;
  text-shadow: 0 4px 12px rgba(239, 68, 68, 0.5);
  animation: pulse-distance 1s infinite;
}

@keyframes pulse-distance {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 导航提示文字 */
.navigation-hint {
  font-size: clamp(14px, 3.5vw, 18px);
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  text-align: center;
  padding: 10px 20px;
  background: rgba(0,0,0,0.3);
  backdrop-filter: blur(10px);
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.1);
  max-width: 90%;
  line-height: 1.4;
  flex-shrink: 0;
}

.navigation-hint.warning {
  color: #F59E0B;
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.3);
}

.navigation-hint.urgent {
  color: #EF4444;
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  font-weight: 700;
  animation: pulse-hint 1.5s infinite;
}

@keyframes pulse-hint {
  0%, 100% { 
    opacity: 1;
    transform: scale(1);
  }
  50% { 
    opacity: 0.9;
    transform: scale(1.02);
  }
}

/* 提前提示（400米和100米） */
.advance-notice {
  position: absolute;
  top: 100px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 50px;
  font-weight: 600;
  font-size: 16px;
  animation: slideDown 0.3s ease;
  backdrop-filter: blur(10px);
  border: 2px solid;
}

.advance-notice.warning {
  background: rgba(245, 158, 11, 0.9);
  color: white;
  border-color: #F59E0B;
  box-shadow: 0 4px 20px rgba(245, 158, 11, 0.4);
}

.advance-notice.urgent {
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border-color: #EF4444;
  box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4);
  animation: slideDown 0.3s ease, pulse-notice 1s infinite;
}

@keyframes pulse-notice {
  0%, 100% { 
    box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4);
  }
  50% { 
    box-shadow: 0 4px 30px rgba(239, 68, 68, 0.6);
  }
}

.notice-icon {
  font-size: 20px;
}

.notice-text {
  white-space: nowrap;
}

/* 转向文字 */
.simple-turn-text {
  font-size: clamp(20px, 5vw, 32px);
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 8px rgba(0,0,0,0.3);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  flex-shrink: 0;
}

/* 底部信息栏 */
.simple-nav-footer {
  grid-area: footer;
  padding: 12px 16px;
  padding-bottom: max(16px, env(safe-area-inset-bottom) + 8px);
}

.simple-info-bar {
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 16px;
  padding: 14px 16px;
}

.simple-info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}

.simple-label {
  font-size: 11px;
  color: rgba(255,255,255,0.6);
  font-weight: 500;
}

.simple-value {
  font-size: 16px;
  font-weight: 700;
  color: white;
}

.simple-divider {
  width: 1px;
  height: 32px;
  background: rgba(255,255,255,0.2);
}

/* 警告和到达提示 */
.simple-warning {
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #EF4444, #DC2626);
  color: white;
  padding: 12px 24px;
  border-radius: 50px;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
  animation: slideDown 0.3s ease;
}

.simple-arrived {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: linear-gradient(135deg, #8B5CF6, #7C3AED);
  color: white;
  padding: 24px 48px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 24px;
  box-shadow: 0 8px 32px rgba(139, 92, 246, 0.4);
  animation: scaleIn 0.5s ease;
}

/* 备案号样式 */
.icp-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  text-align: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  z-index: 100;
}

.icp-footer a {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  text-decoration: none;
  transition: color 0.3s ease;
}

.icp-footer a:hover {
  color: rgba(255, 255, 255, 0.9);
}
</style>
