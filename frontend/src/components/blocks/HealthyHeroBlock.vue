<template>
  <section class="healthy-hero blk" dir="rtl">
    <div class="healthy-hero__copy">
      <span class="healthy-hero__eyebrow">
        <span class="healthy-hero__eyebrow-dot" aria-hidden="true"></span>
        {{ eyebrow }}
      </span>
      <h1 class="healthy-hero__title">
        {{ title }}
        <span class="healthy-hero__title-accent">{{ highlight }}</span>
      </h1>
      <p class="healthy-hero__description">{{ description }}</p>

      <div class="healthy-hero__actions">
        <a class="healthy-hero__button" :href="ctaHref">
          {{ ctaLabel }}
          <ArrowLeft :size="18" aria-hidden="true" />
        </a>
        <a class="healthy-hero__text-link" href="/about-us">آشنایی با ویدرخت</a>
      </div>

      <div class="healthy-hero__values" aria-label="ویژگی‌های منو">
        <span><Leaf :size="17" aria-hidden="true" /> ترکیب‌های تازه</span>
        <i aria-hidden="true"></i>
        <span><Heart :size="17" aria-hidden="true" /> انتخاب آگاهانه</span>
      </div>
    </div>

    <div class="healthy-hero__visual-column">
      <div class="healthy-hero__visual" :class="{ 'is-open': expanded }">
        <span class="healthy-hero__visual-orbit healthy-hero__visual-orbit--one" aria-hidden="true"></span>
        <span class="healthy-hero__visual-orbit healthy-hero__visual-orbit--two" aria-hidden="true"></span>
        <span class="healthy-hero__visual-label">
          <Sparkles :size="15" aria-hidden="true" />
          انتخاب امروز
        </span>
        <div class="healthy-hero__plate" aria-hidden="true"></div>

        <div
          class="healthy-hero__sandwich"
          role="img"
          :aria-label="expanded ? 'ساندویچ باشگاهی بازشده و مواد تشکیل‌دهنده آن' : 'ساندویچ باشگاهی سالم با نان تست جو'"
        >
          <img
            v-for="layer in layers"
            :key="layer.key"
            class="healthy-hero__layer"
            :class="`healthy-hero__layer--${layer.key}`"
            :src="layer.src"
            alt=""
            draggable="false"
          />
        </div>

      </div>

      <div id="healthy-sandwich-ingredients" v-show="expanded" class="healthy-hero__ingredient-list" aria-live="polite">
        <div v-for="(ingredient, index) in visibleIngredients" :key="`${ingredient.title}-${index}`" class="healthy-hero__ingredient">
          <span class="healthy-hero__ingredient-index">{{ toPersianNumber(index + 1) }}</span>
          <span>
            <strong>{{ ingredient.title }}</strong>
            <small v-if="ingredient.description">{{ ingredient.description }}</small>
          </span>
        </div>
      </div>

      <button
        class="healthy-hero__reveal"
        type="button"
        :aria-expanded="expanded"
        aria-controls="healthy-sandwich-ingredients"
        @click="expanded = !expanded"
      >
        <span class="healthy-hero__reveal-icon" aria-hidden="true">
          <component :is="expanded ? X : Plus" :size="18" />
        </span>
        {{ expanded ? 'بستن ترکیبات' : 'ترکیبات ساندویچ را ببین' }}
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ArrowLeft, Heart, Leaf, Plus, Sparkles, X } from 'lucide-vue-next'
import '@/components/blocks/blocks.css'
import bottomBread from '@/assets/homev2/sandwich/bread_bottom.webp'
import greens from '@/assets/homev2/sandwich/greens.webp'
import chickenSauce from '@/assets/homev2/sandwich/chicken_sauce.webp'
import caramelizedOnion from '@/assets/homev2/sandwich/caramelized_onion.webp'
import sweetCorn from '@/assets/homev2/sandwich/sweet_corn.webp'
import topBread from '@/assets/homev2/sandwich/bread_top.webp'

const props = defineProps({
  eyebrow: { type: String, default: 'غذای سالم، با حال خوب' },
  title: { type: String, default: 'هر روز، یک انتخاب' },
  highlight: { type: String, default: 'خوش‌طعم‌تر از همیشه' },
  description: { type: String, default: 'طعم‌های تازه و ترکیب‌های متعادل، برای وقتی که می‌خواهی هم خوشمزه بخوری هم انتخاب خوبی داشته باشی.' },
  ctaLabel: { type: String, default: 'دیدن منوی سالم' },
  ctaHref: { type: String, default: '/menu' },
  ingredients: { type: Array, default: () => [] },
})

const expanded = ref(false)
const layers = [
  { key: 'bottom', src: bottomBread },
  { key: 'greens', src: greens },
  { key: 'chicken', src: chickenSauce },
  { key: 'onion', src: caramelizedOnion },
  { key: 'corn', src: sweetCorn },
  { key: 'top', src: topBread },
]

const fallbackIngredients = [
  { title: 'نان تست جو', description: 'دو برش برشته و خوش‌عطر' },
  { title: 'کاهوی تازه', description: 'ترد و سبز' },
  { title: 'سینه مرغ گریل‌شده', description: 'همراه سس سبک سبزیجات' },
  { title: 'پیاز کاراملی', description: 'با طعمی ملایم و شیرین' },
  { title: 'کمی ذرت شیرین', description: 'برای یک طعم دلنشین' },
]

const visibleIngredients = computed(() =>
  props.ingredients.filter((item) => String(item?.title || '').trim()).length
    ? props.ingredients.filter((item) => String(item?.title || '').trim())
    : fallbackIngredients,
)

function toPersianNumber(value) {
  return Number(value).toLocaleString('fa-IR')
}
</script>

<style scoped>
.healthy-hero {
  --healthy-green: var(--ds-color-action-primary, #236246);
  --healthy-green-deep: #173f31;
  --healthy-orange: var(--ds-color-action-accent, #e98b34);
  --healthy-cream: #f4f3e8;
  position: relative;
  isolation: isolate;
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(390px, 1.08fr);
  align-items: center;
  gap: clamp(1.25rem, 4vw, 4rem);
  width: min(1360px, calc(100% - 2rem));
  min-height: min(720px, calc(100svh - 96px));
  margin: 0 auto;
  padding: clamp(2rem, 6vw, 5.5rem);
  overflow: hidden;
  border-radius: var(--ds-radius-xl, 28px);
  color: #fffdf6;
  background:
    radial-gradient(ellipse at 76% 48%, rgb(134 166 105 / 0.26), transparent 43%),
    linear-gradient(130deg, #173f31 0%, #225c40 58%, #2d704b 100%);
  box-shadow: var(--ds-shadow-lg, 0 28px 70px rgb(24 58 41 / 0.2));
}

.healthy-hero::before,
.healthy-hero::after {
  position: absolute;
  z-index: -1;
  border: 1px solid rgb(255 255 255 / 0.09);
  border-radius: 50%;
  content: '';
  pointer-events: none;
}

.healthy-hero::before {
  width: 540px;
  aspect-ratio: 1;
  inset-inline-start: -205px;
  top: -285px;
}

.healthy-hero::after {
  width: 380px;
  aspect-ratio: 1;
  inset-inline-end: 11%;
  bottom: -295px;
}

.healthy-hero__copy {
  position: relative;
  z-index: 2;
  max-width: 560px;
}

.healthy-hero__eyebrow,
.healthy-hero__values,
.healthy-hero__values span,
.healthy-hero__actions,
.healthy-hero__button,
.healthy-hero__text-link,
.healthy-hero__visual-label,
.healthy-hero__reveal,
.healthy-hero__reveal-icon {
  display: inline-flex;
  align-items: center;
}

.healthy-hero__eyebrow {
  gap: 0.58rem;
  min-height: 2.4rem;
  padding: 0.35rem 0.9rem;
  border: 1px solid rgb(255 255 255 / 0.19);
  border-radius: var(--ds-radius-pill, 999px);
  background: rgb(255 255 255 / 0.08);
  color: #f5e8d2;
  font-size: 0.82rem;
  font-weight: 700;
}

.healthy-hero__eyebrow-dot {
  width: 0.48rem;
  height: 0.48rem;
  border-radius: 50%;
  background: var(--healthy-orange);
  box-shadow: 0 0 0 5px rgb(233 139 52 / 0.14);
}

.healthy-hero__title {
  display: flex;
  flex-direction: column;
  gap: 0.1em;
  margin: 1.4rem 0 1rem;
  font-size: clamp(2.55rem, 5.5vw, 5.3rem);
  font-weight: 900;
  line-height: 1.16;
  letter-spacing: -0.055em;
  text-wrap: balance;
}

.healthy-hero__title-accent {
  color: #f2a451;
}

.healthy-hero__description {
  max-width: 46ch;
  margin: 0;
  color: rgb(255 253 246 / 0.78);
  font-size: clamp(1rem, 1.5vw, 1.16rem);
  line-height: 1.95;
}

.healthy-hero__actions {
  flex-wrap: wrap;
  gap: 1.25rem;
  margin-top: 2rem;
}

.healthy-hero__button {
  justify-content: center;
  gap: 0.65rem;
  min-height: 3.45rem;
  padding: 0.75rem 1.35rem;
  border: 1px solid #f5a24b;
  border-radius: var(--ds-radius-pill, 999px);
  background: var(--healthy-orange);
  color: #23382c;
  font-size: 0.94rem;
  font-weight: 900;
  text-decoration: none;
  box-shadow: 0 12px 30px rgb(10 35 24 / 0.22);
  transition: transform var(--ds-motion-fast, 160ms) var(--ds-motion-ease, ease), box-shadow var(--ds-motion-fast, 160ms) ease;
}

.healthy-hero__button:hover {
  transform: translateY(-2px);
  box-shadow: 0 17px 34px rgb(10 35 24 / 0.26);
}

.healthy-hero__text-link {
  min-height: 2.75rem;
  color: rgb(255 253 246 / 0.88);
  font-size: 0.88rem;
  font-weight: 700;
  text-decoration: none;
  text-underline-offset: 5px;
}

.healthy-hero__text-link:hover {
  text-decoration: underline;
}

.healthy-hero__values {
  flex-wrap: wrap;
  gap: 0.85rem 1.1rem;
  margin-top: 2.5rem;
  color: rgb(255 253 246 / 0.74);
  font-size: 0.79rem;
  font-weight: 600;
}

.healthy-hero__values span {
  gap: 0.42rem;
}

.healthy-hero__values :deep(svg) {
  color: #f2a451;
}

.healthy-hero__values i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgb(255 255 255 / 0.4);
}

.healthy-hero__visual-column {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
}

.healthy-hero__visual {
  position: relative;
  display: grid;
  width: min(100%, 610px);
  min-height: clamp(360px, 43vw, 550px);
  place-items: center;
  isolation: isolate;
}

.healthy-hero__visual-orbit {
  position: absolute;
  z-index: -1;
  border: 1px solid rgb(255 255 255 / 0.17);
  border-radius: 50%;
  pointer-events: none;
}

.healthy-hero__visual-orbit--one {
  width: 83%;
  aspect-ratio: 1;
}

.healthy-hero__visual-orbit--two {
  width: 62%;
  aspect-ratio: 1;
  border-style: dashed;
  opacity: 0.45;
  transform: rotate(-18deg);
}

.healthy-hero__visual-label {
  position: absolute;
  z-index: 3;
  top: 8%;
  inset-inline-start: 8%;
  gap: 0.38rem;
  padding: 0.5rem 0.8rem;
  border: 1px solid rgb(255 255 255 / 0.33);
  border-radius: var(--ds-radius-pill, 999px);
  background: rgb(255 255 255 / 0.15);
  color: #fff4df;
  font-size: 0.76rem;
  font-weight: 800;
  backdrop-filter: blur(12px);
}

.healthy-hero__visual-label :deep(svg) {
  color: #ffc173;
}

.healthy-hero__plate {
  position: absolute;
  bottom: 11%;
  width: 82%;
  height: 20%;
  border: 1px solid rgb(255 255 255 / 0.65);
  border-radius: 50%;
  background: linear-gradient(180deg, #fffdf2 0%, #e9e6d8 100%);
  box-shadow: 0 28px 50px rgb(12 42 28 / 0.35), inset 0 -9px 15px rgb(69 78 55 / 0.1);
  transform: rotate(-7deg);
  transition: transform 700ms var(--ds-motion-ease, cubic-bezier(0.22, 1, 0.36, 1));
}

.healthy-hero__sandwich {
  position: relative;
  width: min(100%, 560px);
  aspect-ratio: 900 / 760;
  filter: drop-shadow(0 23px 14px rgb(13 38 26 / 0.22));
  transform: translateY(-3%);
  transition: filter 700ms ease;
}

.healthy-hero__layer {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  user-select: none;
  transition: transform 800ms var(--ds-motion-ease, cubic-bezier(0.22, 1, 0.36, 1));
  will-change: transform;
}

.healthy-hero__layer--bottom { z-index: 1; }
.healthy-hero__layer--greens { z-index: 2; }
.healthy-hero__layer--chicken { z-index: 3; }
.healthy-hero__layer--onion { z-index: 4; }
.healthy-hero__layer--corn { z-index: 5; }
.healthy-hero__layer--top { z-index: 6; }

.is-open .healthy-hero__layer--bottom { transform: translateY(16%); }
.is-open .healthy-hero__layer--greens { transform: translateY(8%); }
.is-open .healthy-hero__layer--chicken { transform: translateY(2%); }
.is-open .healthy-hero__layer--onion { transform: translateY(-4%); }
.is-open .healthy-hero__layer--corn { transform: translateY(-8%); }
.is-open .healthy-hero__layer--top { transform: translateY(-17%); }
.is-open .healthy-hero__sandwich { filter: drop-shadow(0 30px 16px rgb(13 38 26 / 0.25)); }
.is-open .healthy-hero__plate { transform: rotate(-7deg) scale(1.04); }

.healthy-hero__ingredient-list {
  display: flex;
  width: min(100%, 460px);
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.45rem;
  margin-top: -0.6rem;
  animation: healthy-ingredients-in 360ms both;
}

.healthy-hero__ingredient {
  display: inline-flex;
  align-items: center;
  gap: 0.48rem;
  min-height: 2.35rem;
  padding: 0.4rem 0.72rem;
  border: 1px solid rgb(255 255 255 / 0.68);
  border-radius: var(--ds-radius-pill, 999px);
  background: #fffdf6;
  color: #294838;
  box-shadow: var(--ds-shadow-sm, 0 8px 24px rgb(20 44 30 / 0.12));
  font-size: 0.74rem;
}

.healthy-hero__ingredient-index {
  display: grid;
  width: 1.42rem;
  height: 1.42rem;
  place-items: center;
  border-radius: 50%;
  background: #eaf0df;
  color: var(--healthy-green);
  font-size: 0.68rem;
  font-weight: 900;
}

.healthy-hero__ingredient strong {
  display: block;
  font-size: 0.74rem;
  font-weight: 800;
}

.healthy-hero__ingredient small {
  display: block;
  margin-top: 0.06rem;
  color: #768276;
  font-size: 0.65rem;
}

.healthy-hero__reveal {
  position: relative;
  z-index: 9;
  justify-content: center;
  gap: 0.58rem;
  min-height: 2.9rem;
  margin-top: -0.35rem;
  padding: 0.55rem 1rem;
  border: 1px solid rgb(255 255 255 / 0.28);
  border-radius: var(--ds-radius-pill, 999px);
  background: rgb(20 56 39 / 0.54);
  color: #fffdf6;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 800;
  cursor: pointer;
  transition: background var(--ds-motion-fast, 160ms) ease, transform var(--ds-motion-fast, 160ms) ease;
}

.healthy-hero__reveal:hover {
  transform: translateY(-2px);
  background: rgb(20 56 39 / 0.78);
}

.healthy-hero__reveal-icon {
  width: 1.65rem;
  height: 1.65rem;
  justify-content: center;
  border-radius: 50%;
  background: var(--healthy-orange);
  color: #24412f;
}

.healthy-hero__sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@keyframes healthy-ingredients-in {
  from { opacity: 0; transform: translateY(-0.5rem); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 900px) {
  .healthy-hero {
    grid-template-columns: 1fr;
    gap: 1rem;
    min-height: auto;
    padding: clamp(1.6rem, 7vw, 3rem);
    text-align: center;
  }

  .healthy-hero__copy { max-width: 680px; margin-inline: auto; }
  .healthy-hero__eyebrow,
  .healthy-hero__actions,
  .healthy-hero__values { justify-content: center; }
  .healthy-hero__title { font-size: clamp(2.4rem, 8vw, 4rem); }
  .healthy-hero__description { margin-inline: auto; }
  .healthy-hero__visual { width: min(100%, 520px); min-height: clamp(310px, 73vw, 450px); }
  .healthy-hero__visual-label { top: 6%; inset-inline-start: 4%; }
  .healthy-hero__reveal { margin-top: -0.6rem; }
}

@media (max-width: 520px) {
  .healthy-hero { width: min(100% - 1rem, 460px); border-radius: 22px; }
  .healthy-hero__title { margin-top: 1.1rem; font-size: clamp(2.15rem, 10vw, 3rem); }
  .healthy-hero__actions { flex-direction: column; gap: 0.45rem; }
  .healthy-hero__button { width: 100%; }
  .healthy-hero__values { margin-top: 1.5rem; font-size: 0.72rem; }
  .healthy-hero__visual { min-height: clamp(270px, 75vw, 360px); }
  .healthy-hero__ingredient-list { width: 100%; gap: 0.3rem; margin-top: -0.2rem; }
  .healthy-hero__ingredient { min-height: 2rem; padding: 0.32rem 0.5rem; }
  .healthy-hero__ingredient strong { font-size: 0.66rem; }
  .healthy-hero__ingredient small { font-size: 0.58rem; }
}

@media (prefers-reduced-motion: reduce) {
  .healthy-hero *,
  .healthy-hero *::before,
  .healthy-hero *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
