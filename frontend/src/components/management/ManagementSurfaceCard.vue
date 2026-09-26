<template>
  <section class="glass-card surface-card" :class="toneClass">
    <header class="surface-head" v-if="title || subtitle || $slots.head">
      <div>
        <h3 v-if="title">{{ title }}</h3>
        <p class="muted" v-if="subtitle">{{ subtitle }}</p>
      </div>
      <slot name="head" />
    </header>
    <slot />
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  tone: {
    type: String,
    default: 'base',
  },
})

const toneClass = computed(() => `tone-${props.tone || 'base'}`)
</script>

<style scoped>
.surface-card {
  min-width: 0;
  border-radius: var(--ds-radius-md, 16px);
  border: 1px solid var(--ds-color-border, var(--border, var(--mg-border-light)));
  background: var(--ds-color-surface, var(--bg-card, #fff));
  box-shadow: var(--ds-shadow-sm, var(--shadow-sm, 0 8px 24px rgb(52 38 31 / 0.06)));
  overflow: visible;
  transition: border-color var(--ds-motion-fast, 160ms) ease, box-shadow var(--ds-motion-fast, 160ms) ease;
}

.surface-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-3, .75rem);
  margin-bottom: var(--ds-space-3, .75rem);
}

.surface-head h3 {
  margin: 0;
  color: var(--ds-color-text-primary, var(--text-primary, var(--mg-text-main)));
  font-size: 1rem;
  font-weight: 900;
  line-height: 1.45;
}

.surface-head p {
  margin: 0.2rem 0 0;
  color: var(--ds-color-text-muted, var(--text-muted, var(--mg-text-muted)));
  font-size: 0.82rem;
  line-height: 1.65;
}

.tone-soft {
  background: var(--ds-color-surface-muted, color-mix(in srgb, var(--bg-card, #fff) 88%, var(--bg-soft, var(--mg-bg-page))));
}

.tone-accent {
  background: var(--ds-color-surface, var(--bg-card, #fff));
  border-color: color-mix(in srgb, var(--ds-color-action-primary, var(--mg-primary)) 28%, var(--ds-color-border, var(--mg-border-light)));
}

@media (hover: hover) {
  .surface-card:hover {
    border-color: color-mix(in srgb, var(--ds-color-action-primary, var(--mg-primary)) 38%, var(--ds-color-border, var(--mg-border-light)));
  }
}

@media (prefers-reduced-motion: reduce) {
  .surface-card { transition: none; }
}
</style>
