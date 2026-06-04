<template>
  <div class="feature-card glass-card">
    <div class="feature-icon-wrap">
      <span class="feature-icon">{{ icon }}</span>
    </div>
    <h4 class="feature-title">{{ title }}</h4>
    <p class="feature-desc muted">{{ description }}</p>
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>

<style scoped>
.feature-card {
  text-align: center;
  padding: 1.6rem 1.2rem;
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-deep);
}

.feature-icon-wrap {
  width: 3.4rem;
  height: 3.4rem;
  margin: 0 auto 1rem;
  border-radius: 16px;
  background: var(--accent-green20);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.feature-icon {
  font-size: 1.6rem;
}

.feature-title {
  margin: 0 0 0.4rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink-900);
}

.feature-desc {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.7;
}
</style>
