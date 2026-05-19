import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type ThemeMode = 'auto' | 'dark' | 'light'

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>('auto')
  const isDark = ref(true)

  let timerHandle: ReturnType<typeof setInterval> | null = null

  function isNightTime(): boolean {
    const hour = new Date().getHours()
    // Dark mode from 6pm (18:00) to 6am (06:00)
    return hour >= 18 || hour < 6
  }

  function syncIsDarkFromMode() {
    if (mode.value === 'auto') {
      isDark.value = isNightTime()
    } else {
      isDark.value = mode.value === 'dark'
    }
  }

  function applyTheme() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  function persistMode() {
    localStorage.setItem('pioneclaw_theme_mode', mode.value)
  }

  function startAutoCheck() {
    stopAutoCheck()
    timerHandle = setInterval(() => {
      if (mode.value === 'auto') {
        const wasDark = isDark.value
        syncIsDarkFromMode()
        if (isDark.value !== wasDark) {
          applyTheme()
        }
      }
    }, 60_000) // check every minute
  }

  function stopAutoCheck() {
    if (timerHandle !== null) {
      clearInterval(timerHandle)
      timerHandle = null
    }
  }

  function init() {
    const saved = localStorage.getItem('pioneclaw_theme_mode')
    if (saved === 'auto' || saved === 'dark' || saved === 'light') {
      mode.value = saved
    } else {
      // Legacy: migrate old 'pioneclaw_theme' key
      const legacy = localStorage.getItem('pioneclaw_theme')
      if (legacy === 'dark') {
        mode.value = 'dark'
      } else if (legacy === 'light') {
        mode.value = 'light'
      } else {
        mode.value = 'auto'
      }
    }
    syncIsDarkFromMode()
    applyTheme()
    startAutoCheck()
  }

  function toggle() {
    // Cycle: auto → dark → light → auto
    const order: ThemeMode[] = ['auto', 'dark', 'light']
    const idx = order.indexOf(mode.value)
    mode.value = order[(idx + 1) % order.length]
    syncIsDarkFromMode()
    persistMode()
    applyTheme()
  }

  const getThemeIcon = computed(() => {
    if (mode.value === 'auto') {
      return isDark.value ? 'moon-stars' : 'sun'
    }
    return mode.value === 'dark' ? 'moon' : 'sun'
  })

  return { mode, isDark, getThemeIcon, init, toggle, stopAutoCheck }
})
