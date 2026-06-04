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

    <div class="nutrition-box" v-if="nutritionRows.length">
      <small>ارزش غذایی هر عدد</small>
      <div class="nutrition-chips">
        <span class="chip" v-for="row in nutritionRows" :key="row.key">{{ row.label }}</span>
      </div>
      <small v-if="nutritionTotalRows.length">برای کل سفارش: {{ nutritionTotalRows.join(' • ') }}</small>
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

const nutritionRows = computed(() => {
  const perUnit = props.breakdown?.nutrition || {}
  const rows = []
  const kcal = Number(perUnit?.kcal || 0)
  if (kcal > 0) {
    rows.push({ key: 'kcal', label: `${Math.round(kcal)} kcal` })
  }
  const protein = Number(perUnit?.protein_g || 0)
  if (protein > 0) {
    rows.push({ key: 'protein', label: `پروتئین ${formatMacro(protein)}g` })
  }
  const carb = Number(perUnit?.carb_g || 0)
  if (carb > 0) {
    rows.push({ key: 'carb', label: `کربوهیدرات ${formatMacro(carb)}g` })
  }
  const sugar = Number(perUnit?.sugar_g || 0)
  if (sugar > 0) {
    rows.push({ key: 'sugar', label: `قند ${formatMacro(sugar)}g` })
  }
  const fat = Number(perUnit?.fat_g || 0)
  if (fat > 0) {
    rows.push({ key: 'fat', label: `چربی ${formatMacro(fat)}g` })
  }
  return rows
})

const nutritionTotalRows = computed(() => {
  const totals = props.breakdown?.nutrition_totals || props.breakdown?.nutritionTotals || {}
  const rows = []
  const kcal = Number(totals?.kcal || 0)
  if (kcal > 0) {
    rows.push(`${Math.round(kcal)} kcal`)
  }
  const protein = Number(totals?.protein_g || 0)
  if (protein > 0) {
    rows.push(`پروتئین ${formatMacro(protein)}g`)
  }
  const carb = Number(totals?.carb_g || 0)
  if (carb > 0) {
    rows.push(`کربوهیدرات ${formatMacro(carb)}g`)
  }
  const sugar = Number(totals?.sugar_g || 0)
  if (sugar > 0) {
    rows.push(`قند ${formatMacro(sugar)}g`)
  }
  const fat = Number(totals?.fat_g || 0)
  if (fat > 0) {
    rows.push(`چربی ${formatMacro(fat)}g`)
  }
  return rows
})

function deltaText(value) {
  const amount = Number(value || 0)
  if (Math.abs(amount) < 1e-8) {
    return formatMoney(0, props.currency)
  }
  const sign = amount > 0 ? '+' : '-'
  return `${sign}${formatMoney(Math.abs(amount), props.currency)}`
}

function deltaClass(value) {
  const amount = Number(value || 0)
  if (Math.abs(amount) < 1e-8) {
    return 'neutral'
  }
  return amount > 0 ? 'positive' : 'negative'
}

function formatMacro(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return '0'
  }
  if (Math.abs(numeric - Math.round(numeric)) < 1e-8) {
    return String(Math.round(numeric))
  }
  return numeric.toFixed(1).replace(/\.0$/, '')
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

.neutral {
  color: var(--text-muted);
}

.nutrition-box {
  margin-top: 0.2rem;
  padding-top: 0.35rem;
  border-top: 1px dashed rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  display: grid;
  gap: 0.3rem;
}

.nutrition-box small {
  color: var(--text-muted);
}

.nutrition-chips {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.chip {
  border-radius: 999px;
  padding: 0.15rem 0.45rem;
  font-size: 0.72rem;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.09);
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
}
</style>
