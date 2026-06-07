<template>
  <section ref="heroRef" class="site-hero" dir="rtl">
    <div
      class="hero-bg"
      :style="heroImage ? { backgroundImage: `url('${heroImage}')` } : {}"
    ></div>
    <div class="hero-overlay"></div>

    <div class="hero-particles" aria-hidden="true">
      <span v-for="n in 6" :key="n" class="particle" :class="`p-${n}`"></span>
    </div>

    <div class="hero-content">
      <span class="hero-eyebrow" v-if="branding.tagline">{{ branding.tagline }}</span>

      <div class="hero-title-wrap">
        <h1 class="hero-title">{{ title || branding.hero_title || branding.name }}</h1>
        <div class="hero-title-accent" aria-hidden="true"></div>
      </div>

      <p class="hero-description" v-if="description || branding.hero_subtitle">
        {{ description || branding.hero_subtitle }}
      </p>

      <div class="hero-cta-row">
        <a class="hero-cta-primary" href="/menu">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <path d="M16 10a4 4 0 0 1-8 0"/>
          </svg>
          {{ cta || branding.primary_cta_label || 'مشاهده منو' }}
        </a>
        <a class="hero-cta-secondary" href="#content">
          بیشتر بدانید
        </a>
      </div>

      <div class="hero-category-chips" v-if="resolvedCategories.length">
        <span class="chips-label">دسته‌بندی‌ها:</span>
        <a
          v-for="cat in resolvedCategories"
          :key="cat.slug"
          :href="`/menu?category=${cat.slug}`"
          class="hero-chip"
        >
          {{ cat.title }}
        </a>
        <a href="/menu" class="hero-chip hero-chip--more">همه</a>
      </div>
    </div>

    <div class="hero-food-icons" aria-hidden="true">
      <span class="fi fi-1">🍕</span>
      <span class="fi fi-2">🍔</span>
      <span class="fi fi-3">🍜</span>
      <span class="fi fi-4">☕</span>
      <span class="fi fi-5">🥗</span>
      <span class="fi fi-6">🍰</span>
    </div>

    <div class="hero-scroll-hint">
      <span></span>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  branding: {
    type: Object,
    default: () => ({}),
  },
  title: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
  cta: {
    type: String,
    default: '',
  },
  heroImage: {
    type: String,
    default: '',
  },
  categories: {
    type: Array,
    default: () => [],
  },
})

const resolvedCategories = computed(() =>
  (props.categories || [])
    .filter((c) => c.slug)
    .slice(0, 6)
    .map((c) => ({ slug: c.slug, title: c.title || c.slug })),
)

const emit = defineEmits(['visibility-change'])

const heroRef = ref(null)
let observer = null

onMounted(() => {
  if (!heroRef.value) return
  observer = new IntersectionObserver(
    ([entry]) => {
      emit('visibility-change', entry.isIntersecting)
    },
    { threshold: 0.15 },
  )
  observer.observe(heroRef.value)
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
})
</script>

<style scoped>
.site-hero {
  position: relative;
  min-height: 100svh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  isolation: isolate;
}

.hero-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background-color: var(--palette-deep-sapphire, #6F4A31);
  background-size: cover;
  background-position: center;
  transform: scale(1.04);
  transition: transform 0.6s ease;
}

.site-hero:hover .hero-bg {
  transform: scale(1.0);
}

.hero-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(
    160deg,
    rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.82) 0%,
    rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.60) 50%,
    rgb(0 0 0 / 0.72) 100%
  );
}

.hero-content {
  position: relative;
  z-index: 2;
  text-align: center;
  max-width: 780px;
  width: calc(100% - 3rem);
  margin: 0 auto;
  padding: 3rem 1.5rem 5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.1rem;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 1rem;
  border-radius: 999px;
  border: 1px solid rgb(255 255 255 / 0.35);
  background: rgb(255 255 255 / 0.12);
  backdrop-filter: blur(6px);
  color: rgb(255 255 255 / 0.9);
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.hero-title {
  margin: 0;
  font-size: clamp(2.2rem, 6vw, 4.5rem);
  font-weight: 900;
  line-height: 1.15;
  color: #fff;
  text-shadow: 0 4px 28px rgb(0 0 0 / 0.3);
  letter-spacing: -0.02em;
}

.hero-description {
  margin: 0;
  font-size: clamp(1rem, 2vw, 1.25rem);
  line-height: 1.7;
  color: rgb(255 255 255 / 0.82);
  max-width: 560px;
  text-shadow: 0 2px 10px rgb(0 0 0 / 0.25);
}

/* Particles */
.hero-particles {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

.particle {
  position: absolute;
  border-radius: 50%;
  background: rgb(255 255 255 / 0.06);
  animation: float-particle 8s ease-in-out infinite;
}

.p-1 { width: 180px; height: 180px; top: 10%; right: -40px; animation-delay: 0s; }
.p-2 { width: 80px; height: 80px; top: 55%; left: 5%; animation-delay: 1.2s; }
.p-3 { width: 120px; height: 120px; bottom: 15%; right: 20%; animation-delay: 2.4s; }
.p-4 { width: 50px; height: 50px; top: 30%; left: 25%; animation-delay: 0.7s; }
.p-5 { width: 200px; height: 200px; bottom: -60px; left: -40px; animation-delay: 1.8s; }
.p-6 { width: 60px; height: 60px; top: 70%; right: 10%; animation-delay: 3.1s; }

@keyframes float-particle {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-20px) scale(1.05); }
}

/* Floating food icons */
.hero-food-icons {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  overflow: hidden;
}

.fi {
  position: absolute;
  font-size: 2.2rem;
  opacity: 0.12;
  animation: float-fi 6s ease-in-out infinite;
  filter: blur(0.5px);
}

.fi-1 { top: 8%; left: 8%; animation-delay: 0s; font-size: 2.8rem; }
.fi-2 { top: 20%; right: 6%; animation-delay: 1s; }
.fi-3 { bottom: 25%; right: 3%; animation-delay: 2s; font-size: 2rem; }
.fi-4 { bottom: 15%; left: 6%; animation-delay: 0.5s; }
.fi-5 { top: 55%; left: 3%; animation-delay: 2.5s; font-size: 1.8rem; }
.fi-6 { top: 12%; right: 22%; animation-delay: 1.5s; font-size: 2rem; }

@keyframes float-fi {
  0%, 100% { transform: translateY(0) rotate(-5deg); }
  50% { transform: translateY(-14px) rotate(5deg); }
}

/* Title wrap */
.hero-title-wrap {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
}

.hero-title-accent {
  width: 60px;
  height: 3px;
  border-radius: 999px;
  background: var(--palette-deep-saffron, #C98D42);
  margin-top: 0.6rem;
  opacity: 0.85;
}

/* Category chips */
.hero-category-chips {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 0.4rem;
}

.chips-label {
  font-size: 0.72rem;
  color: rgb(255 255 255 / 0.55);
  white-space: nowrap;
}

.hero-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.1);
  border: 1px solid rgb(255 255 255 / 0.2);
  color: rgb(255 255 255 / 0.88);
  font-size: 0.76rem;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.15s, border-color 0.15s, transform 0.15s;
  backdrop-filter: blur(4px);
}

.hero-chip:hover {
  background: rgb(255 255 255 / 0.2);
  border-color: rgb(255 255 255 / 0.4);
  transform: translateY(-1px);
}

.hero-chip--more {
  background: rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.28);
  border-color: rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.5);
  color: #f0c878;
}

.hero-cta-row {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 0.6rem;
}

.hero-cta-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.8rem 2rem;
  border-radius: 999px;
  background: var(--palette-deep-saffron, #C98D42);
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  text-decoration: none;
  box-shadow: 0 4px 20px rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.5);
  transition: transform 0.18s, box-shadow 0.18s, background 0.18s;
}

.hero-cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgb(var(--palette-deep-saffron-rgb, 201 141 66) / 0.6);
}

.hero-cta-secondary {
  display: inline-flex;
  align-items: center;
  padding: 0.8rem 1.6rem;
  border-radius: 999px;
  border: 1.5px solid rgb(255 255 255 / 0.5);
  color: #fff;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  backdrop-filter: blur(6px);
  background: rgb(255 255 255 / 0.1);
  transition: background 0.18s, border-color 0.18s;
}

.hero-cta-secondary:hover {
  background: rgb(255 255 255 / 0.2);
  border-color: rgb(255 255 255 / 0.7);
}

.hero-scroll-hint {
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
}

.hero-scroll-hint span {
  display: block;
  width: 1.5rem;
  height: 2.5rem;
  border: 2px solid rgb(255 255 255 / 0.5);
  border-radius: 999px;
  position: relative;
}

.hero-scroll-hint span::after {
  content: '';
  position: absolute;
  top: 0.35rem;
  left: 50%;
  transform: translateX(-50%);
  width: 0.3rem;
  height: 0.7rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.8);
  animation: scroll-dot 1.6s ease-in-out infinite;
}

@keyframes scroll-dot {
  0% { opacity: 1; top: 0.35rem; }
  100% { opacity: 0; top: 1.4rem; }
}

@media (max-width: 640px) {
  .hero-content {
    gap: 0.9rem;
    padding: 2rem 1rem 4rem;
  }

  .hero-cta-row {
    flex-direction: column;
    width: 100%;
  }

  .hero-cta-primary,
  .hero-cta-secondary {
    width: 100%;
    justify-content: center;
  }
}
</style>
