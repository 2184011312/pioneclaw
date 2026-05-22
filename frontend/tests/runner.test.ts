import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import zhCN from '@/locales/zh-CN'

// ── Hoisted mocks — use plain objects since imports aren't available yet ──
const { mockApi, mockUserStore } = vi.hoisted(() => {
  return {
    mockApi: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
    mockUserStore: {
      isSuperAdmin: false,
      isOrgAdmin: false,
      user: { id: 1, username: 'testuser', display_name: 'Test User', role: 'user' },
    },
  }
})

// ── Mock element-plus service functions ──
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...(actual as Record<string, unknown>),
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
    },
    ElMessageBox: {
      confirm: vi.fn().mockResolvedValue('confirm'),
      alert: vi.fn().mockResolvedValue('confirm'),
    },
  }
})

// ── Mock api module ──
vi.mock('@/api', () => ({
  api: mockApi,
}))

// ── Mock user store ──
vi.mock('@/stores/user', () => ({
  useUserStore: () => mockUserStore,
  getAccessToken: () => '',
}))

// ── Import component after mocks ──
import Runners from '@/views/Runners.vue'

// ── Create i18n ──
const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: { 'zh-CN': zhCN },
})

// ── Default runner data ──
const defaultRunners = [
  {
    id: 1,
    name: 'runner-1',
    display_name: 'Runner 1',
    status: 'online',
    platform: 'linux',
    host: '192.168.1.1',
    port: 20006,
    total_tasks: 10,
    success_tasks: 9,
    failed_tasks: 1,
    applied_at: '2025-01-01T00:00:00Z',
    last_heartbeat: new Date().toISOString(),
  },
  {
    id: 2,
    name: 'runner-2',
    display_name: 'Runner 2',
    status: 'offline',
    platform: 'windows',
    host: '192.168.1.2',
    port: 20006,
    total_tasks: 5,
    success_tasks: 5,
    failed_tasks: 0,
    applied_at: '2025-01-02T00:00:00Z',
  },
]

const defaultBindings = [
  {
    id: 3,
    name: 'my-runner-1',
    display_name: 'My Runner 1',
    status: 'online',
    platform: 'linux',
    host: '10.0.0.1',
    port: 20006,
    total_tasks: 20,
    success_tasks: 18,
    failed_tasks: 2,
    applied_at: '2025-01-03T00:00:00Z',
    last_heartbeat: new Date().toISOString(),
  },
]

const defaultReleases = [
  {
    id: 1,
    version: '1.0.0',
    filename: 'pioneclaw-runner-linux-1.0.0.zip',
    file_size: 1024000,
    checksum: 'abc123',
    platform: 'linux',
    is_latest: true,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    version: '1.1.0',
    filename: 'pioneclaw-runner-windows-1.1.0.exe',
    file_size: 2048000,
    checksum: 'def456',
    platform: 'windows',
    is_latest: false,
    created_at: '2025-02-01T00:00:00Z',
  },
]

function setupApiMocks() {
  mockApi.get.mockImplementation((url: string) => {
    if (url.includes('/runners/stats')) {
      return Promise.resolve({
        data: {
          total_runners: 5,
          online_count: 3,
          pending_count: 1,
          total_tasks: 100,
          success_rate: 95,
        },
      })
    }
    if (url.includes('/runners/center-info')) {
      return Promise.resolve({
        data: {
          http_address: 'http://localhost:20005',
          apply_endpoint: 'http://localhost:20005/api/runners/apply',
        },
      })
    }
    if (url.startsWith('/runners?') || url === '/runners') {
      return Promise.resolve({ data: defaultRunners })
    }
    if (url.includes('/runners/my-bindings')) {
      return Promise.resolve({ data: defaultBindings })
    }
    if (url.includes('/runner-releases/versions')) {
      return Promise.resolve({ data: defaultReleases })
    }
    if (url.includes('/runners/1/diagnostics')) {
      return Promise.resolve({
        data: {
          cpu_percent: 45,
          memory_percent: 60,
          disk_percent: 30,
          processes: [{ pid: 1234, name: 'agent', cpu_percent: 12, memory_percent: 5 }],
          updated_at: new Date().toISOString(),
        },
      })
    }
    if (url.includes('/connection-events')) {
      return Promise.resolve({
        data: [
          { event_type: 'connected', detail: 'Agent started', timestamp: new Date().toISOString() },
          { event_type: 'heartbeat', timestamp: new Date().toISOString() },
        ],
      })
    }
    return Promise.resolve({ data: [] })
  })

  mockApi.post.mockResolvedValue({ data: {} })
  mockApi.put.mockResolvedValue({ data: {} })
  mockApi.delete.mockResolvedValue({ data: {} })
}

// ── Mount helper ──
function mountRunners() {
  return mount(Runners, {
    global: {
      plugins: [i18n],
    },
  })
}

describe('Runners.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setupApiMocks()
    // Reset user store to non-admin default
    mockUserStore.isSuperAdmin = false
    mockUserStore.isOrgAdmin = false
    mockUserStore.user = { id: 1, username: 'testuser', display_name: 'Test User', role: 'user' }
  })

  // ── Test 1: Renders 4 tabs for super admin ──
  it('renders 4 tabs for super admin', async () => {
    mockUserStore.isSuperAdmin = true
    mockUserStore.isOrgAdmin = true

    const wrapper = mountRunners()
    await flushPromises()

    const tabItems = wrapper.findAll('.el-tabs__item')
    // 4 tabs: Runner 列表, 诊断面板, 版本管理, 我的 Runner
    expect(tabItems.length).toBe(4)
  })

  // ── Test 2: Non-admin sees only "我的 Runner" ──
  it('shows only my runner tab for regular users', async () => {
    mockUserStore.isSuperAdmin = false
    mockUserStore.isOrgAdmin = false

    const wrapper = mountRunners()
    await flushPromises()

    const tabItems = wrapper.findAll('.el-tabs__item')
    // 1 tab: 我的 Runner
    expect(tabItems.length).toBe(1)
    expect(tabItems[0].text()).toBe('我的 Runner')
  })

  // ── Test 3: Org admin sees 列表 + 诊断 + 我的 Runner, no 版本管理 ──
  it('shows 3 tabs for org admin', async () => {
    mockUserStore.isSuperAdmin = false
    mockUserStore.isOrgAdmin = true

    const wrapper = mountRunners()
    await flushPromises()

    const tabItems = wrapper.findAll('.el-tabs__item')
    // 3 tabs: Runner 列表, 诊断面板, 我的 Runner
    expect(tabItems.length).toBe(3)

    const tabTexts = tabItems.map(el => el.text())
    expect(tabTexts).toContain('诊断面板')
    expect(tabTexts).toContain('我的 Runner')
    expect(tabTexts).not.toContain('版本管理')
  })

  // ── Test 4: My bindings list renders ──
  it('renders my bindings list on tab switch', async () => {
    const wrapper = mountRunners()
    await flushPromises()

    // Switch to "我的 Runner" tab
    const myTab = wrapper.findAll('.el-tabs__item').find(el => el.text() === '我的 Runner')
    expect(myTab).toBeTruthy()
    await myTab!.trigger('click')
    await flushPromises()

    // Verify API was called
    expect(mockApi.get).toHaveBeenCalledWith('/runners/my-bindings')

    // Check that binding data is rendered
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('My Runner 1')
  })

  // ── Test 5: Set default button triggers API call ──
  it('triggers set default API when button clicked', async () => {
    const wrapper = mountRunners()
    await flushPromises()

    // Switch to my runners tab
    const myTab = wrapper.findAll('.el-tabs__item').find(el => el.text() === '我的 Runner')
    await myTab!.trigger('click')
    await flushPromises()

    // Find "设为默认" button
    const defaultBtn = wrapper.find('.my-runners-panel .card-actions .el-button')
    expect(defaultBtn.exists()).toBe(true)
    await defaultBtn.trigger('click')
    await flushPromises()

    expect(mockApi.put).toHaveBeenCalledWith('/runners/my-default', { runner_id: 3 })
  })

  // ── Test 6: Token rotation confirm dialog ──
  it('shows confirm dialog on token rotation', async () => {
    const { ElMessageBox } = await import('element-plus')
    mockUserStore.isSuperAdmin = true

    mockApi.post.mockResolvedValue({ data: { new_token: 'new-secret-token-abc123' } })

    const wrapper = mountRunners()
    await flushPromises()

    // Find the dropdown trigger on first runner card and click it
    const dropdownTrigger = wrapper.find('.runner-card .btn-menu')
    expect(dropdownTrigger.exists()).toBe(true)
    await dropdownTrigger.trigger('click')
    await flushPromises()

    // Find the "轮换 Token" dropdown item
    const dropdownItems = document.querySelectorAll('.el-dropdown-menu__item')
    const rotateItem = Array.from(dropdownItems).find(
      el => el.textContent?.includes('轮换 Token')
    )
    expect(rotateItem).toBeTruthy()

    await (rotateItem as HTMLElement).click()
    await flushPromises()

    // Confirm dialog should have been shown
    expect(ElMessageBox.confirm).toHaveBeenCalled()
  })

  // ── Test 7: Empty state for my bindings ──
  it('shows empty state when no bindings', async () => {
    mockApi.get.mockImplementation((url: string) => {
      if (url.includes('/runners/my-bindings')) {
        return Promise.resolve({ data: [] })
      }
      if (url.includes('/runners/stats')) {
        return Promise.resolve({
          data: { total_runners: 0, online_count: 0, pending_count: 0, total_tasks: 0, success_rate: 0 },
        })
      }
      if (url.includes('/runners/center-info')) {
        return Promise.resolve({
          data: { http_address: 'http://localhost:20005', apply_endpoint: 'http://localhost:20005/api/runners/apply' },
        })
      }
      return Promise.resolve({ data: [] })
    })

    const wrapper = mountRunners()
    await flushPromises()

    // Switch to my runners tab
    const myTab = wrapper.findAll('.el-tabs__item').find(el => el.text() === '我的 Runner')
    await myTab!.trigger('click')
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('你还没有绑定的 Runner')
  })

  // ── Test 8: Version list renders for super admin ──
  it('renders version list for super admin', async () => {
    mockUserStore.isSuperAdmin = true

    const wrapper = mountRunners()
    await flushPromises()

    // Switch to version management tab
    const versionTab = wrapper.findAll('.el-tabs__item').find(el => el.text() === '版本管理')
    expect(versionTab).toBeTruthy()
    await versionTab!.trigger('click')
    await flushPromises()

    // Verify releases API was called
    expect(mockApi.get).toHaveBeenCalledWith('/runner-releases/versions?')

    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('1.0.0')
    expect(text).toContain('1.1.0')
  })
})
