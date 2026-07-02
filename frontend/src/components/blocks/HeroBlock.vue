<template>
  <section class="blk hero" :class="`hero--${variant}`" dir="rtl">
    <!-- COVER: big image background, centered copy -->
    <div v-if="variant === 'cover'" class="hero-cover" :style="coverStyle">
      <div class="hero-cover__inner">
        <span v-if="eyebrow" class="blk__eyebrow hero-cover__eyebrow">{{ eyebrow }}</span>
        <h1 class="hero-cover__title">{{ title }}</h1>
        <p v-if="description" class="hero-cover__desc">{{ description }}</p>
        <div class="hero-actions">
          <a class="blk-btn blk-btn--primary" :href="ctaHref">{{ ctaLabel }}</a>
          <a v-if="secondaryLabel" class="blk-btn blk-btn--ghost hero-cover__ghost" :href="secondaryHref">{{ secondaryLabel }}</a>
        </div>
      </div>
    </div>

    <!-- SPLIT: copy one side, image other side -->
    <div v-else-if="variant === 'split'" class="hero-split">
      <div class="hero-split__copy">
        <span v-if="eyebrow" class="blk__eyebrow">{{ eyebrow }}</span>
        <h1 class="hero-split__title">{{ title }}</h1>
        <p v-if="description" class="blk__subtitle">{{ description }}</p>
        <div class="hero-actions">
          <a class="blk-btn blk-btn--primary" :href="ctaHref">{{ ctaLabel }}</a>
          <a v-if="secondaryLabel" class="blk-btn blk-btn--ghost" :href="secondaryHref">{{ secondaryLabel }}</a>
        </div>
      </div>
      <div class="hero-split__media">
        <img :src="image || fallbackImage" :alt="title" loading="lazy" />
      </div>
    </div>

    <!-- MINIMAL: text only, tight -->
    <div v-else-if="variant === 'minimal'" class="hero-minimal">
      <span v-if="eyebrow" class="blk__eyebrow">{{ eyebrow }}</span>
      <h1 class="hero-minimal__title">{{ title }}</h1>
      <p v-if="description" class="blk__subtitle hero-minimal__desc">{{ description }}</p>
      <div class="hero-actions hero-minimal__actions">
        <a class="blk-btn blk-btn--primary" :href="ctaHref">{{ ctaLabel }}</a>
        <a v-if="secondaryLabel" class="blk-btn blk-btn--ghost" :href="secondaryHref">{{ secondaryLabel }}</a>
      </div>
    </div>

    <!-- SLIDER: horizontal image slides -->
    <div v-else class="hero-slider">
      <div class="hero-slider__track">
        <a
          v-for="(slide, idx) in normalizedSlides"
          :key="slide.name || idx"
          class="hero-slide"
          :href="slide.href"
          :style="slide.image ? { backgroundImage: `url('${slide.image}')` } : {}"
        >
          <div class="hero-slide__overlay">
            <strong>{{ slide.title }}</strong>
            <span v-if="slide.subtitle">{{ slide.subtitle }}</span>
            <em v-if="slide.cta" class="hero-slide__cta">{{ slide.cta }}</em>
          </div>
        </a>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import '@/components/blocks/blocks.css'

const props = defineProps({
  variant: { type: String, default: 'cover' },
  eyebrow: { type: String, default: '' },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  image: { type: String, default: '' },
  ctaLabel: { type: String, default: '\u0645\u0634\u0627\u0647\u062f\u0647 \u0645\u0646\u0648' },
  ctaHref: { type: String, default: '/menu' },
  secondaryLabel: { type: String, default: '' },
  secondaryHref: { type: String, default: '' },
  slides: { type: Array, default: () => [] },
  currency: { type: String, default: 'IRR' },
})

const fallbackImage =
  'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200&auto=format&fit=crop&q=70'

const coverStyle = computed(() => ({
  backgroundImage: `linear-gradient(180deg, rgb(0 0 0 / 0.15), rgb(0 0 0 / 0.55)), url('${props.image || fallbackImage}')`,
}))

const normalizedSlides = computed(() =>
  (props.slides || [])
    .filter((s) => Number(s?.is_active ?? 1) !== 0)
    .map((s) => ({
      name: s.name,
      title: String(s.title || s.item_title || '').trim(),
      subtitle: String(s.subtitle || s.short_desc || '').trim(),
      image: String(s.image || s.item_image || '').trim(),
      cta: String(s.cta_label || '').trim(),
      href: String(s.cta_url || (s.slug ? `/menu/${s.slug}` : '/menu')).trim(),
    })),
)
</script>

<style scoped>
.hero {
  width: min(1200px, calc(100% - 2rem));
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 1.35rem;
}

/* Cover */
.hero-cover {
  position: relative;
  border-radius: var(--blk-radius);
  overflow: hidden;
  background-size: cover;
  background-position: center;
  min-height: clamp(340px, 52vh, 520px);
  display: flex;
  align-items: center;
}

.hero-cover__inner {
  padding: var(--blk-pad);
  max-width: 44ch;
  color: #fff;
}

.hero-cover__eyebrow {
  color: #fff;
  background: rgb(255 255 255 / 0.2);
}

.hero-cover__title {
  margin: 0.5rem 0 0;
  font-size: clamp(1.9rem, 5vw, 3.1rem);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.hero-cover__desc {
  margin: 0.85rem 0 0;
  font-size: 1.02rem;
  line-height: 1.8;
  color: rgb(255 255 255 / 0.9);
}

.hero-cover__ghost {
  color: #fff;
  border-color: rgb(255 255 255 / 0.5);
}

/* Split */
.hero-split {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: clamp(1.5rem, 4vw, 3rem);
  align-items: center;
}

.hero-split__title {
  margin: 0.5rem 0 0.9rem;
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.hero-split__media img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: var(--blk-radius);
}

/* Minimal */
.hero-minimal {
  text-align: center;
  max-width: 60ch;
  margin-inline: auto;
  padding-block: clamp(2rem, 6vw, 4rem);
}

.hero-minimal .blk__eyebrow {
  align-self: center;
}

.hero-minimal__title {
  margin: 0.75rem 0 0;
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 800;
  line-height: 1.18;
  letter-spacing: -0.02em;
}

.hero-minimal__desc {
  margin-inline: auto;
  margin-top: 1rem;
}

.hero-minimal__actions {
  justify-content: center;
}

/* Slider */
.hero-slider__track {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: min(78%, 460px);
  gap: 1rem;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  padding-bottom: 0.5rem;
  scrollbar-width: none;
}

.hero-slider__track::-webkit-scrollbar {
  display: none;
}

.hero-slide {
  scroll-snap-align: start;
  position: relative;
  min-height: clamp(260px, 40vh, 380px);
  border-radius: var(--blk-radius);
  overflow: hidden;
  background: var(--blk-surface-soft) center / cover no-repeat;
  display: flex;
  align-items: flex-end;
  text-decoration: none;
}

.hero-slide__overlay {
  width: 100%;
  padding: 1.1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  color: #fff;
  background: linear-gradient(180deg, transparent, rgb(0 0 0 / 0.7));
}

.hero-slide__overlay strong {
  font-size: 1.1rem;
}

.hero-slide__overlay span {
  font-size: 0.85rem;
  opacity: 0.9;
}

.hero-slide__cta {
  margin-top: 0.4rem;
  align-self: flex-start;
  font-style: normal;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.2);
}

@media (max-width: 860px) {
  .hero-split {
    grid-template-columns: 1fr;
  }

  .hero-split__media {
    order: -1;
  }
}
</style>
