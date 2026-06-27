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
  gap: 1rem;
}

.hero-card {
  border-radius: 16px;
  border: 1px solid var(--border, #e2e8f0);
  background: linear-gradient(180deg, var(--bg-card, #fff) 0%, color-mix(in srgb, var(--bg-card, #fff) 92%, var(--bg-soft, #f1f5f9)) 100%);
  box-shadow: var(--shadow-sm, 0 14px 34px rgb(15 23 42 / 0.06));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  padding: clamp(0.9rem, 2vw, 1.25rem);
}

.hero-card h2 {
  margin: 0;
  color: var(--text-primary, #0f172a);
  font-size: clamp(1.02rem, 1vw + 0.8rem, 1.35rem);
  font-weight: 900;
  line-height: 1.35;
}

.hero-card p {
  margin: 0.24rem 0 0;
  color: var(--text-muted, #64748b);
  font-size: 0.86rem;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

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
  .hero-card h2 {
    font-size: 0.95rem;
  }
}
</style>
