<template>
  <span class="ds-badge" :class="`ds-badge--${tone}`">
    <slot />
  </span>
</template>

<script setup>
defineProps({
  tone: { type: String, default: 'neutral' },
})
</script>

<style scoped>
.ds-badge { min-height: 28px; padding: 0 var(--ds-space-3); border: 1px solid transparent; border-radius: var(--ds-radius-pill); display: inline-flex; align-items: center; gap: var(--ds-space-1); color: var(--ds-color-text-secondary); background: var(--ds-color-surface-muted); font: inherit; font-size: 0.76rem; font-weight: 700; line-height: 1; }
.ds-badge--neutral { color: var(--ds-color-text-secondary); background: var(--ds-color-surface-muted); border-color: var(--ds-color-border); }
.ds-badge--primary { color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.ds-badge--success { color: var(--ds-color-status-success); background: var(--ds-color-status-success-soft); }
.ds-badge--warning { color: var(--ds-color-status-warning); background: var(--ds-color-status-warning-soft); }
.ds-badge--danger { color: var(--ds-color-status-danger); background: var(--ds-color-status-danger-soft); }
.ds-badge--info { color: var(--ds-color-status-info); background: var(--ds-color-status-info-soft); }
</style>
