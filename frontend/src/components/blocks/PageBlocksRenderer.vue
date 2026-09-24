<template>
  <div class="page-blocks" dir="rtl">
    <ScrollReveal
      v-for="(block, index) in blocks"
      :key="block.id"
      :threshold="isHomePage ? 0.08 : 0.15"
      :delay="isHomePage ? Math.min(index, 4) * 35 : Math.min(index, 6) * 80"
    >
      <BlockRenderer :block="block" :boot="boot" @quick-add="$emit('quick-add', $event)" />
    </ScrollReveal>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BlockRenderer from '@/components/blocks/BlockRenderer.vue'
import ScrollReveal from '@/components/ScrollReveal.vue'
import { resolvePageLayout } from '@/utils/pageLayout'

const props = defineProps({
  boot: { type: Object, default: () => ({}) },
  page: { type: String, default: 'home' },
})

defineEmits(['quick-add'])

const blocks = computed(() => resolvePageLayout(props.boot, props.page))
const isHomePage = computed(() => ['home', 'homev2'].includes(String(props.page || '').toLowerCase()))
</script>

<style scoped>
.page-blocks {
  display: flex;
  flex-direction: column;
  gap: clamp(2.5rem, 6vw, 5rem);
}
</style>
