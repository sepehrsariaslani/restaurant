<template>
  <section class="home-about glass-card" dir="rtl" v-if="sections.length">
    <div class="section-head">
      <h3 class="section-title">درباره ما</h3>
      <a href="/about-us" class="more-link">مشاهده کامل</a>
    </div>

    <div class="about-grid">
      <article class="about-card" v-for="section in visibleSections" :key="section.name || section.title">
        <img
          class="about-image"
          :src="section.image || fallbackImage"
          :alt="section.title"
        />
        <div class="about-body">
          <h4>{{ section.title }}</h4>
          <p class="muted">{{ section.subtitle }}</p>
          <p class="body">{{ excerpt(section.body_text) }}</p>
          <div class="stat-row" v-if="section.stat_value || section.stat_label">
            <strong>{{ section.stat_value }}</strong>
            <small>{{ section.stat_label }}</small>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  sections: {
    type: Array,
    default: () => [],
  },
})

const fallbackImage =
  'https://images.unsplash.com/photo-1551218808-94e220e084d2?w=900&auto=format&fit=crop&q=60'

const visibleSections = computed(() => (props.sections || []).slice(0, 2))

function excerpt(value) {
  const text = String(value || '').trim()
  if (text.length <= 140) {
    return text
  }
  return `${text.slice(0, 140)}...`
}
</script>

<style scoped>
.home-about {
  margin-top: 0.8rem;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
}

.more-link {
  border-radius: 999px;
  padding: 0.3rem 0.7rem;
  font-size: 0.78rem;
  background: var(--accent-green20);
  color: var(--ink-800);
}

.about-grid {
  margin-top: 0.7rem;
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.about-card {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 0.75rem;
  border-radius: 18px;
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  overflow: hidden;
}

.about-image {
  width: 160px;
  height: 100%;
  min-height: 160px;
  object-fit: cover;
}

.about-body {
  padding: 0.65rem;
}

.about-body h4 {
  margin: 0;
  font-size: 1.04rem;
}

.about-body .muted {
  margin: 0.3rem 0 0;
  font-size: 0.78rem;
}

.body {
  margin: 0.35rem 0 0;
  font-size: 0.82rem;
  line-height: 1.75;
}

.stat-row {
  margin-top: 0.4rem;
  display: inline-flex;
  gap: 0.35rem;
  align-items: baseline;
}

.stat-row strong {
  color: var(--accent-green);
  font-size: 1rem;
}

.stat-row small {
  color: var(--text-muted);
  font-size: 0.73rem;
}

@media (max-width: 980px) {
  .about-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .about-card {
    grid-template-columns: 1fr;
  }

  .about-image {
    width: 100%;
    height: 150px;
  }
}
</style>
