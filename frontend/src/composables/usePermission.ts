import { computed } from 'vue'
import { useUserStore } from '../stores/user'

/**
 * 权限组合式函数
 *
 * 用法:
 * const { hasPermission, hasAnyPermission } = usePermission()
 * if (hasPermission('task:create')) { ... }
 */
export function usePermission() {
  const userStore = useUserStore()

  const permissions = computed<string[]>(() => {
    return userStore.permissions || []
  })

  const isSuperAdmin = computed(() => userStore.isSuperAdmin)

  /**
   * 检查是否拥有指定权限
   * 支持通配符: task:* 匹配 task:create
   */
  function hasPermission(code: string): boolean {
    if (isSuperAdmin.value) return true
    if (permissions.value.includes('*')) return true
    if (permissions.value.includes(code)) return true

    // 通配符匹配
    const parts = code.split(':')
    if (parts.length >= 2) {
      const wildcard = `${parts[0]}:*`
      if (permissions.value.includes(wildcard)) return true
    }

    return false
  }

  /**
   * 检查是否拥有任一权限
   */
  function hasAnyPermission(codes: string[]): boolean {
    return codes.some(code => hasPermission(code))
  }

  /**
   * 检查是否拥有全部权限
   */
  function hasAllPermissions(codes: string[]): boolean {
    return codes.every(code => hasPermission(code))
  }

  return {
    permissions,
    isSuperAdmin,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
  }
}
