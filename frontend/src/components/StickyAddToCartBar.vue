<template>
  <div class="sticky-add">
    <div class="price-info">
      <small class="hint" v-if="hint">{{ hint }}</small>
      <strong class="total">{{ formatMoney(total, currency) }}</strong>
    </div>

    <button
      class="add-action"
      type="button"
      :disabled="disabled"
      @click="$emit('action')"
    >
      <span>{{ buttonText }}</span>
      <span class="plus-circle">+</span>
    </button>
  </div>
</template>

<script setup>
import { formatMoney } from '@/utils/format'

defineProps({
  total:      { type: Number, default: 0 },
  currency:   { type: String, default: 'TOMAN' },
  hint:       { type: String, default: '' },
  buttonText: { type: String, default: 'افزودن به سبد' },
  disabled:   { type: Boolean, default: false },
})

defineEmits(['action'])
</script>

<style scoped>
.sticky-add {
  position: sticky;
  z-index: 20;
  border-radius: 20px;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  color: var(--text-primary);
  padding: 0.75rem 0.75rem 0.75rem 1.1rem;
  display: flex; align-items: center; justify-content: space-between;
  gap: 0.8rem;
  box-shadow: 0 14px 34px rgb(15 23 42 / 0.1), 0 0 0 1px rgb(var(--palette-deep-sapphire-rgb) / 0.1) inset;
}

.price-info {
  display: flex; flex-direction: column; gap: 0.1rem;
}

.hint {
  display: block; font-size: 0.67rem;
  color: var(--text-muted);
}

.total {
  font-size: 1rem; font-weight: 700;
  color: var(--text-primary);
}

/* دکمه مثل رفرنس — pill با دایره + */
.add-action {
  border: 0; border-radius: 999px;
  background: var(--accent-green);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.48);
  color: #fff;
  padding: 0 0.6rem 0 1rem;
  height: 44px;
  display: inline-flex; align-items: center; gap: 0.55rem;
  font-family: inherit; font-size: 0.87rem;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.18s ease;
  flex-shrink: 0;
}

.add-action:hover:not(:disabled) {
  background: var(--accent-green80);
  transform: scale(1.02);
}

.add-action:active:not(:disabled) { transform: scale(0.97); }

.add-action:disabled {
  opacity: 0.38; cursor: not-allowed;
}

.plus-circle {
  width: 28px; height: 28px; border-radius: 50%;
  background: rgb(var(--palette-eggshell-rgb) / 0.92);
  color: var(--accent-green);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 1.2rem; line-height: 1;
}
</style>
