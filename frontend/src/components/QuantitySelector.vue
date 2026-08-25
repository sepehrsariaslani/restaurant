<template>
  <div class="qty-selector">
    <span class="qty-label">تعداد:</span>
    <button
      class="qty-btn qty-minus"
      type="button"
      :disabled="modelValue <= min || disabled"
      @click="decrement"
      aria-label="کاهش تعداد"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>
    </button>
    <span class="qty-value" aria-live="polite">{{ modelValue }}</span>
    <button
      class="qty-btn qty-plus"
      type="button"
      :disabled="modelValue >= max || disabled"
      @click="increment"
      aria-label="افزایش تعداد"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: { type: Number, default: 1 },
  min: { type: Number, default: 1 },
  max: { type: Number, default: 99 },
  step: { type: Number, default: 1 },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

function increment() {
  if (props.modelValue < props.max) {
    emit('update:modelValue', props.modelValue + props.step)
  }
}

function decrement() {
  if (props.modelValue > props.min) {
    emit('update:modelValue', props.modelValue - props.step)
  }
}
</script>

<style scoped>
.qty-selector {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 999px;
  background: var(--preview-bg);
  border: 1px solid var(--preview-border);
}

.qty-label {
  font-size: 0.82rem;
  color: var(--preview-muted);
  white-space: nowrap;
}

.qty-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 999px;
  border: 1px solid var(--preview-border);
  background: var(--preview-surface);
  color: var(--preview-primary);
  cursor: pointer;
  transition: background 0.15s ease, transform 0.1s ease;
  flex-shrink: 0;
}

.qty-btn:hover:not(:disabled) {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.06);
}

.qty-btn:active:not(:disabled) {
  transform: scale(0.92);
}

.qty-btn:focus-visible {
  outline: 2px solid var(--preview-primary);
  outline-offset: 2px;
}

.qty-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.qty-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--preview-text);
  min-width: 2ch;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

/* Mobile: larger touch targets */
@media (max-width: 767px) {
  .qty-btn {
    width: 48px;
    height: 48px;
  }
}
</style>
