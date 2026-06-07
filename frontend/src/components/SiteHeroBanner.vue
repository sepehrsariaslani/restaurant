<template>
  <section class="site-hero-banner" dir="rtl">
    <div
      class="banner-bg"
      :style="heroImage ? { backgroundImage: `url('${heroImage}')` } : {}"
    ></div>
    <div class="banner-overlay"></div>

    <div class="banner-inner">
      <div class="banner-text">
        <span class="banner-eyebrow" v-if="branding.tagline">{{ branding.tagline }}</span>
        <h2 class="banner-title">{{ title || branding.hero_title || branding.name }}</h2>
        <p class="banner-desc" v-if="description">{{ description }}</p>
        <div class="banner-actions">
          <a class="banner-cta-primary" href="/menu">
            {{ cta || branding.primary_cta_label || 'مشاهده منو' }}
          </a>
          <a class="banner-cta-secondary" href="#content">
            بیشتر بدانید
          </a>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
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
</script>

<style scoped>
.site-hero-banner {
  position: relative;
  width: 100%;
  min-height: 300px;
  display: flex;
  align-items: center;
  direction: rtl;
  overflow: hidden;
}

.banner-bg {
  position: absolute;
  inset: 0;
  background-color: #1c1411;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  transform: scale(1.03);
  transition: transform 6s ease;
}

.banner-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgb(28 20 17 / 0.88) 0%, rgb(28 20 17 / 0.55) 100%);
}

.banner-inner {
  position: relative;
  z-index: 2;
  width: min(1200px, calc(100% - 2.5rem));
  margin: 0 auto;
  padding: 3rem 0;
}

.banner-text {
  max-width: 580px;
  display: grid;
  gap: 0.9rem;
}

.banner-eyebrow {
  display: inline-flex;
  width: max-content;
  border-radius: 999px;
  padding: 0.28rem 0.9rem;
  background: rgb(201 141 66 / 0.22);
  border: 1px solid rgb(201 141 66 / 0.45);
  font-size: 0.78rem;
  font-weight: 700;
  color: #c98d42;
  letter-spacing: 0.02em;
}

.banner-title {
  margin: 0;
  font-size: clamp(1.4rem, 3.2vw, 2.1rem);
  font-weight: 900;
  color: #fff;
  line-height: 1.28;
}

.banner-desc {
  margin: 0;
  font-size: 0.92rem;
  color: rgb(255 255 255 / 0.78);
  line-height: 1.65;
}

.banner-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-top: 0.35rem;
}

.banner-cta-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.65rem 1.4rem;
  border-radius: 999px;
  background: #c98d42;
  color: #fff;
  font-size: 0.88rem;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.18s, transform 0.15s;
}

.banner-cta-primary:hover {
  background: #b87c38;
  transform: translateY(-1px);
}

.banner-cta-secondary {
  display: inline-flex;
  align-items: center;
  padding: 0.65rem 1.1rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.12);
  border: 1px solid rgb(255 255 255 / 0.25);
  color: rgb(255 255 255 / 0.88);
  font-size: 0.88rem;
  text-decoration: none;
  transition: background 0.18s;
}

.banner-cta-secondary:hover {
  background: rgb(255 255 255 / 0.2);
}

@media (max-width: 640px) {
  .site-hero-banner {
    min-height: 240px;
  }

  .banner-inner {
    padding: 2rem 0;
  }
}
</style>
