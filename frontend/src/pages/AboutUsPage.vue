<template>
  <div v-if="hasCustomLayout" class="about-builder-shell" dir="rtl">
    <PageBlocksRenderer page="about" :boot="boot" />
  </div>
  <div v-else class="about-page" dir="rtl">
    <div class="about-wrap">
      <header class="about-hero">
        <div class="about-hero__copy">
          <span class="about-eyebrow"><Leaf :size="17" aria-hidden="true" /> درباره {{ branding.name || 'ما' }}</span>
          <h1>{{ heroResolved.title || 'داستان مجموعه ما' }}</h1>
          <p class="about-lead" v-if="heroResolved.subtitle">{{ heroResolved.subtitle }}</p>
          <p class="about-intro" v-if="heroResolved.body_text">{{ heroResolved.body_text }}</p>
          <div class="about-actions">
            <a class="about-primary" href="/menu">دیدن منو <ArrowUpLeft :size="18" aria-hidden="true" /></a>
            <a class="about-secondary" href="#our-values" v-if="values.length">ارزش‌های ما <ArrowDown :size="17" aria-hidden="true" /></a>
          </div>
        </div>
        <div class="about-hero__visual" :class="{ 'about-hero__visual--image': hero?.image }">
          <img v-if="hero?.image" :src="hero.image" :alt="heroResolved.title || branding.name" />
          <template v-else>
            <span class="about-hero__circle" aria-hidden="true"><Leaf :size="70" :stroke-width="1.2" /></span>
            <strong>{{ branding.name || 'رستوران ما' }}</strong>
          </template>
          <span class="about-founded" v-if="heroResolved.founded_year">از {{ toPersianDigits(heroResolved.founded_year) }} در کنار شما</span>
        </div>
      </header>

      <section class="about-purpose" v-if="mission || vision" aria-label="نگاه ما">
        <article v-if="mission" class="about-purpose__card">
          <span class="about-kicker"><Target :size="18" aria-hidden="true" /> ماموریت</span>
          <h2>{{ mission.title }}</h2>
          <p>{{ mission.body_text }}</p>
        </article>
        <article v-if="vision" class="about-purpose__card">
          <span class="about-kicker"><Eye :size="18" aria-hidden="true" /> چشم‌انداز</span>
          <h2>{{ vision.title }}</h2>
          <p>{{ vision.body_text }}</p>
        </article>
      </section>

      <section id="our-values" class="about-section" v-if="values.length">
        <div class="about-section__head"><span class="about-eyebrow">آنچه برای ما مهم است</span><h2>ارزش‌های ما</h2></div>
        <div class="about-values">
          <article class="about-value" v-for="(item, index) in values" :key="item.name || index">
            <span class="about-value__icon"><component :is="valueIcon(item, index)" :size="23" aria-hidden="true" /></span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.body_text }}</p>
          </article>
        </div>
      </section>

      <section class="about-section about-history" v-if="history || timeline.length">
        <div class="about-section__head"><span class="about-eyebrow">مسیر ما</span><h2>{{ history?.title || 'از شروع تا امروز' }}</h2><p v-if="history?.body_text">{{ history.body_text }}</p></div>
        <ol class="about-timeline" v-if="timeline.length">
          <li v-for="(event, index) in timeline" :key="event.name || index">
            <span class="about-timeline__year">{{ toPersianDigits(event.year_label || '') }}</span>
            <div><h3>{{ event.title }}</h3><p>{{ event.body_text }}</p></div>
          </li>
        </ol>
      </section>

      <div class="about-empty" v-if="!activeSections.length"><p>داستان مجموعه به‌زودی اینجا منتشر می‌شود.</p><a href="/menu">مشاهده منو</a></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowDown, ArrowUpLeft, ChefHat, Eye, Heart, Leaf, Sparkles, Target } from 'lucide-vue-next'
import PageBlocksRenderer from '@/components/blocks/PageBlocksRenderer.vue'
import { hasStoredPageLayout } from '@/utils/pageLayout'

const props = defineProps({ boot: { type: Object, default: () => ({}) } })
const branding = computed(() => props.boot.branding || {})
const hasCustomLayout = computed(() => hasStoredPageLayout(props.boot, 'about'))
const activeSections = computed(() => (Array.isArray(props.boot.about_us_sections) ? props.boot.about_us_sections : [])
  .filter((row) => Number(row?.is_active ?? 1) !== 0)
  .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0)))
const firstByType = (type) => activeSections.value.find((row) => String(row.section_type || '').toLowerCase() === type) || null
const hero = computed(() => firstByType('hero') || firstByType('story') || activeSections.value[0] || null)
const mission = computed(() => firstByType('mission'))
const vision = computed(() => firstByType('vision'))
const history = computed(() => firstByType('history'))
const values = computed(() => activeSections.value.filter((row) => String(row.section_type || '').toLowerCase() === 'value'))
const timeline = computed(() => activeSections.value.filter((row) => String(row.section_type || '').toLowerCase() === 'timeline'))
const heroResolved = computed(() => ({
  title: String(hero.value?.title || '').trim(),
  subtitle: String(hero.value?.subtitle || '').trim(),
  body_text: String(hero.value?.body_text || '').trim(),
  founded_year: String(hero.value?.founded_year || '').trim(),
}))
function toPersianDigits(value) { return String(value || '').replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[Number(digit)]) }
function valueIcon(item, index) {
  const title = String(item?.title || '')
  if (/کیفیت|مواد|تازه/.test(title)) return Leaf
  if (/پخت|آشپز/.test(title)) return ChefHat
  if (/مشتری|رضایت/.test(title)) return Heart
  return [Sparkles, Heart, Leaf][index % 3]
}
</script>

<style scoped>
.about-builder-shell { padding-block: clamp(1.5rem, 4vw, 3rem); background: var(--ds-color-bg-page); }
.about-page { background: var(--ds-color-bg-page); color: var(--ds-color-text-primary); }
.about-wrap { width: min(1160px, calc(100% - 2rem)); margin: auto; padding: clamp(1.5rem, 4vw, 3rem) 0 clamp(3rem, 6vw, 5rem); }
.about-hero { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(280px, .85fr); gap: clamp(1.5rem, 4vw, 3rem); align-items: center; padding: clamp(1.25rem, 3vw, 2rem); border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); box-shadow: var(--ds-shadow-sm); }
.about-eyebrow, .about-kicker { display: inline-flex; align-items: center; gap: .45rem; color: var(--ds-color-action-primary); font-size: .83rem; font-weight: 800; }
.about-hero h1 { margin: .8rem 0 .7rem; font-size: clamp(2rem, 5vw, 3.5rem); line-height: 1.22; letter-spacing: -.025em; }
.about-lead { margin: 0; color: var(--ds-color-text-primary); font-size: clamp(1rem, 2vw, 1.2rem); font-weight: 700; line-height: 1.75; }
.about-intro { max-width: 42rem; margin: .85rem 0 0; color: var(--ds-color-text-secondary); font-size: .95rem; line-height: 2; }
.about-actions { display: flex; gap: .6rem; flex-wrap: wrap; margin-top: 1.5rem; }
.about-actions a { display: inline-flex; align-items: center; justify-content: center; gap: .4rem; min-height: 46px; padding: .65rem 1rem; border-radius: var(--ds-radius-md); font-size: .88rem; font-weight: 800; text-decoration: none; }
.about-primary { background: var(--ds-color-action-accent); color: var(--ds-color-action-accent-foreground); }
.about-secondary { border: 1px solid var(--ds-color-border); background: var(--ds-color-surface-muted); color: var(--ds-color-text-primary); }
.about-hero__visual { position: relative; min-height: 325px; border-radius: var(--ds-radius-lg); background: var(--ds-color-action-primary-soft); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: .5rem; overflow: hidden; color: var(--ds-color-action-primary); }
.about-hero__visual::before { content: ''; position: absolute; inset: 1rem; border: 1px solid color-mix(in srgb, var(--ds-color-action-primary) 20%, transparent); border-radius: calc(var(--ds-radius-lg) - 5px); pointer-events: none; }
.about-hero__visual img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.about-hero__visual strong { font-size: 1.35rem; font-weight: 900; }
.about-hero__circle { display: grid; place-items: center; width: 9rem; height: 9rem; border-radius: 50%; background: var(--ds-color-surface-raised); box-shadow: var(--ds-shadow-md); }
.about-founded { position: absolute; inset-inline-start: 1.2rem; bottom: 1.2rem; padding: .5rem .75rem; border-radius: var(--ds-radius-pill); background: var(--ds-color-surface-raised); color: var(--ds-color-action-primary); font-size: .76rem; font-weight: 800; box-shadow: var(--ds-shadow-sm); }
.about-purpose { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 1rem; }
.about-purpose__card, .about-value { border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); padding: clamp(1.25rem, 2.5vw, 1.75rem); }
.about-purpose__card h2 { margin: .8rem 0 .4rem; font-size: 1.35rem; }
.about-purpose__card p, .about-value p, .about-section__head p, .about-timeline p { margin: 0; color: var(--ds-color-text-secondary); line-height: 1.85; font-size: .9rem; }
.about-section { margin-top: clamp(2.5rem, 5vw, 4rem); scroll-margin-top: 6rem; }
.about-section__head { max-width: 45rem; margin-bottom: 1.2rem; }
.about-section__head h2 { margin: .45rem 0; font-size: clamp(1.5rem, 3vw, 2.2rem); }
.about-values { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
.about-value__icon { display: grid; place-items: center; width: 48px; height: 48px; border-radius: var(--ds-radius-md); background: var(--ds-color-action-accent-soft); color: var(--ds-color-action-accent); }
.about-value h3 { margin: 1rem 0 .35rem; font-size: 1.08rem; }
.about-history { padding: clamp(1.25rem, 3vw, 2rem); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-muted); }
.about-timeline { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .8rem; list-style: none; margin: 1.5rem 0 0; padding: 0; }
.about-timeline li { padding: 1.2rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface-raised); }
.about-timeline__year { color: var(--ds-color-action-accent); font-size: 1.1rem; font-weight: 900; }
.about-timeline h3 { margin: .55rem 0 .3rem; font-size: 1rem; }
.about-empty { padding: 2rem; text-align: center; }
.about-empty a { color: var(--ds-color-action-primary); font-weight: 800; }
.about-page a:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 3px; }
@media (max-width: 760px) { .about-wrap { padding-bottom: calc(8rem + env(safe-area-inset-bottom)); } .about-hero { grid-template-columns: 1fr; } .about-hero__visual { min-height: 230px; } .about-values { grid-template-columns: 1fr 1fr; } .about-timeline { grid-template-columns: 1fr; } }
@media (max-width: 520px) { .about-purpose, .about-values { grid-template-columns: 1fr; } .about-actions a { flex: 1; } }
</style>
