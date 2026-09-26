<template>
  <section class="management-page" :class="{ 'management-page--compact': compact }" dir="rtl">
    <slot name="breadcrumbs" />
    <header v-if="title || subtitle || $slots.actions || $slots.header" class="glass-card hero-card management-page__header">
      <div>
        <p class="management-page__eyebrow" v-if="eyebrow">{{ eyebrow }}</p>
        <h1 v-if="title">{{ title }}</h1>
        <p class="muted" v-if="subtitle">{{ subtitle }}</p>
      </div>
      <div class="hero-actions" v-if="$slots.actions">
        <slot name="actions" />
      </div>
      <slot name="header" />
    </header>
    <div v-if="$slots.toolbar" class="management-page__toolbar"><slot name="toolbar" /></div>
    <div v-if="$slots.status" class="management-page__status" aria-live="polite"><slot name="status" /></div>
    <slot />
  </section>
</template>

<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: '',
  },
  compact: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.management-page {
  display: grid;
  gap: var(--ds-space-4, 1rem);
  width: 100%;
  min-width: 0;
  color: var(--ds-color-text-primary, var(--mg-text-main));
}

.hero-card {
  border-radius: var(--ds-radius-md, 16px);
  border: 1px solid var(--ds-color-border, var(--mg-border-light));
  background: var(--ds-color-surface, var(--mg-bg-surface));
  box-shadow: var(--ds-shadow-sm, var(--mg-shadow-sm));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-4, 1rem);
  padding: clamp(var(--ds-space-4, 1rem), 2vw, var(--ds-space-5, 1.25rem));
  min-width: 0;
}

.hero-card h1 {
  margin: 0;
  color: var(--ds-color-text-primary, var(--mg-text-main));
  font-size: clamp(1.1rem, 1vw + 0.85rem, 1.4rem);
  font-weight: 900;
  line-height: 1.35;
}

.management-page__eyebrow {
  margin: 0 0 var(--ds-space-1, .25rem);
  color: var(--ds-color-action-accent, var(--mg-primary));
  font-size: .75rem;
  font-weight: 800;
}

.hero-card p {
  margin: var(--ds-space-1, .25rem) 0 0;
  color: var(--ds-color-text-secondary, var(--mg-text-muted));
  font-size: .86rem;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: var(--ds-space-2, .5rem);
  flex-wrap: wrap;
  min-width: 0;
}

.management-page__toolbar,
.management-page__status,
.management-page > :deep(*) {
  min-width: 0;
}

.management-page--compact { gap: var(--ds-space-3, .75rem); }

@media (max-width: 860px) {
  .hero-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .hero-actions {
    width: 100%;
    overflow-x: auto;
    padding-bottom: 0.2rem;
    flex-wrap: nowrap;
  }
}

@media (max-width: 520px) {
  .hero-card h1 {
    font-size: 1.05rem;
  }
}
</style>
