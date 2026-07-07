<template>
  <div class="bar-list">
    <article class="bar-row" v-for="row in rows" :key="row.key || row.label">
      <header>
        <strong>{{ row.label }}</strong>
        <small>{{ formatValue(row.value) }}</small>
      </header>
      <div class="track">
        <span class="fill" :style="{ width: `${barWidth(row.value)}%`, background: row.color || 'var(--accent-green)' }"></span>
      </div>
    </article>

    <p class="empty" v-if="!rows.length">داده‌ای برای نمایش وجود ندارد.</p>
  </div>
</template>

<script setup>
const props = defineProps({
  rows: {
    type: Array,
    default: () => [],
  },
  mode: {
    type: String,
    default: 'money',
  },
  currency: {
    type: String,
    default: 'IRR',
  },
})

function maxValue() {
  const values = (props.rows || []).map((row) => Number(row.value || 0))
  const max = Math.max(...values, 1)
  return max > 0 ? max : 1
}

function barWidth(value) {
  return Math.max((Number(value || 0) * 100) / maxValue(), 2)
}

function formatValue(value) {
  const numeric = Number(value || 0)
  if (props.mode === 'count') {
    return `${numeric.toLocaleString('fa-IR')} عدد`
  }
  return `${numeric.toLocaleString('fa-IR')} ${props.currency === 'IRR' ? 'ریال' : props.currency}`
}
</script>

<style scoped>
.bar-list {
  display: grid;
  gap: 0.5rem;
}

.bar-row {
  display: grid;
  gap: 0.25rem;
}

.bar-row header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.bar-row strong {
  font-size: 0.8rem;
}

.bar-row small {
  color: var(--text-muted);
  font-size: 0.74rem;
}

.track {
  width: 100%;
  border-radius: 999px;
  height: 8px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  overflow: hidden;
}

.fill {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.empty {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.82rem;
}
</style>
