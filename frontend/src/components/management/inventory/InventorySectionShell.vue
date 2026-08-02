<template>
  <ManagementPageScaffold v-if="showHeader" :title="title" :subtitle="subtitle">
    <template #actions>
      <slot name="actions" />
    </template>
    <section class="inventory-section-shell" dir="rtl">
      <slot />
    </section>
  </ManagementPageScaffold>

  <section v-else class="inventory-section-shell" dir="rtl">
    <slot />
  </section>
</template>

<script setup>
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'

defineProps({
  title: { type: String, default: 'انبارداری' },
  subtitle: { type: String, default: '' },
  showHeader: { type: Boolean, default: true },
})
</script>

<style scoped>
.inventory-section-shell {
  --inv-primary: var(--mg-primary);
  --inv-success: var(--mg-success);
  --inv-surface: var(--mg-bg-surface);
  --inv-page: var(--mg-bg-page);
  --inv-text: var(--mg-text-main);
  --inv-muted: var(--mg-text-muted);
  --inv-border: var(--mg-border-light);
  display: grid;
  gap: 0.9rem;
  color: var(--inv-text);
}

.inventory-section-shell :deep(.surface-card) {
  border-color: color-mix(in srgb, var(--mg-border) 78%, transparent);
  background: linear-gradient(180deg, var(--inv-surface) 0%, color-mix(in srgb, var(--inv-surface) 92%, var(--inv-page) 8%) 100%);
  box-shadow: 0 16px 34px rgb(52 38 31 / 0.07);
}

.inventory-section-shell :deep(.surface-head h3) {
  color: var(--inv-text);
}

.inventory-section-shell :deep(.surface-head p),
.inventory-section-shell .muted {
  color: var(--inv-muted);
}

.inventory-section-shell :deep(.input) {
  border-color: var(--inv-border);
  background: var(--inv-surface);
  color: var(--inv-text);
}

.inventory-section-shell :deep(.primary-btn) {
  background: var(--inv-primary);
  border-color: var(--inv-primary);
}

.inventory-section-shell :deep(.secondary-btn) {
  border-color: color-mix(in srgb, var(--inv-primary) 28%, var(--inv-border) 72%);
  color: var(--inv-primary);
}
</style>
