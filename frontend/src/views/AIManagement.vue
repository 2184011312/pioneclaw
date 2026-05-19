<template>
  <ManagementHub
    v-model="activeMenu"
    title-key="nav.aiManagement"
    :icon="MagicStick"
    :menu-items="menuItems"
    :default-tab="'ai-configs'"
    :tab-slugs="['ai-configs', 'channels', 'logs']"
  >
    <template #default="{ activeMenu: tab }">
      <AIConfigsView v-if="tab === 'ai-configs'" />
      <ChannelsView v-else-if="tab === 'channels'" />
      <LogsView v-else-if="tab === 'logs'" />
    </template>
  </ManagementHub>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MagicStick, ChatLineSquare, SetUp, Document } from '@element-plus/icons-vue'
import ManagementHub from '@/components/ManagementHub.vue'
import AIConfigsView from './AIConfigs.vue'
import ChannelsView from './Channels.vue'
import LogsView from './Logs.vue'

const activeMenu = ref('ai-configs')

const menuItems = [
  { key: 'ai-configs', icon: SetUp, labelKey: 'nav.aiConfigs' },
  { key: 'channels', icon: ChatLineSquare, labelKey: 'nav.channels' },
  { key: 'logs', icon: Document, labelKey: 'nav.logs' },
]
</script>
