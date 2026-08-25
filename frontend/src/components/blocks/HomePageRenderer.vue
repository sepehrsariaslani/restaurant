<template>
  <PageBlocksRenderer page="home" :boot="boot" @quick-add="$emit('quick-add', $event)" />
</template>

<script setup>
import PageBlocksRenderer from '@/components/blocks/PageBlocksRenderer.vue'

const props = defineProps({
  boot: { type: Object, default: () => ({}) },
})

defineEmits(['quick-add'])
</script>
