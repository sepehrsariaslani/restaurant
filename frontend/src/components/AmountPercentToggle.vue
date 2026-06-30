<template>
  <div class="apt" role="group" :aria-label="ariaLabel">
    <button
      type="button"
      class="apt-seg"
      :class="{ active: modelValue === 'fixed' }"
      :aria-pressed="modelValue === 'fixed'"
      :title="amountTitle"
      @click="$emit('update:modelValue', 'fixed')"
    >
      <span class="apt-glyph">{{ currencySymbol }}</span>
    </button>
    <button
      type="button"
      class="apt-seg"
      :class="{ active: modelValue === 'percent' }"
      :aria-pressed="modelValue === 'percent'"
      :title="percentTitle"
      @click="$emit('update:modelValue', 'percent')"
    >
      <span class="apt-glyph">٪</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: 'fixed',
    validator: (v) => ['fixed', 'percent'].includes(v),
  },
  currencySymbol: {
    type: String,
    default: '﷼',
  },
  ariaLabel: {
    type: String,
    default: 'انتخاب نوع: مبلغ یا درصد',
  },
  amountTitle: {
    type: String,
    default: 'مبلغی',
  },
  percentTitle: {
    type: String,
    default: 'درصدی',
  },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.apt {
  display: inline-flex;
  align-items: stretch;
  padding: 2px;
  border-radius: 10px;
  background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.06);
  border: 1px solid rgb(var(--pos-primary-rgb, 1 90 114) / 0.18);
  gap: 2px;
  height: 32px;
  flex-shrink: 0;
}

.apt-seg {
  border: 0;
  background: transparent;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.7);
  font-family: inherit;
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1;
  padding: 0 0.55rem;
  min-width: 30px;
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}

.apt-seg:hover:not(.active) {
  background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.08);
  color: var(--pos-primary, #015a72);
}

.apt-seg.active {
  background: var(--pos-white, #fff);
  color: var(--pos-primary, #015a72);
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.08);
}

.apt-seg:focus-visible {
  outline: 2px solid rgb(var(--pos-accent-rgb, 255 152 54) / 0.6);
  outline-offset: 1px;
}

.apt-glyph {
  display: inline-block;
  font-variant-numeric: tabular-nums;
}
</style>
