<template>
  <section class="kpi-grid" v-if="kpis.length">
    <article class="kpi-card" v-for="kpi in kpis" :key="kpi.key">
      <small>{{ kpi.label }}</small>
      <strong>{{ formatKpiValue(kpi) }}</strong>
      <div class="meta-row">
        <span class="change" :class="trendClass(kpi.trend)">{{ formatChange(kpi.change_pct) }}</span>
        <small>{{ kpi.change_label || 'نسبت به بازه قبل' }}</small>
      </div>
      <a v-if="kpi.action_url" :href="kpi.action_url">{{ kpi.action_label || 'مشاهده' }}</a>
    </article>
  </section>
</template>

<script setup>
import { formatMoney } from '@/utils/format'

const props = defineProps({
  kpis: {
    type: Array,
    default: () => [],
  },
  currency: {
    type: String,
    default: 'IRR',
  },
})

function formatKpiValue(kpi) {
  const value = Number(kpi?.value || 0)
  const unit = String(kpi?.unit || '').toLowerCase()

  if (unit === 'money') {
    return formatMoney(value, props.currency)
  }
  if (unit === 'percent') {
    return `${value.toLocaleString('fa-IR')}%`
  }
  if (unit === 'minutes' || unit === 'min') {
    return `${value.toLocaleString('fa-IR')} دقیقه`
  }
  if (unit === 'score') {
    return `${value.toLocaleString('fa-IR')} از 10`
  }
  return value.toLocaleString('fa-IR')
}

function formatChange(value) {
  const numeric = Number(value || 0)
  const sign = numeric > 0 ? '+' : ''
  return `${sign}${numeric.toFixed(1)}%`
}

function trendClass(trend) {
  const normalized = String(trend || '').toLowerCase()
  if (normalized === 'up') {
    return 'up'
  }
  if (normalized === 'down') {
    return 'down'
  }
  return 'flat'
}
</script>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.6rem;
}

.kpi-card {
  border-radius: 14px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.2);
  background: rgb(var(--palette-eggshell-rgb) / 0.58);
  padding: 0.55rem;
  display: grid;
  gap: 0.22rem;
}

.kpi-card small {
  color: var(--text-muted);
  font-size: 0.74rem;
}

.kpi-card strong {
  font-size: 0.95rem;
}

.meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
}

.change {
  font-size: 0.74rem;
  font-weight: 600;
}

.change.up {
  color: var(--success);
}

.change.down {
  color: var(--danger);
}

.change.flat {
  color: var(--text-muted);
}

.kpi-card a {
  font-size: 0.73rem;
  color: var(--accent-green);
}

@media (max-width: 980px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
