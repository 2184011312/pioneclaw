import { config } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { vi } from 'vitest'
import ElementPlus from 'element-plus'
import zhCN from '../src/locales/zh-CN'

// Create i18n instance for tests
const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
  },
})

// Global plugins
config.global.plugins = [i18n, ElementPlus]

// Mock IntersectionObserver with proper constructor
class MockIntersectionObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
global.IntersectionObserver = MockIntersectionObserver as any

// Mock ResizeObserver with proper constructor
class MockResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
global.ResizeObserver = MockResizeObserver as any

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
