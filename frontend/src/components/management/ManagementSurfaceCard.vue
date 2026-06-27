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
  border-radius: 16px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--bg-card, #fff);
  box-shadow: var(--shadow-sm, 0 12px 30px rgb(15 23 42 / 0.05));
  overflow: visible;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.surface-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.8rem;
}

.surface-head h3 {
  margin: 0;
  color: var(--text-primary, #0f172a);
  font-size: 1rem;
  font-weight: 900;
  line-height: 1.45;
}

.surface-head p {
  margin: 0.2rem 0 0;
  color: var(--text-muted, #64748b);
  font-size: 0.82rem;
  line-height: 1.65;
}

.tone-soft {
  background: color-mix(in srgb, var(--bg-card, #fff) 88%, var(--bg-soft, #f1f5f9));
}

.tone-accent {
  background: linear-gradient(180deg, var(--bg-card, #fff), color-mix(in srgb, var(--bg-card, #fff) 86%, var(--module-50, rgb(139 94 52 / 0.075))));
  border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.16);
}

@media (hover: hover) {
  .surface-card:hover {
    border-color: rgb(var(--palette-deep-sapphire-rgb, 139 94 52) / 0.18);
    box-shadow: 0 18px 42px rgb(15 23 42 / 0.08);
  }
}
</style>
