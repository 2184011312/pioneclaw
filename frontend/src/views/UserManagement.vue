<template>
  <ManagementHub
    v-model="activeMenu"
    title-key="nav.userManagement"
    :icon="Setting"
    :menu-items="menuItems"
    :default-tab="'users'"
    :tab-slugs="['users', 'roles', 'organizations', 'permissions']"
  >
    <template #default="{ activeMenu: tab }">
      <UsersView v-if="tab === 'users'" />
      <RolesView v-else-if="tab === 'roles'" />
      <OrganizationsView v-else-if="tab === 'organizations'" />
      <PermissionsView v-else-if="tab === 'permissions'" />
    </template>
  </ManagementHub>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { User, UserFilled, OfficeBuilding, Lock, Setting } from '@element-plus/icons-vue'
import ManagementHub from '@/components/ManagementHub.vue'
import UsersView from './Users.vue'
import RolesView from './Roles.vue'
import OrganizationsView from './Organizations.vue'
import PermissionsView from './Permissions.vue'

const activeMenu = ref('users')

const menuItems = [
  { key: 'users', icon: User, labelKey: 'nav.users' },
  { key: 'roles', icon: UserFilled, labelKey: 'nav.roles' },
  { key: 'organizations', icon: OfficeBuilding, labelKey: 'nav.organizations' },
  { key: 'permissions', icon: Lock, labelKey: 'nav.permissions' },
]
</script>
