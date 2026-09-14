<template>
  <button
    class="ds-button"
    :class="[`ds-button--${variant}`, `ds-button--${size}`]"
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading ? 'true' : 'false'"
  >
    <LoaderCircle v-if="loading" class="ds-button__loader" :size="16" aria-hidden="true" />
    <slot />
  </button>
</template>

<script setup>
import { LoaderCircle } from 'lucide-vue-next'

defineProps({
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  type: { type: String, default: 'button' },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})
</script>

<style scoped>
.ds-button {
  min-height: 44px;
  border: 1px solid transparent;
  border-radius: var(--ds-radius-pill);
  padding: 0 var(--ds-space-4);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-2);
  font: inherit;
  font-size: 0.84rem;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  transition: transform var(--ds-motion-fast) var(--ds-motion-ease), background-color var(--ds-motion-fast) ease, border-color var(--ds-motion-fast) ease, box-shadow var(--ds-motion-fast) ease, opacity var(--ds-motion-fast) ease;
}

.ds-button:hover:not(:disabled) { transform: translateY(-1px); }
.ds-button:active:not(:disabled) { transform: scale(0.98); }
.ds-button:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
.ds-button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.ds-button--sm { min-height: 40px; padding-inline: var(--ds-space-3); font-size: 0.78rem; }
.ds-button--primary { color: var(--ds-color-text-inverse); background: var(--ds-color-action-primary); box-shadow: var(--ds-shadow-sm); }
.ds-button--accent { color: var(--ds-color-text-inverse); background: var(--ds-color-action-accent); }
.ds-button--secondary { color: var(--ds-color-action-primary); background: var(--ds-color-surface-raised); border-color: var(--ds-color-border); }
.ds-button--quiet { color: var(--ds-color-text-secondary); background: transparent; }
.ds-button--danger { color: var(--ds-color-status-danger); background: var(--ds-color-status-danger-soft); border-color: color-mix(in srgb, var(--ds-color-status-danger) 28%, var(--ds-color-border)); }
.ds-button__loader { animation: ds-spin 0.8s linear infinite; }
@keyframes ds-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .ds-button { transition: background-color 0.01ms, border-color 0.01ms, opacity 0.01ms; } .ds-button__loader { animation: none; } }
</style>
