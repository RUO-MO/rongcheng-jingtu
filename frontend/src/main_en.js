// 清理可能残留的地图实例，但保留 AMap 对象
if (window.AMap && window.AMap.Map) {
  // 清理所有可能的实例
  document.querySelectorAll('.amap-container').forEach(el => {
    try {
      const map = el._map || el.__vue__?.$amap
      if (map && map.destroy) map.destroy()
    } catch(e) {}
  })
}

// 清理可能残留的全局回调
Object.keys(window).forEach(key => {
  if (key.startsWith('____on') && key.includes('AMap')) {
    delete window[key]
  }
})

import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { createI18n } from 'vue-i18n'
import zh from './locales/zh'
import en from './locales/en'

// 配置i18n - 默认英文
const i18n = createI18n({
  legacy: false,
  locale: 'en', // 默认英文
  messages: {
    zh,
    en
  }
})

const app = createApp(App)
app.use(router)
app.use(i18n)
app.mount('#app')
