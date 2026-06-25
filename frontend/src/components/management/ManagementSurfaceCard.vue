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
  border-radius: 8px;
  border: 1px solid #e4ded6;
  background: #fff;
  box-shadow: 0 12px 30px rgb(15 23 42 / 0.06);
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
  color: #2b211a;
  font-size: 1rem;
  font-weight: 900;
  line-height: 1.45;
}

.surface-head p {
  margin: 0.2rem 0 0;
  color: #74685f;
  font-size: 0.82rem;
  line-height: 1.65;
}

.tone-soft {
  background: #fbfaf8;
}

.tone-accent {
  background: #f7f1ea;
  border-color: rgb(124 90 66 / 0.18);
}

@media (hover: hover) {
  .surface-card:hover {
    border-color: rgb(124 90 66 / 0.18);
    box-shadow: 0 18px 42px rgb(15 23 42 / 0.08);
  }
}
</style>
