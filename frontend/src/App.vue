<template>
  <div class="app-container">
    <header class="glass-header" v-if="!isNavigating">
      <div class="logo-section">
        <div class="logo-icon">
          <span class="leaf-icon">🌿</span>
          <div class="pulse-ring"></div>
        </div>
        <div class="title-text">
          <h1>{{ $t('title') }}</h1>
          <span class="subtitle">{{ $t('subtitle') }}</span>
        </div>
      </div>
      <div class="header-right">
        <!-- 语言切换链接 -->
        <div class="lang-switch">
          <a href="/index.html" class="lang-link">中文</a>
          <span class="lang-separator">|</span>
          <a href="/index_en.html" class="lang-link">English</a>
        </div>
        <!-- AQI 指示器 -->
        <div class="weather-badge" v-if="currentAqi">
          <div class="aqi-indicator" :style="{ background: getAqiGradient(currentAqi) }">
            <span class="aqi-value">{{ currentAqi }}</span>
          </div>
        </div>
      </div>
    </header>
    <HomeView 
      :currentAqi="currentAqi" 
      :lang="locale.value"
      @update:aqi="updateAqi"
      @update:navigating="updateNavigating"
      ref="homeViewRef"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import HomeView from './components/HomeView.vue'

const { locale, t } = useI18n()
const currentAqi = ref(null)
const isNavigating = ref(false)
const homeViewRef = ref(null)

// 语言切换通过页面跳转实现，移除动态切换功能

// 更新 AQI
const updateAqi = (aqi) => {
  currentAqi.value = aqi
}

// 更新导航状态
const updateNavigating = (navigating) => {
  isNavigating.value = navigating
}



// 获取 AQI 渐变颜色
const getAqiGradient = (aqi) => {
  if (aqi <= 50) return "linear-gradient(135deg, #10B981 0%, #059669 100%)"
  if (aqi <= 100) return "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)"
  if (aqi <= 150) return "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)"
  return "linear-gradient(135deg, #991B1B 0%, #7F1D1D 100%)"
}
</script>

<style>
body { margin: 0; padding: 0; font-family: 'PingFang SC', 'Helvetica Neue', Arial, sans-serif; }
#app { width: 100%; height: 100%; }

.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.glass-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-bottom: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  position: relative;
  z-index: 1000;
  transition: all 0.3s ease;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  position: relative;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #10B981, #059669);
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.leaf-icon {
  font-size: 24px;
  z-index: 2;
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid #10B981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.2);
    opacity: 0;
  }
}

.title-text {
  display: flex;
  flex-direction: column;
}

.glass-header h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.subtitle {
  font-size: 0.875rem;
  color: #4b5563;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 语言切换链接 */
.lang-switch {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lang-link {
  padding: 10px 18px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.5);
  background: rgba(255,255,255,0.7);
  backdrop-filter: blur(15px);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  text-decoration: none;
  color: #333;
}

.lang-link:hover {
  background: #10B981;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.lang-separator {
  color: #999;
  font-weight: 400;
}

/* AQI 指示器 */
.weather-badge {
  display: flex;
  align-items: center;
}

.aqi-indicator {
  padding: 6px 12px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.aqi-value {
  color: white;
  font-size: 14px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .glass-header {
    padding: 0.75rem 1rem;
  }
  
  .logo-icon {
    width: 40px;
    height: 40px;
  }
  
  .leaf-icon {
    font-size: 20px;
  }
  
  .glass-header h1 {
    font-size: 1.25rem;
  }
  
  .subtitle {
    font-size: 0.75rem;
  }
  
  .lang-btn {
    padding: 6px 12px;
    font-size: 12px;
  }
  
  .aqi-indicator {
    padding: 4px 8px;
  }
  
  .aqi-value {
    font-size: 12px;
  }
}
</style>