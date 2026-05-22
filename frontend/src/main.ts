import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/user'
import { useThemeStore } from './stores/theme'
import i18n from './locales'
import './styles/main.scss'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// Element Plus locale mapping
const epLocales: Record<string, any> = {
  'zh-CN': zhCn,
  'en-US': en,
}
const savedLang = localStorage.getItem('language') || 'zh-CN'

app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(ElementPlus, { locale: epLocales[savedLang] || zhCn })

app.mount('#app')

// 初始化主题
const themeStore = useThemeStore()
themeStore.init()

// 尝试恢复登录会话（通过 HttpOnly cookie 中的 refresh_token）
const userStore = useUserStore()
userStore.restoreSession()
