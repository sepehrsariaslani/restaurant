<template>
  <section class="insight-grid" v-if="insights.length">
    <article v-for="item in insights" :key="item.key || item.text" :class="severityClass(item.severity)">
      <strong>{{ severityLabel(item.severity) }}</strong>
      <p>{{ item.text }}</p>
    </article>
  </section>
</template>

<script setup>
defineProps({
  insights: {
    type: Array,
    default: () => [],
  },
})

function severityClass(severity) {
  const normalized = String(severity || 'info').toLowerCase()
  return `tone-${normalized}`
}

function severityLabel(severity) {
  const normalized = String(severity || 'info').toLowerCase()
  if (normalized === 'warn') {
    return 'هشدار'
  }
  if (normalized === 'success') {
    return 'نکته مثبت'
  }
  return 'تحلیل'
}
</script>

<style scoped>
.insight-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.insight-grid article {
  border-radius: 12px;
  padding: 0.5rem;
  border: 1px solid transparent;
  display: grid;
  gap: 0.2rem;
}

.insight-grid strong {
  font-size: 0.78rem;
}

.insight-grid p {
  margin: 0;
  font-size: 0.78rem;
  color: var(--text-muted);
  line-height: 1.75;
}

.tone-info {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.2);
}

.tone-warn {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.12);
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.28);
}

.tone-success {
  background: rgb(var(--success-rgb) / 0.12);
  border-color: rgb(var(--success-rgb) / 0.28);
}

@media (max-width: 780px) {
  .insight-grid {
    grid-template-columns: 1fr;
  }
}
</style>
