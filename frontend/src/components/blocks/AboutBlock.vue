<template>
  <section class="blk about" dir="rtl" v-if="visibleSections.length">
    <div class="blk__head blk__head--between">
      <div>
        <span v-if="eyebrow" class="blk__eyebrow">{{ eyebrow }}</span>
        <h2 class="blk__title">{{ title }}</h2>
        <p v-if="subtitle" class="blk__subtitle">{{ subtitle }}</p>
      </div>
      <a v-if="moreLabel" class="blk__more" :href="moreHref">{{ moreLabel }}</a>
    </div>

    <!-- CARDS -->
    <div v-if="variant === 'cards'" class="about-cards">
      <article v-for="(s, idx) in visibleSections" :key="s.name || idx" class="about-card">
        <div class="about-card__media">
          <AboutMedia :image="s.image" :alt="s.title" :title="s.title" />
        </div>
        <div class="about-card__body">
          <h3 data-design-collection="about_sections" :data-design-index="sections.indexOf(s)" data-design-site-key="title">{{ s.title }}</h3>
          <p v-if="s.subtitle" class="about-card__sub" data-design-collection="about_sections" :data-design-index="sections.indexOf(s)" data-design-site-key="subtitle">{{ s.subtitle }}</p>
          <p class="about-card__text" data-design-collection="about_sections" :data-design-index="sections.indexOf(s)" data-design-site-key="body_text">{{ excerpt(s.body_text) }}</p>
          <div v-if="s.stat_value || s.stat_label" class="about-card__stat">
            <strong data-design-collection="about_sections" :data-design-index="sections.indexOf(s)" data-design-site-key="stat_value">{{ s.stat_value }}</strong>
            <small data-design-collection="about_sections" :data-design-index="sections.indexOf(s)" data-design-site-key="stat_label">{{ s.stat_label }}</small>
          </div>
        </div>
      </article>
    </div>

    <!-- STORY -->
    <div v-else-if="variant === 'story'" class="about-story">
      <div class="about-story__media">
        <AboutMedia :image="primary.image" :alt="primary.title" :title="primary.title" variant="story" />
      </div>
      <div class="about-story__body">
        <h3 data-design-collection="about_sections" :data-design-index="sections.indexOf(primary)" data-design-site-key="title">{{ primary.title }}</h3>
        <p v-if="primary.subtitle" class="about-card__sub" data-design-collection="about_sections" :data-design-index="sections.indexOf(primary)" data-design-site-key="subtitle">{{ primary.subtitle }}</p>
        <p class="about-story__text" data-design-collection="about_sections" :data-design-index="sections.indexOf(primary)" data-design-site-key="body_text">{{ primary.body_text }}</p>
      </div>
    </div>

    <!-- STATS -->
    <div v-else class="about-stats">
      <div v-for="(s, idx) in visibleSections" :key="s.name || idx" class="about-stat">
        <strong>{{ s.stat_value || s.year_label || '\u2014' }}</strong>
        <span>{{ s.stat_label || s.title }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import AboutMedia from '@/components/blocks/AboutMedia.vue'
import '@/components/blocks/blocks.css'

const props = defineProps({
  variant: { type: String, default: 'cards' },
  eyebrow: { type: String, default: '' },
  title: { type: String, default: '\u062f\u0631\u0628\u0627\u0631\u0647 \u0645\u0627' },
  subtitle: { type: String, default: '' },
  moreLabel: { type: String, default: '' },
  moreHref: { type: String, default: '/about-us' },
  sections: { type: Array, default: () => [] },
  limit: { type: Number, default: 3 },
})

const activeSections = computed(() =>
  (props.sections || []).filter((s) => Number(s?.is_active ?? 1) !== 0),
)

const visibleSections = computed(() => {
  const rows = activeSections.value
  return props.limit > 0 ? rows.slice(0, props.limit) : rows
})

const primary = computed(() => visibleSections.value[0] || {})

function excerpt(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  if (text.length <= 150) return text
  const cut = text.slice(0, 150)
  const lastSpace = cut.lastIndexOf(' ')
  return `${cut.slice(0, lastSpace > 90 ? lastSpace : 150).trim()}\u2026`
}

</script>

<style scoped>
.about-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--blk-gap);
}

.about-card {
  display: flex;
  flex-direction: column;
  background: var(--blk-surface);
  border: 1px solid var(--blk-border);
  border-radius: var(--blk-radius);
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.about-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 40px rgb(0 0 0 / 0.08);
}

.about-card__media {
  border-radius: var(--blk-radius) var(--blk-radius) 0 0;
  overflow: hidden;
}

.about-card__body {
  padding: 1.1rem 1.15rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.about-card__body h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
}

.about-card__sub {
  margin: 0;
  font-size: 0.85rem;
  color: var(--blk-ink-soft);
}

.about-card__text {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.85;
  color: var(--blk-ink-soft);
}

.about-card__stat {
  margin-top: 0.35rem;
  display: inline-flex;
  align-items: baseline;
  gap: 0.4rem;
}

.about-card__stat strong {
  font-size: 1.15rem;
  color: var(--blk-accent);
}

.about-card__stat small {
  font-size: 0.78rem;
  color: var(--blk-ink-soft);
}

/* Story */
.about-story {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: clamp(1.5rem, 4vw, 3rem);
  align-items: center;
}

.about-story__media {
  border-radius: var(--blk-radius);
  overflow: hidden;
}

.about-story__body h3 {
  margin: 0 0 0.6rem;
  font-size: clamp(1.3rem, 3vw, 1.9rem);
  font-weight: 800;
}

.about-story__text {
  margin: 0.6rem 0 0;
  font-size: 0.98rem;
  line-height: 1.95;
  color: var(--blk-ink-soft);
  white-space: pre-line;
}

/* Stats */
.about-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--blk-gap);
  text-align: center;
}

.about-stat {
  padding: 1.5rem 1rem;
  border-radius: var(--blk-radius);
  background: var(--blk-surface-soft);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.about-stat strong {
  font-size: clamp(1.6rem, 4vw, 2.4rem);
  font-weight: 800;
  color: var(--blk-accent);
}

.about-stat span {
  font-size: 0.9rem;
  color: var(--blk-ink-soft);
}

@media (max-width: 800px) {
  .about-story {
    grid-template-columns: 1fr;
  }

  .about-story__media {
    order: -1;
  }
}
</style>
