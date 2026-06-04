<template>
  <GlassShell class="about-shell" :title="branding.name" :subtitle="'درباره ما'">
    <section class="about-page" dir="rtl">
      <section class="about-wrap">
        <header class="hero-panel glass-card" data-reveal>
          <div class="hero-top-row">
            <span class="hero-badge">{{ heroResolved.badge || 'ABOUT US' }}</span>
            <span class="hero-year">{{ toPersianDigits(heroResolved.founded_year || '1400') }}</span>
          </div>
          <h1>{{ heroResolved.title || 'داستان مجموعه ما' }}</h1>
          <p class="hero-subtitle">{{ heroResolved.subtitle || (branding.hero_subtitle || '') }}</p>
          <p class="hero-intro">{{ heroResolved.body_text }}</p>
          <div class="hero-actions">
            <a class="primary-btn" href="/menu">مشاهده منو</a>
            <a class="secondary-btn" href="/faq">سوالات متداول</a>
          </div>
        </header>

        <section class="mission-vision-grid">
          <article class="glass-card info-card" data-reveal v-if="mission">
            <span class="card-kicker">ماموریت</span>
            <h2>{{ mission.title }}</h2>
            <p>{{ mission.body_text }}</p>
          </article>
          <article class="glass-card info-card" data-reveal v-if="vision">
            <span class="card-kicker">چشم انداز</span>
            <h2>{{ vision.title }}</h2>
            <p>{{ vision.body_text }}</p>
          </article>
        </section>

        <section class="values-section" data-reveal v-if="values.length">
          <div class="section-head">
            <span class="kicker">ارزش ها</span>
            <h2>ارزش های کلیدی ما</h2>
          </div>
          <div class="values-grid">
            <article
              v-for="(item, idx) in values"
              :key="`${item.title}-${idx}`"
              class="glass-card value-card"
            >
              <span class="value-icon">{{ item.icon || '✦' }}</span>
              <h3>{{ item.title }}</h3>
              <p>{{ item.body_text }}</p>
            </article>
          </div>
        </section>

        <section class="history-section" data-reveal v-if="history">
          <article class="glass-card history-overview">
            <span class="kicker">تاریخچه</span>
            <h2>{{ history.title }}</h2>
            <p class="history-intro">{{ history.subtitle }}</p>
            <p>{{ history.body_text }}</p>
          </article>
        </section>

        <section class="timeline-section" data-reveal v-if="timeline.length">
          <div class="section-head">
            <span class="kicker">مسیر رشد</span>
            <h2>خط زمانی پیشرفت</h2>
          </div>
          <ol class="timeline-zigzag">
            <li
              v-for="(event, idx) in timeline"
              :key="`${event.year_label}-${event.title}-${idx}`"
              class="timeline-row"
              :class="[(idx % 2 === 0 ? 'left' : 'right'), { highlight: Number(event.highlight || 0) === 1 }]"
            >
              <span class="timeline-center-dot" aria-hidden="true"></span>
              <article class="glass-card timeline-content">
                <span class="timeline-step">{{ toPersianDigits(event.year_label || '') }}</span>
                <h3>{{ event.title }}</h3>
                <p>{{ event.body_text }}</p>
              </article>
            </li>
          </ol>
        </section>

        <section class="glass-card empty-state" v-if="!activeSections.length">
          <p class="muted">محتوای درباره ما هنوز ثبت نشده است.</p>
        </section>
      </section>
    </section>
  </GlassShell>
</template>

<script setup>
import { computed } from 'vue'
import GlassShell from '@/components/GlassShell.vue'

const props = defineProps({
  boot: {
    type: Object,
    default: () => ({}),
  },
})

const branding = computed(() => props.boot.branding || {})

const activeSections = computed(() => {
  const rows = Array.isArray(props.boot.about_us_sections) ? props.boot.about_us_sections : []
  return rows
    .map((row) => ({
      name: String(row?.name || '').trim(),
      section_type: String(row?.section_type || 'story').trim(),
      title: String(row?.title || '').trim(),
      subtitle: String(row?.subtitle || '').trim(),
      badge: String(row?.badge || '').trim(),
      founded_year: String(row?.founded_year || '').trim(),
      icon: String(row?.icon || '').trim(),
      year_label: String(row?.year_label || '').trim(),
      highlight: Number(row?.highlight || 0) ? 1 : 0,
      body_text: String(row?.body_text || '').trim(),
      image: String(row?.image || '').trim(),
      sort_order: Number(row?.sort_order || 0) || 0,
      is_active: Number(row?.is_active ?? 1) ? 1 : 0,
    }))
    .filter((row) => row.is_active !== 0)
    .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0))
})

function firstByType(typeName) {
  return activeSections.value.find((row) => String(row.section_type || '').toLowerCase() === typeName) || null
}

const hero = computed(() => firstByType('hero') || firstByType('story') || activeSections.value[0] || null)
const mission = computed(() => firstByType('mission'))
const vision = computed(() => firstByType('vision'))
const history = computed(() => firstByType('history'))
const values = computed(() => activeSections.value.filter((row) => String(row.section_type || '').toLowerCase() === 'value'))
const timeline = computed(() =>
  activeSections.value.filter((row) => String(row.section_type || '').toLowerCase() === 'timeline'),
)
const heroResolved = computed(() => {
  const row = hero.value || {}
  return {
    badge: String(row.badge || '').trim(),
    founded_year: String(row.founded_year || '').trim(),
    title: String(row.title || '').trim(),
    subtitle: String(row.subtitle || '').trim(),
    body_text: String(row.body_text || '').trim(),
  }
})

function toPersianDigits(value) {
  return String(value || '').replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[Number(digit)])
}
</script>

<style scoped>
.about-shell {
  background: #fff;
}

.about-page {
  color: var(--text-primary);
  background: #fff;
}

.about-wrap {
  width: min(1180px, calc(100% - 2rem));
  margin: 0 auto;
  padding-bottom: 1.2rem;
}

.hero-panel {
  margin-top: 0.4rem;
  border-radius: 28px;
  padding: 2rem 1.5rem;
}

.hero-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.9rem;
}

.hero-badge,
.hero-year {
  border-radius: 999px;
  padding: 0.35rem 0.75rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.25);
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--ink-900);
  font-size: 0.8rem;
  font-weight: 700;
}

.hero-panel h1 {
  margin: 0;
  font-size: clamp(1.7rem, 4vw, 2.7rem);
  line-height: 1.25;
}

.hero-subtitle {
  margin: 0.65rem 0 0;
  font-size: 1rem;
  color: var(--ink-800);
}

.hero-intro {
  margin: 0.8rem 0 0;
  line-height: 1.9;
  color: var(--text-muted);
}

.hero-actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.mission-vision-grid {
  margin-top: 0.9rem;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.info-card {
  border-radius: 22px;
}

.card-kicker,
.kicker {
  display: inline-block;
  margin-bottom: 0.45rem;
  color: var(--accent-gold);
  font-size: 0.8rem;
  font-weight: 700;
}

.info-card h2,
.section-head h2 {
  margin: 0;
}

.info-card p,
.history-overview p,
.value-card p,
.timeline-content p {
  margin: 0.6rem 0 0;
  line-height: 1.9;
  color: var(--text-muted);
}

.values-section,
.history-section,
.timeline-section {
  margin-top: 0.9rem;
}

.values-grid {
  margin-top: 0.6rem;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.65rem;
}

.value-card {
  border-radius: 20px;
}

.value-icon {
  display: inline-grid;
  place-items: center;
  width: 2.1rem;
  height: 2.1rem;
  border-radius: 10px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
}

.value-card h3 {
  margin: 0.45rem 0 0;
}

.history-overview {
  border-radius: 22px;
}

.history-intro {
  color: var(--ink-800);
}

.timeline-zigzag {
  list-style: none;
  margin: 0.7rem 0 0;
  padding: 0;
}

.timeline-row {
  display: flex;
  justify-content: center;
  margin-bottom: 0.6rem;
}

.timeline-content {
  width: min(700px, 100%);
  border-radius: 18px;
}

.timeline-step {
  display: inline-block;
  margin-bottom: 0.35rem;
  font-size: 0.78rem;
  color: var(--accent-gold);
}

.empty-state {
  margin-top: 0.8rem;
  text-align: center;
}

@media (max-width: 980px) {
  .about-wrap {
    width: min(760px, calc(100% - 1rem));
  }

  .mission-vision-grid,
  .values-grid {
    grid-template-columns: 1fr;
  }
}
</style>
