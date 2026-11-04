import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../components/HomeView.vue'

const routes = [
  { path: '/', redirect: '/zh' },
  { path: '/zh', name: 'home-zh', component: HomeView, props: { lang: 'zh' } },
  { path: '/en', name: 'home-en', component: HomeView, props: { lang: 'en' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
