<template>
  <PageBlocksRenderer :page="page" :boot="boot" @quick-add="$emit('quick-add', $event)" />
</template>

<script setup>
import PageBlocksRenderer from '@/components/blocks/PageBlocksRenderer.vue'

const props = defineProps({
  boot: { type: Object, default: () => ({}) },
  page: { type: String, default: 'home' },
})

defineEmits(['quick-add'])
</script>
