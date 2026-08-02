<template>
  <ManagementInventoryPage :initial-tab="initialTab" />
</template>

<script setup>
import ManagementInventoryPage from './ManagementInventoryPage.vue'

defineProps({ initialTab: { type: String, default: 'overview' } })
</script>
