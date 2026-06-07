<template>
  <div class="hero-header" :class="{ 'hero-header--preview': preview }" dir="rtl">
    <div
      class="hero-header__bg"
      :style="bgStyle"
    >
      <div class="hero-header__overlay"></div>
    </div>

    <header class="hero-header__bar">
      <div class="hero-header__bar-inner">
        <a href="/" class="hero-brand">
          <span class="hero-brand-dot"></span>
          <div class="hero-brand-copy">
            <strong>{{ branding.name }}</strong>
            <small>{{ branding.tagline }}</small>
          </div>
        </a>

        <nav class="hero-desktop-nav" aria-label="ناوبری">
          <a
            v-for="link in links"
            :key="link.url"
            :href="link.url"
            class="hero-nav-link"
          >
            {{ link.label }}
            <span class="hero-count-pill" v-if="link.kind === 'cart' && cartCount > 0">{{ cartCount }}</span>
          </a>
        </nav>

        <div class="hero-header__actions">
          <a :href="managementLoginUrl" class="hero-mgmt-pill" aria-label="ورود مدیریت">
            ورود مدیریت
          </a>
          <a href="/cart" class="hero-cart-pill" aria-label="سبد سفارش">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round">
              <circle cx="8" cy="20" r="1" /><circle cx="18" cy="20" r="1" />
              <path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.5L22 7H7" />
            </svg>
            <span v-if="cartCount > 0">{{ cartCount }}</span>
          </a>
          <button class="hero-hamburger" :class="{ open: mobileOpen }" type="button" @click="mobileOpen = !mobileOpen" aria-label="منو">
            <span></span><span></span><span></span>
          </button>
        </div>
      </div>
    </header>

    <div class="hero-header__content">
      <div class="hero-header__text">
        <p class="hero-eyebrow">رستوران آنلاین</p>
        <h1 class="hero-title">{{ branding.hero_title || branding.name }}</h1>
        <p class="hero-subtitle">{{ branding.hero_subtitle || branding.tagline }}</p>
        <div class="hero-cta-row">
          <a class="hero-cta-btn" href="/menu">{{ branding.primary_cta_label || 'مشاهده منو' }}</a>
          <a class="hero-cta-outline" href="/cart">سبد سفارش</a>
        </div>
      </div>
    </div>

    <div class="hero-scroll-hint">
      <span></span>
    </div>

    <div class="mobile-overlay" :class="{ visible: mobileOpen }" @click="mobileOpen = false"></div>
    <aside class="mobile-sheet" :class="{ open: mobileOpen }" dir="rtl">
      <div class="sheet-head">
        <strong>{{ branding.name }}</strong>
        <button class="sheet-close" type="button" @click="mobileOpen = false">×</button>
      </div>
      <nav class="sheet-links">
        <a v-for="link in links" :key="`m-${link.url}`" :href="link.url" @click="mobileOpen = false">
          <span>{{ link.label }}</span>
          <span class="hero-count-pill" v-if="link.kind === 'cart' && cartCount > 0">{{ cartCount }}</span>
        </a>
      </nav>
      <a class="sheet-management-btn" :href="managementLoginUrl" @click="mobileOpen = false">ورود به مدیریت</a>
    </aside>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  branding: { type: Object, default: () => ({}) },
  cartCount: { type: Number, default: 0 },
  hasLastOrder: { type: Boolean, default: false },
  lastOrderUrl: { type: String, default: '/menu' },
  page: { type: String, default: 'landing' },
  preview: { type: Boolean, default: false },
})

const mobileOpen = ref(false)
const managementLoginUrl = '/management/login?redirect_to=%2Fmanagement'

const bgStyle = computed(() => {
  const img = String(props.branding?.hero_image || '').trim()
  if (img) {
    return { backgroundImage: `url('${img}')` }
  }
  return {}
})

const links = computed(() => {
  const base = [
    { key: 'landing', label: 'خانه', url: '/' },
    { key: 'menu', label: 'منو', url: '/menu' },
    { key: 'about-us', label: 'درباره ما', url: '/about-us' },
    { key: 'faq', label: 'سوالات', url: '/faq' },
    { key: 'cart', label: 'سبد سفارش', url: '/cart', kind: 'cart' },
  ]
  if (props.hasLastOrder && props.lastOrderUrl) {
    base.push({ key: 'order-success', label: 'پیگیری سفارش', url: props.lastOrderUrl })
  }
  return base
})
</script>

<style scoped>
.hero-header {
  position: relative;
  width: 100%;
  min-height: 100svh;
  display: flex;
  flex-direction: column;
  direction: rtl;
  overflow: hidden;
}

.hero-header--preview {
  min-height: 260px;
  max-height: 320px;
}

.hero-header__bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #1c1411 0%, #3d2510 40%, #5a3a20 100%);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.hero-header__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgb(0 0 0 / 0.55) 0%,
    rgb(0 0 0 / 0.3) 40%,
    rgb(0 0 0 / 0.65) 100%
  );
}

.hero-header__bar {
  position: relative;
  z-index: 10;
  padding: 1rem 1.2rem 0;
}

.hero-header__bar-inner {
  max-width: 1180px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.7rem;
}

.hero-brand {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  text-decoration: none;
}

.hero-brand-dot {
  width: 1.65rem;
  height: 1.65rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.9);
  flex-shrink: 0;
}

.hero-brand-copy strong {
  display: block;
  font-size: 0.95rem;
  color: #fff;
  font-weight: 800;
  white-space: nowrap;
}

.hero-brand-copy small {
  display: block;
  font-size: 0.72rem;
  color: rgb(255 255 255 / 0.7);
}

.hero-desktop-nav {
  display: none;
  align-items: center;
  gap: 0.4rem;
}

.hero-nav-link {
  border-radius: 999px;
  padding: 0.44rem 0.8rem;
  font-size: 0.82rem;
  color: rgb(255 255 255 / 0.9);
  border: 1px solid rgb(255 255 255 / 0.22);
  background: rgb(255 255 255 / 0.08);
  backdrop-filter: blur(8px);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  transition: background 0.15s;
}

.hero-nav-link:hover {
  background: rgb(255 255 255 / 0.18);
}

.hero-count-pill {
  min-width: 1rem;
  height: 1rem;
  border-radius: 999px;
  background: rgb(255 200 100 / 0.85);
  color: #1c1411;
  font-size: 0.64rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.22rem;
  font-weight: 700;
}

.hero-header__actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.hero-mgmt-pill {
  border-radius: 999px;
  border: 1px solid rgb(255 255 255 / 0.3);
  background: rgb(255 255 255 / 0.12);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.46rem 0.72rem;
  white-space: nowrap;
  text-decoration: none;
}

.hero-cart-pill {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 12px;
  background: rgb(255 255 255 / 0.12);
  border: 1px solid rgb(255 255 255 / 0.24);
  backdrop-filter: blur(8px);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  padding: 0 0.35rem;
  text-decoration: none;
}

.hero-cart-pill svg { width: 16px; height: 16px; }

.hero-cart-pill span {
  min-width: 0.9rem;
  height: 0.9rem;
  border-radius: 999px;
  background: #e8a347;
  color: #1c1411;
  font-size: 0.6rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.hero-hamburger {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 12px;
  border: 1px solid rgb(255 255 255 / 0.24);
  background: rgb(255 255 255 / 0.1);
  backdrop-filter: blur(8px);
  display: grid;
  align-content: center;
  gap: 4px;
  padding: 0 8px;
  cursor: pointer;
}

.hero-hamburger span {
  display: block;
  height: 2px;
  border-radius: 999px;
  background: #fff;
  transition: transform 0.2s;
}

.hero-header__content {
  position: relative;
  z-index: 5;
  flex: 1;
  display: flex;
  align-items: center;
  padding: 3rem 1.5rem 5rem;
  max-width: 1180px;
  margin: 0 auto;
  width: 100%;
}

.hero-header__text {
  max-width: 600px;
  display: grid;
  gap: 1rem;
}

.hero-eyebrow {
  display: inline-flex;
  width: max-content;
  border-radius: 999px;
  padding: 0.28rem 0.9rem;
  background: rgb(255 200 100 / 0.18);
  border: 1px solid rgb(255 200 100 / 0.35);
  color: rgb(255 220 150);
  font-size: 0.78rem;
  font-weight: 700;
  margin: 0;
}

.hero-title {
  margin: 0;
  font-size: clamp(1.8rem, 5vw, 3.2rem);
  font-weight: 900;
  color: #fff;
  line-height: 1.2;
  text-shadow: 0 2px 16px rgb(0 0 0 / 0.4);
}

.hero-subtitle {
  margin: 0;
  font-size: clamp(0.9rem, 2vw, 1.1rem);
  color: rgb(255 255 255 / 0.82);
  line-height: 1.65;
}

.hero-cta-row {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
  margin-top: 0.3rem;
}

.hero-cta-btn {
  padding: 0.72rem 1.5rem;
  border-radius: 999px;
  background: #e8a347;
  color: #1c1411;
  font-size: 0.9rem;
  font-weight: 800;
  text-decoration: none;
  transition: background 0.18s, transform 0.15s;
}

.hero-cta-btn:hover {
  background: #d4923a;
  transform: translateY(-1px);
}

.hero-cta-outline {
  padding: 0.72rem 1.4rem;
  border-radius: 999px;
  border: 1.5px solid rgb(255 255 255 / 0.45);
  color: #fff;
  background: transparent;
  font-size: 0.9rem;
  font-weight: 700;
  text-decoration: none;
  backdrop-filter: blur(4px);
  transition: background 0.18s;
}

.hero-cta-outline:hover {
  background: rgb(255 255 255 / 0.12);
}

.hero-scroll-hint {
  position: absolute;
  bottom: 1.8rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
}

.hero-scroll-hint span {
  display: block;
  width: 1.6rem;
  height: 2.6rem;
  border-radius: 999px;
  border: 2px solid rgb(255 255 255 / 0.4);
  position: relative;
}

.hero-scroll-hint span::after {
  content: '';
  position: absolute;
  top: 0.35rem;
  left: 50%;
  transform: translateX(-50%);
  width: 0.32rem;
  height: 0.32rem;
  background: #fff;
  border-radius: 50%;
  animation: scrollDot 1.5s ease-in-out infinite;
}

@keyframes scrollDot {
  0% { top: 0.35rem; opacity: 1; }
  100% { top: 1.5rem; opacity: 0; }
}

.hero-header--preview .hero-scroll-hint { display: none; }
.hero-header--preview .hero-header__content { padding: 1rem 1.2rem 1.5rem; }
.hero-header--preview .hero-title { font-size: 1.3rem; }
.hero-header--preview .hero-cta-row { display: none; }

.mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 0.4);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s;
  z-index: 119;
}

.mobile-overlay.visible { opacity: 1; pointer-events: auto; }

.mobile-sheet {
  position: fixed;
  top: 0;
  right: -320px;
  width: min(300px, 86vw);
  height: 100vh;
  background: #1c1411;
  border-left: 1px solid rgb(255 255 255 / 0.1);
  box-shadow: -12px 0 24px rgb(0 0 0 / 0.3);
  transition: right 0.22s ease;
  padding: 0.9rem 0.8rem;
  z-index: 120;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 0.8rem;
}

.mobile-sheet.open { right: 0; }

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
}

.sheet-close {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  border: 1px solid rgb(255 255 255 / 0.2);
  background: transparent;
  color: #fff;
  font-size: 1.1rem;
  cursor: pointer;
}

.sheet-links {
  display: grid;
  gap: 0.4rem;
  align-content: start;
}

.sheet-links a {
  border-radius: 12px;
  padding: 0.58rem 0.65rem;
  background: rgb(255 255 255 / 0.06);
  border: 1px solid rgb(255 255 255 / 0.1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-decoration: none;
}

.sheet-management-btn {
  border-radius: 12px;
  padding: 0.62rem 0.65rem;
  text-align: center;
  border: 1px solid rgb(255 200 100 / 0.3);
  background: rgb(255 200 100 / 0.12);
  color: rgb(255 220 150);
  font-weight: 700;
  text-decoration: none;
  display: block;
}

@media (min-width: 920px) {
  .hero-desktop-nav { display: flex; }
  .hero-hamburger { display: none; }
}

@media (max-width: 540px) {
  .hero-mgmt-pill { display: none; }
}
</style>
