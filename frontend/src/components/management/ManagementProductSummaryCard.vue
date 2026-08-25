<template>
  <ManagementSurfaceCard tone="accent" class="product-summary-card">
    <div class="product-summary-head">
      <div>
        <strong>{{ title }}</strong>
        <small>{{ subtitle }}</small>
      </div>
      <a v-if="customerUrl" class="primary-pill-link" :href="customerUrl" target="_blank" rel="noreferrer">
        مشاهده صفحه مشتری ←
      </a>
    </div>
    <div class="product-summary-grid" aria-label="خلاصه وضعیت محصول">
      <article v-for="chip in chips" :key="chip.key" :class="['summary-chip', `tone-${chip.tone || 'neutral'}`]">
        <span>{{ chip.label }}</span>
        <strong>{{ chip.value }}</strong>
      </article>
    </div>
  </ManagementSurfaceCard>
</template>

<script setup>
import ManagementSurfaceCard from './ManagementSurfaceCard.vue'

defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  customerUrl: {
    type: String,
    default: '',
  },
  chips: {
    type: Array,
    default: () => [],
  },
})
</script>

<style scoped>
.product-summary-card {
  position: relative;
  overflow: hidden;
}

.product-summary-card::before {
  content: '';
  position: absolute;
  inset: 0 auto auto 0;
  width: 180px;
  height: 180px;
  pointer-events: none;
  background: radial-gradient(circle, rgb(var(--palette-deep-sapphire-rgb) / 0.12), transparent 68%);
  transform: translate(-38%, -42%);
}

.product-summary-head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.7rem;
}

.product-summary-head > div {
  display: grid;
  gap: 0.18rem;
}

.product-summary-head strong {
  color: var(--text-primary, var(--mg-text-main));
  font-size: 1rem;
}

.product-summary-head small {
  color: var(--text-muted, var(--mg-text-muted));
  line-height: 1.55;
}

.product-summary-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 0.48rem;
}

.summary-chip {
  min-height: 4.6rem;
  border: 1px solid var(--border, var(--mg-border-light));
  border-radius: 12px;
  background: color-mix(in srgb, var(--bg-card, #fff) 88%, transparent);
  padding: 0.62rem;
  display: grid;
  align-content: space-between;
  gap: 0.35rem;
  box-shadow: 0 10px 24px rgb(72 52 38 / 0.06);
}

.summary-chip span {
  color: var(--text-muted, var(--mg-text-muted));
  font-size: 0.72rem;
  font-weight: 800;
}

.summary-chip strong {
  color: var(--text-primary, var(--mg-text-main));
  font-size: 0.86rem;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.summary-chip.tone-success {
  border-color: rgb(var(--success-rgb) / 0.28);
  background: linear-gradient(145deg, rgb(var(--success-rgb) / 0.11), rgb(255 255 255 / 0.82));
}

.summary-chip.tone-danger {
  border-color: rgb(var(--danger-rgb) / 0.28);
  background: linear-gradient(145deg, rgb(var(--danger-rgb) / 0.1), rgb(255 255 255 / 0.82));
}

.summary-chip.tone-warn {
  border-color: rgb(218 138 47 / 0.35);
  background: linear-gradient(145deg, rgb(218 138 47 / 0.12), rgb(255 255 255 / 0.82));
}

.summary-chip.tone-info {
  border-color: rgb(62 142 208 / 0.28);
  background: linear-gradient(145deg, rgb(62 142 208 / 0.1), rgb(255 255 255 / 0.82));
}

@media (max-width: 980px) {
  .product-summary-head {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
