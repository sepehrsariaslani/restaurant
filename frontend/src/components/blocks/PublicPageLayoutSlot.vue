<template>
  <section v-if="hasCustomLayout" class="public-page-layout-slot" dir="rtl" aria-label="محتوای افزوده‌شدهٔ صفحه">
    <PageBlocksRenderer :page="page" :boot="boot" />
  </section>
</template>

<script setup>
import { computed } from 'vue'
import PageBlocksRenderer from '@/components/blocks/PageBlocksRenderer.vue'
import { hasStoredPageLayout } from '@/utils/pageLayout'

const props = defineProps({
  page: { type: String, required: true },
  boot: { type: Object, default: () => ({}) },
})

const hasCustomLayout = computed(() => hasStoredPageLayout(props.boot, props.page))
</script>

<style scoped>
.public-page-layout-slot {
  padding-block: clamp(1rem, 3vw, 2rem);
  background: var(--ds-color-bg-page, var(--bg-soft, #f7f5f2));
}

.public-page-layout-slot :deep(.page-blocks) {
  width: min(1160px, calc(100% - 2rem));
  margin-inline: auto;
}
</style>
