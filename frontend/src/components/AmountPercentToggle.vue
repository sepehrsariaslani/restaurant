<template>
  <div class="apt" role="group" :aria-label="ariaLabel">
    <button
      type="button"
      class="apt-seg"
      :class="{ active: modelValue === 'fixed' }"
      :aria-pressed="modelValue === 'fixed'"
      :disabled="disabled"
      :title="amountTitle"
      @click="$emit('update:modelValue', 'fixed')"
    >
      <Banknote :size="15" :stroke-width="2.2" />
    </button>
    <button
      type="button"
      class="apt-seg"
      :class="{ active: modelValue === 'percent' }"
      :aria-pressed="modelValue === 'percent'"
      :disabled="disabled"
      :title="percentTitle"
      @click="$emit('update:modelValue', 'percent')"
    >
      <Percent :size="14" :stroke-width="2.5" />
    </button>
  </div>
</template>

<script setup>
import { Banknote, Percent } from 'lucide-vue-next'

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
  disabled: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.apt {
  display: inline-flex;
  align-items: stretch;
  padding: 2px;
  border-radius: 9px;
  background: rgb(var(--mg-primary-rgb, 1 90 114) / 0.06);
  border: 1px solid rgb(var(--mg-primary-rgb, 1 90 114) / 0.12);
  gap: 2px;
  height: 30px;
  flex-shrink: 0;
}

.apt-seg {
  border: 0;
  background: transparent;
  color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.45);
  font-family: inherit;
  line-height: 1;
  padding: 0 0.45rem;
  min-width: 28px;
  border-radius: 7px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}

.apt-seg:hover:not(.active) {
  background: rgb(var(--mg-primary-rgb, 1 90 114) / 0.08);
  color: rgb(var(--mg-primary-rgb, 1 90 114) / 0.7);
}

.apt-seg.active {
  background: var(--pos-white, #fff);
  color: var(--mg-primary, #015a72);
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.08);
}

.apt-seg:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.apt-seg:focus-visible {
  outline: 2px solid rgb(var(--mg-primary-rgb, 255 152 54) / 0.6);
  outline-offset: 1px;
}
</style>
