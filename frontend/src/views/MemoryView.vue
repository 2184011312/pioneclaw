<template>
  <ManagementHub
    v-model="activeMenu"
    title-key="nav.memory"
    :icon="Memo"
    :menu-items="menuItems"
    :default-tab="'layered'"
    :tab-slugs="['file', 'layered']"
  >
    <template #default="{ activeMenu: tab }">
      <FileMemory v-if="tab === 'file'" />
      <LayeredMemoryPanel v-else-if="tab === 'layered'" :stats="track2Stats" @updated="loadT2Stats" />
    </template>
  </ManagementHub>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Memo, Notebook, Histogram } from '@element-plus/icons-vue'
import { layeredMemoryApi, type LayeredMemoryStats } from '@/api/layeredMemory'
import ManagementHub from '@/components/ManagementHub.vue'
import FileMemory from './FileMemory.vue'
import LayeredMemoryPanel from './LayeredMemory.vue'

const activeMenu = ref('layered')

const menuItems = [
  { key: 'file', icon: Notebook, labelKey: 'memory.track1' },
  { key: 'layered', icon: Histogram, labelKey: 'memory.track2' },
]

const track2Stats = ref<LayeredMemoryStats>({
  total: 0, l0_count: 0, l1_count: 0, l2_count: 0,
  by_type: {}, by_source: {}, vector_count: 0,
})

async function loadT2Stats() {
  try {
    const { data } = await layeredMemoryApi.stats()
    if (data) track2Stats.value = data
  } catch { /* ignore */ }
}

onMounted(() => {
  loadT2Stats()
})
</script>
