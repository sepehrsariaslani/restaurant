<template>
  <section class="management-page">
    <header class="glass-card hero-card">
      <div>
        <h2>{{ title }}</h2>
        <p class="muted" v-if="subtitle">{{ subtitle }}</p>
      </div>
      <div class="hero-actions" v-if="$slots.actions">
        <slot name="actions" />
      </div>
    </header>
    <slot />
  </section>
</template>

<script setup>
defineProps({
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
  gap: 0.75rem;
}

.hero-card {
  border-radius: 22px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  background: #fff;
  box-shadow: 0 10px 24px rgb(15 23 42 / 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.7rem;
}

.hero-card h2 {
  margin: 0;
  font-size: 1.06rem;
}

.hero-card p {
  margin: 0.24rem 0 0;
  font-size: 0.8rem;
}

.hero-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

@media (max-width: 860px) {
  .hero-card {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
