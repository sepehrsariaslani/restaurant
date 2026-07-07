<template>
  <div class="section-header" :class="[`align-${align}`, `variant-${variant}`]">
    <span class="section-eyebrow" v-if="eyebrow">{{ eyebrow }}</span>
    <h2 class="section-heading">{{ title }}</h2>
    <p class="section-subtitle muted" v-if="subtitle">{{ subtitle }}</p>
    <slot name="action" />
  </div>
</template>

<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  align: { type: String, default: 'center' },
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['compact', 'default', 'feature'].includes(value),
  },
})
</script>

<style scoped>
.section-header {
  margin-bottom: 2rem;
}

.variant-compact {
  margin-bottom: 1.15rem;
}

.variant-feature {
  margin-bottom: 1.35rem;
}

.align-center {
  text-align: center;
}

.align-start {
  text-align: right;
}

.section-eyebrow {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--accent-green);
  background: var(--accent-green20);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  padding: 0.25rem 0.85rem;
  border-radius: 999px;
  margin-bottom: 0.7rem;
}

.section-heading {
  margin: 0;
  font-size: clamp(1.35rem, 3.5vw, 1.75rem);
  font-weight: 800;
  color: var(--ink-900);
  line-height: 1.3;
}

.section-subtitle {
  margin: 0.5rem 0 0;
  font-size: 0.92rem;
  line-height: 1.7;
  max-width: 540px;
}

.align-center .section-subtitle {
  margin-inline: auto;
}

@media (min-width: 920px) {
  .section-heading {
    font-size: 2.1rem;
  }

  .variant-compact .section-heading {
    font-size: 1.82rem;
  }

  .variant-feature .section-heading {
    font-size: 1.72rem;
  }
}
</style>
