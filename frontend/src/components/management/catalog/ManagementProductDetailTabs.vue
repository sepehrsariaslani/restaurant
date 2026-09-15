<template>
  <ManagementSurfaceCard tone="soft" class="section-picker-shell">
    <div class="section-picker">
      <div class="simple-tabs" role="tablist" aria-label="بخش‌های جزئیات محصول">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="simple-tab"
          :class="{ active: activeTab === tab.value }"
          type="button"
          role="tab"
          :aria-selected="activeTab === tab.value"
          @click="$emit('update:active-tab', tab.value)"
        >
          <span>{{ tab.label }}</span>
          <span v-if="badges?.[tab.value]" class="tab-badge">{{ badges[tab.value] }}</span>
        </button>
      </div>
      <button class="secondary-btn" type="button" @click="$emit('refresh')" :disabled="loading">
        {{ loading ? 'در حال بروزرسانی...' : 'تازه‌سازی' }}
      </button>
    </div>
  </ManagementSurfaceCard>
</template>

<script setup>
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'

defineProps({
  tabs: { type: Array, default: () => [] },
  activeTab: { type: String, default: 'overview' },
  badges: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
})

defineEmits(['update:active-tab', 'refresh'])
</script>

<style scoped>
.section-picker-shell { min-width: 0; }
.section-picker { display: flex; align-items: center; justify-content: space-between; gap: .55rem; flex-wrap: wrap; padding: .65rem; border-radius: var(--mg-radius-md); background: var(--mg-bg-surface); border: 1px solid var(--mg-border-light); box-shadow: var(--mg-shadow-sm); }
.simple-tabs { display: flex; align-items: center; gap: .28rem; flex-wrap: wrap; min-width: 0; }
.simple-tab { min-height: 2.7rem; border: 1px solid transparent; border-radius: 8px; background: transparent; color: var(--mg-text-muted); padding: .34rem .68rem; font: inherit; font-size: .78rem; font-weight: 850; cursor: pointer; display: inline-flex; align-items: center; gap: .34rem; white-space: nowrap; }
.simple-tab:hover, .simple-tab.active { background: var(--mg-bg-surface); border-color: color-mix(in srgb, var(--mg-primary) 28%, transparent); color: var(--mg-text-main); box-shadow: inset 0 -2px 0 color-mix(in srgb, var(--mg-primary) 55%, transparent); }
.tab-badge { min-width: 1.32rem; min-height: 1.32rem; border-radius: 999px; display: inline-grid; place-items: center; padding: 0 .34rem; background: var(--module-50); color: var(--module-title-light); font-size: .66rem; line-height: 1; }
@media (max-width: 700px) { .section-picker { align-items: stretch; flex-direction: column; } .simple-tabs { overflow-x: auto; flex-wrap: nowrap; padding-bottom: .2rem; } .section-picker > .secondary-btn { width: 100%; justify-content: center; } }
@media (max-width: 560px) { .simple-tabs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); width: 100%; } .simple-tab { width: 100%; justify-content: center; white-space: normal; } }
</style>
