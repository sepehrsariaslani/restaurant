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
  border-radius: 22px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  background: #fff;
  box-shadow: 0 8px 20px rgb(15 23 42 / 0.06);
  overflow: visible;
}

.surface-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}

.surface-head h3 {
  margin: 0;
  font-size: 0.96rem;
}

.surface-head p {
  margin: 0.2rem 0 0;
  font-size: 0.78rem;
}

.tone-soft {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.04);
}

.tone-accent {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.07);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.28);
}
</style>
