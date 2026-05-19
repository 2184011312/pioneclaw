<template>
  <div class="management-page">
    <div class="management-container">
      <div class="management-sidebar">
        <div class="sidebar-header">
          <el-icon><component :is="icon" /></el-icon>
          <span class="sidebar-title">{{ $t(titleKey) }}</span>
        </div>
        <el-menu :default-active="activeMenu" @select="handleMenuSelect">
          <el-menu-item v-for="item in menuItems" :key="item.key" :index="item.key">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ $t(item.labelKey) }}</span>
          </el-menu-item>
        </el-menu>
      </div>
      <div class="management-content">
        <slot :activeMenu="activeMenu" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps<{
  titleKey: string
  icon: Component
  menuItems: { key: string; icon: Component; labelKey: string }[]
  defaultTab: string
  tabSlugs: string[]
}>()

const activeMenu = defineModel<string>({ default: '' })

const route = useRoute()
const router = useRouter()

if (!activeMenu.value) {
  activeMenu.value = props.defaultTab
}

function handleMenuSelect(key: string) {
  activeMenu.value = key
  router.replace({ query: { tab: key } })
}

onMounted(() => {
  const tab = route.query.tab as string
  if (tab && props.tabSlugs.includes(tab)) {
    activeMenu.value = tab
  }
})
</script>

<style scoped lang="scss">
.management-page {
  padding: 0;
  height: 100%;
}

.management-container {
  display: flex;
  gap: 20px;
  height: calc(100vh - 140px);
}

.management-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--pc-bg-elevated);
  border-radius: var(--pc-radius-lg);
  border: 1px solid var(--pc-border);
  overflow: hidden;
  display: flex;
  flex-direction: column;

  .sidebar-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 16px 20px;
    border-bottom: 1px solid var(--pc-border);
    font-size: 15px;
    font-weight: 600;

    .el-icon {
      font-size: 18px;
      color: var(--pc-primary);
    }

    .sidebar-title {
      background: var(--pc-gradient-primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }

  .el-menu {
    border-right: none;
    background: transparent;
    flex: 1;
    padding: 8px;
  }
}

.management-content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 24px;
  background: var(--pc-bg-elevated);
  border-radius: var(--pc-radius-lg);
  border: 1px solid var(--pc-border);
}
</style>
