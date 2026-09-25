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
            v-for="link in desktopLinks"
            :key="link.url"
            :href="link.url"
            class="hero-nav-link"
          >
            {{ link.label }}
            <span class="hero-count-pill" v-if="link.kind === 'cart' && cartCount > 0">{{ cartCount }}</span>
          </a>
        </nav>

        <div class="hero-header__actions">
          <button class="hero-search-btn" type="button" @click="openSearch" aria-label="جستجو">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" width="18" height="18">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
          </button>
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
        <p class="hero-eyebrow">تازه، سالم، روزانه</p>
        <h1 class="hero-title">{{ heroTitle }}</h1>
        <p class="hero-subtitle">{{ heroSubtitle }}</p>
        <div class="hero-cta-row">
          <a class="hero-cta-btn" href="/menu">{{ heroCta }}</a>
        </div>
        <div class="hero-benefits">
          <span>مواد اولیه تازه</span>
          <span>ارسال سریع</span>
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
    </aside>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useSearchModal } from '@/composables/useSearchModal'

const props = defineProps({
  branding: { type: Object, default: () => ({}) },
  cartCount: { type: Number, default: 0 },
  hasLastOrder: { type: Boolean, default: false },
  lastOrderUrl: { type: String, default: '/menu' },
  page: { type: String, default: 'landing' },
  preview: { type: Boolean, default: false },
})

const { openSearch } = useSearchModal()
const mobileOpen = ref(false)

const heroTitle = computed(() => String(props.branding?.hero_section_title || props.branding?.hero_title || props.branding?.name || 'سبک زندگی سالم، انتخاب هر روز ما').trim())
const heroSubtitle = computed(() => String(props.branding?.hero_section_description || props.branding?.hero_subtitle || props.branding?.tagline || 'غذاهای سالم و متنوع با بهترین مواد اولیه تازه برای یک زندگی پرانرژی و متعادل.').trim())
const heroCta = computed(() => String(props.branding?.hero_section_cta || props.branding?.primary_cta_label || 'سفارش آنلاین').trim())

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

const desktopLinks = computed(() => links.value.filter((link) => link.kind !== 'cart'))
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
  background:
    radial-gradient(circle at 15% 18%, color-mix(in srgb, var(--ds-color-action-accent) 12%, transparent), transparent 24%),
    linear-gradient(135deg, var(--ds-color-bg-page) 0%, var(--ds-color-surface-raised) 100%);
  background-size: cover;
  background-position: left center;
  background-repeat: no-repeat;
}

.hero-header__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--ds-color-surface-raised) 48%, transparent) 0%,
    color-mix(in srgb, var(--ds-color-surface-raised) 72%, transparent) 46%,
    color-mix(in srgb, var(--ds-color-surface-raised) 94%, transparent) 100%
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
  align-items: flex-end;
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
  background: var(--ds-color-action-accent);
  flex-shrink: 0;
}

.hero-brand-copy strong {
  display: block;
  font-size: 0.95rem;
  color: var(--ds-color-text-primary);
  font-weight: 800;
  white-space: nowrap;
}

.hero-brand-copy small {
  display: block;
  font-size: 0.72rem;
  color: var(--ds-color-text-secondary);
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
  color: var(--ds-color-text-primary);
  border: 1px solid var(--ds-color-border);
  background: var(--ds-color-surface-raised);
  backdrop-filter: blur(8px);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  transition: background 0.15s;
}

.hero-nav-link:hover {
  background: var(--ds-color-action-primary-soft);
}

.hero-count-pill {
  min-width: 1rem;
  height: 1rem;
  border-radius: 999px;
  background: var(--ds-color-action-accent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
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

.hero-search-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--ds-color-surface-raised);
  border: 1px solid var(--ds-color-border);
  backdrop-filter: blur(8px);
  color: var(--ds-color-action-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s;
}

.hero-search-btn:hover {
  background: var(--ds-color-action-primary-soft);
}

.hero-cart-pill {
  min-width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--ds-color-action-accent);
  border: 1px solid var(--ds-color-action-accent);
  backdrop-filter: blur(8px);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
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
  background: color-mix(in srgb, var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff)) 18%, transparent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
  font-size: 0.6rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.hero-hamburger {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid var(--ds-color-border);
  background: var(--ds-color-surface-raised);
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
  background: var(--ds-color-action-primary);
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
  background: var(--ds-color-action-accent-soft);
  border: 1px solid color-mix(in srgb, var(--ds-color-action-accent) 35%, transparent);
  color: var(--ds-color-action-primary);
  font-size: 0.78rem;
  font-weight: 700;
  margin: 0;
}

.hero-title {
  margin: 0;
  font-size: clamp(1.8rem, 5vw, 3.2rem);
  font-weight: 900;
  color: var(--ds-color-text-primary);
  line-height: 1.2;
}

.hero-subtitle {
  margin: 0;
  font-size: clamp(0.9rem, 2vw, 1.1rem);
  color: var(--ds-color-text-secondary);
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
  min-height: 48px;
  border-radius: 999px;
  background: var(--ds-color-action-accent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
  font-size: 0.9rem;
  font-weight: 800;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  transition: background 0.18s, transform 0.15s, filter var(--ds-motion-fast, 160ms);
}

.hero-cta-btn:hover {
  filter: brightness(0.96);
  transform: translateY(-1px);
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
  border: 2px solid var(--ds-color-border);
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
  background: var(--ds-color-action-accent);
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
  background: var(--ds-color-surface-raised);
  border-left: 1px solid var(--ds-color-border);
  box-shadow: -12px 0 24px rgb(0 0 0 / 0.3);
  transition: right 0.22s ease;
  padding: 0.9rem 0.8rem;
  z-index: 120;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 0.8rem;
}

.mobile-sheet.open { right: 0; }

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--ds-color-text-primary);
}

.sheet-close {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 1px solid var(--ds-color-border);
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-action-primary);
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
  min-height: 48px;
  background: var(--ds-color-surface-raised);
  border: 1px solid var(--ds-color-border);
  color: var(--ds-color-text-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-decoration: none;
}

@media (min-width: 920px) {
  .hero-desktop-nav { display: flex; }
  .hero-hamburger { display: none; }
}

.hero-header :is(a, button):focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 3px; }

@media (prefers-reduced-motion: reduce) {
  .hero-header *,
  .hero-header *::before,
  .hero-header *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}

</style>
