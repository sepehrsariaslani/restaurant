<template>
  <section class="blk banner" dir="rtl">
    <div
      class="banner-box"
      :class="`banner-box--${variant}`"
      :style="variant === 'image' && image ? { backgroundImage: `linear-gradient(90deg, rgb(0 0 0 / 0.55), rgb(0 0 0 / 0.2)), url('${image}')` } : {}"
    >
      <div class="banner-copy">
        <h2 class="banner-title">{{ title }}</h2>
        <p v-if="description" class="banner-desc">{{ description }}</p>
      </div>
      <a class="blk-btn banner-cta" :href="ctaHref">{{ ctaLabel }}</a>
    </div>
  </section>
</template>

<script setup>
import '@/components/blocks/blocks.css'

defineProps({
  variant: { type: String, default: 'solid' },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  image: { type: String, default: '' },
  ctaLabel: { type: String, default: '' },
  ctaHref: { type: String, default: '/menu' },
})
</script>

<style scoped>
.banner-box {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1.25rem;
  padding: clamp(1.5rem, 4vw, 2.5rem);
  border-radius: var(--blk-radius);
}

.banner-box--solid {
  background: var(--blk-accent);
  color: #fff;
}

.banner-box--image {
  background: var(--blk-ink) center / cover no-repeat;
  color: #fff;
  min-height: 200px;
}

.banner-title {
  margin: 0;
  font-size: clamp(1.4rem, 3.5vw, 2.1rem);
  font-weight: 800;
  letter-spacing: -0.01em;
}

.banner-desc {
  margin: 0.5rem 0 0;
  font-size: 0.98rem;
  line-height: 1.75;
  opacity: 0.92;
  max-width: 52ch;
}

.banner-cta {
  background: #fff;
  color: var(--blk-ink);
  flex: 0 0 auto;
}

.banner-cta:hover {
  transform: translateY(-1px);
}
</style>
