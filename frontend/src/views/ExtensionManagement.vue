<template>
  <ManagementHub
    v-model="activeMenu"
    title-key="nav.extensionManagement"
    :icon="Connection"
    :menu-items="menuItems"
    :default-tab="'plugins'"
    :tab-slugs="['plugins', 'runners']"
  >
    <template #default="{ activeMenu: tab }">
      <PluginsView v-if="tab === 'plugins'" />
      <RunnersView v-else-if="tab === 'runners'" />
    </template>
  </ManagementHub>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Connection, Cpu } from '@element-plus/icons-vue'
import ManagementHub from '@/components/ManagementHub.vue'
import PluginsView from './Plugins.vue'
import RunnersView from './Runners.vue'

const activeMenu = ref('plugins')

const menuItems = [
  { key: 'plugins', icon: Connection, labelKey: 'nav.plugins' },
  { key: 'runners', icon: Cpu, labelKey: 'nav.runner' },
]
</script>
