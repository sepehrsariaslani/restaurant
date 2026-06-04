<template>
  <section ref="heroRef" class="site-hero" dir="rtl">
    <div
      class="hero-bg"
      :style="heroImage ? { backgroundImage: `url('${heroImage}')` } : {}"
    ></div>
    <div class="hero-overlay"></div>

    <div class="hero-content">
      <span class="hero-eyebrow" v-if="branding.tagline">{{ branding.tagline }}</span>
      <h1 class="hero-title">{{ title || branding.hero_title || branding.name }}</h1>
      <p class="hero-description" v-if="description">{{ description }}</p>
      <div class="hero-cta-row">
        <a class="hero-cta-primary" href="/menu">
          {{ cta || branding.primary_cta_label || 'مشاهده منو' }}
        </a>
        <a class="hero-cta-secondary" href="#content">
          بیشتر بدانید
        </a>
      </div>
    </div>

    <div class="hero-scroll-hint">
      <span></span>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

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
})

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
