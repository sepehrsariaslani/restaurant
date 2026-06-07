<template>
  <div class="feature-card" :class="{ 'feature-card--image': hasBgImage }">
    <div v-if="hasBgImage" class="fc-bg">
      <img :src="bgImage" :alt="title" class="fc-bg-img" loading="lazy" />
      <div class="fc-bg-overlay"></div>
    </div>
    <div class="fc-content">
      <div class="feature-icon-wrap">
        <span class="feature-icon">{{ icon }}</span>
      </div>
      <h4 class="feature-title">{{ title }}</h4>
      <p class="feature-desc">{{ description }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  bgImage: { type: String, default: '' },
})

const hasBgImage = computed(() => Boolean(String(props.bgImage || '').trim()))
</script>

<style scoped>
.feature-card {
  text-align: center;
  padding: 1.6rem 1.2rem;
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 0.3s ease;
  border-radius: var(--radius-lg, 18px);
  position: relative;
  overflow: hidden;
  background: var(--glass-bg, rgba(255,255,255,0.7));
  border: 1px solid var(--glass-border, rgba(111,74,49,0.14));
  box-shadow: var(--shadow-soft);
}

.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-deep);
}

/* ─── Image variant ─── */
.feature-card--image {
  background: transparent;
  border-color: transparent;
  min-height: 240px;
  display: flex;
  align-items: flex-end;
}

.fc-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.fc-bg-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
}

.fc-bg-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(20, 12, 8, 0.88) 0%, rgba(20, 12, 8, 0.3) 50%, rgba(20, 12, 8, 0.1) 100%);
}

.fc-content {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: 0.2rem;
}

.feature-card--image .fc-content {
  padding: 0.5rem;
  text-align: right;
}

.feature-icon-wrap {
  width: 3.4rem;
  height: 3.4rem;
  margin: 0 auto 1rem;
  border-radius: 16px;
  background: var(--accent-green20, rgba(111,74,49,0.12));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.feature-card--image .feature-icon-wrap {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(6px);
  margin: 0 0 0.7rem;
}

.feature-icon {
  font-size: 1.6rem;
}

.feature-title {
  margin: 0 0 0.4rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink-900, #1c1411);
}

.feature-card--image .feature-title {
  color: #fff;
  font-size: 1.05rem;
}

.feature-desc {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.7;
  color: var(--text-muted, #846b58);
}

.feature-card--image .feature-desc {
  color: rgba(255, 255, 255, 0.75);
}
</style>
