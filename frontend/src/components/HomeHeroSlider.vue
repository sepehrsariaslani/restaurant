<template>
  <section class="hero-slider glass-card" dir="rtl" v-if="resolvedSlides.length">
    <div class="slider-track" :style="{ transform: `translateX(-${activeIndex * 100}%)` }">
      <article
        class="hero-slide"
        v-for="slide in resolvedSlides"
        :key="slide.key"
      >
        <img class="slide-image" :src="slide.image" :alt="slide.title" />
        <div class="slide-overlay"></div>
        <div class="slide-content">
          <small class="eyebrow">تازه و خوشمزه</small>
          <h2>{{ slide.title }}</h2>
          <p>{{ slide.subtitle }}</p>
          <a class="slide-cta" :href="slide.url">{{ slide.ctaLabel }}</a>
        </div>
      </article>
    </div>

    <button class="nav-btn nav-next" type="button" @click="nextSlide" aria-label="اسلاید بعدی">‹</button>
    <button class="nav-btn nav-prev" type="button" @click="prevSlide" aria-label="اسلاید قبلی">›</button>

    <div class="dots" role="tablist" aria-label="اسلایدها">
      <button
        v-for="(slide, idx) in resolvedSlides"
        :key="`dot-${slide.key}`"
        type="button"
        class="dot"
        :class="{ active: idx === activeIndex }"
        :aria-label="`اسلاید ${idx + 1}`"
        @click="goToSlide(idx)"
      ></button>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  slides: {
    type: Array,
    default: () => [],
  },
  fallbackItems: {
    type: Array,
    default: () => [],
  },
})

const activeIndex = ref(0)
let autoplayTimer = null

const resolvedSlides = computed(() => {
  if (Array.isArray(props.slides) && props.slides.length) {
    return props.slides.map((slide, idx) => ({
      key: slide.name || `hero-${idx}`,
      title: slide.title || 'محصول ویژه',
      subtitle: slide.subtitle || 'با مواد تازه و امکان شخصی سازی کامل',
      image:
        slide.image ||
        'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=1400&auto=format&fit=crop&q=60',
      url: slide.item_slug ? `/item/${slide.item_slug}` : slide.cta_url || '/menu',
      ctaLabel: slide.cta_label || 'مشاهده محصول',
    }))
  }

  return (props.fallbackItems || []).slice(0, 3).map((item, idx) => ({
    key: item.slug || `featured-${idx}`,
    title: item.title || 'محصول ویژه',
    subtitle: item.short_desc || 'سفارش سریع با جزئیات کامل',
    image:
      item.image ||
      'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1400&auto=format&fit=crop&q=60',
    url: item.slug ? `/item/${item.slug}` : '/menu',
    ctaLabel: 'مشاهده محصول',
  }))
})

function goToSlide(index) {
  if (!resolvedSlides.value.length) {
    return
  }
  const maxIndex = resolvedSlides.value.length - 1
  activeIndex.value = Math.max(0, Math.min(index, maxIndex))
}

function nextSlide() {
  if (!resolvedSlides.value.length) {
    return
  }
  activeIndex.value = (activeIndex.value + 1) % resolvedSlides.value.length
}

function prevSlide() {
  if (!resolvedSlides.value.length) {
    return
  }
  activeIndex.value = (activeIndex.value - 1 + resolvedSlides.value.length) % resolvedSlides.value.length
}

function startAutoplay() {
  stopAutoplay()
  if (resolvedSlides.value.length <= 1) {
    return
  }
  autoplayTimer = window.setInterval(nextSlide, 5000)
}

function stopAutoplay() {
  if (!autoplayTimer) {
    return
  }
  window.clearInterval(autoplayTimer)
  autoplayTimer = null
}

watch(
  () => resolvedSlides.value.length,
  (count) => {
    if (activeIndex.value >= count) {
      activeIndex.value = 0
    }
    startAutoplay()
  },
)

onMounted(() => {
  startAutoplay()
})

onBeforeUnmount(() => {
  stopAutoplay()
})
</script>

<style scoped>
.hero-slider {
  position: relative;
  overflow: hidden;
  border-radius: 30px;
  padding: 0;
  margin-bottom: 1rem;
}

.slider-track {
  display: flex;
  direction: ltr;
  width: 100%;
  transition: transform 0.45s ease;
}

.hero-slide {
  min-width: 100%;
  height: 470px;
  position: relative;
  display: grid;
  align-items: end;
}

.slide-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.slide-overlay {
  position: absolute;
  inset: 0;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.20);
}

.slide-content {
  position: relative;
  z-index: 2;
  color: #fff;
  padding: 1.15rem 1.15rem 1.4rem;
  width: min(560px, 100%);
}

.eyebrow {
  display: inline-block;
  margin-bottom: 0.4rem;
  color: rgb(var(--palette-june-bud-rgb) / 1);
  font-size: 0.78rem;
}

.slide-content h2 {
  margin: 0;
  font-size: 1.95rem;
  line-height: 1.2;
}

.slide-content p {
  margin: 0.55rem 0 0.8rem;
  color: rgb(var(--palette-eggshell-rgb) / 0.95);
  line-height: 1.7;
  font-size: 0.9rem;
}

.slide-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0.55rem 1rem;
  background: rgb(255 255 255 / 0.9);
  color: var(--ink-900, #2f1f0f);
  font-size: 0.84rem;
  font-weight: 700;
}

.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 38px;
  height: 38px;
  border: 0;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.72);
  color: var(--ink-900, #2f1f0f);
  font-size: 1.4rem;
  line-height: 1;
  cursor: pointer;
  z-index: 3;
}

.nav-next {
  left: 0.65rem;
}

.nav-prev {
  right: 0.65rem;
}

.dots {
  position: absolute;
  bottom: 0.75rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.38rem;
  z-index: 3;
}

.dot {
  width: 8px;
  height: 8px;
  border: 0;
  border-radius: 999px;
  background: rgb(var(--palette-eggshell-rgb) / 0.45);
  cursor: pointer;
}

.dot.active {
  width: 20px;
  background: var(--accent-gold);
}

@media (max-width: 720px) {
  .hero-slide {
    height: 500px;
  }

  .slide-content h2 {
    font-size: 1.35rem;
  }
}
</style>
