<template>
  <ManagementHub
    v-model="activeMenu"
    title-key="nav.systemOps"
    :icon="Operation"
    :menu-items="menuItems"
    :default-tab="'monitor'"
    :tab-slugs="['monitor', 'settings']"
  >
    <template #default="{ activeMenu: tab }">
      <MonitorView v-if="tab === 'monitor'" />
      <SettingsView v-else-if="tab === 'settings'" />
    </template>
  </ManagementHub>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Monitor, Setting, Operation } from '@element-plus/icons-vue'
import ManagementHub from '@/components/ManagementHub.vue'
import MonitorView from './Monitor.vue'
import SettingsView from './Settings.vue'

const activeMenu = ref('monitor')

const menuItems = [
  { key: 'monitor', icon: Monitor, labelKey: 'nav.monitor' },
  { key: 'settings', icon: Setting, labelKey: 'nav.settings' },
]
</script>
