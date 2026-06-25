<template>
  <div class="breakdown">
    <div class="line">
      <span>قیمت پایه</span>
      <strong>{{ formatMoney(breakdown.basePrice || 0, currency) }}</strong>
    </div>

    <div v-for="row in detailRows" :key="row.key" class="line detail">
      <span>{{ row.label }}</span>
      <strong :class="deltaClass(row.delta)">
        {{ deltaText(row.delta) }}
      </strong>
    </div>

    <div class="line total">
      <span>قیمت نهایی (هر عدد)</span>
      <strong>{{ formatMoney(breakdown.unitPrice || breakdown.basePrice || 0, currency) }}</strong>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  breakdown: {
    type: Object,
    default: () => ({}),
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
})

const detailRows = computed(() =>
  Array.isArray(props.breakdown?.details) ? props.breakdown.details : [],
)

function deltaClass(delta) {
  const value = Number(delta || 0)
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return ''
}

function deltaText(delta) {
  const value = Number(delta || 0)
  if (value > 0) return `+${formatMoney(value, props.currency)}`
  if (value < 0) return formatMoney(value, props.currency)
  return 'بدون تغییر'
}
</script>

<style scoped>
.breakdown {
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.46);
  padding: 0.62rem 0.72rem;
  display: grid;
  gap: 0.42rem;
}

.line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.82rem;
}

.line span {
  color: var(--text-muted);
}

.line.detail {
  font-size: 0.8rem;
}

.line.total {
  margin-top: 0.2rem;
  padding-top: 0.35rem;
  border-top: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.28);
}

.positive {
  color: var(--accent-gold);
}

.negative {
  color: #b14545;
}
</style>
