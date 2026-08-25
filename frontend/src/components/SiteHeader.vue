<template>
  <header
    class="site-header"
    :class="{
      'site-header--transparent': transparent,
      'site-header--solid': !transparent,
    }"
    dir="rtl"
  >
    <div class="site-header-inner">
      <a class="site-header-brand" href="/">
        <span class="brand-name">{{ branding.name }}</span>
        <small class="brand-tagline" v-if="transparent && branding.tagline">{{ branding.tagline }}</small>
      </a>

      <nav class="site-header-nav">
        <a href="/" class="nav-link">خانه</a>
        <a href="/menu" class="nav-link">منو</a>
        <a href="/about-us" class="nav-link">درباره ما</a>
      </nav>

      <div class="site-header-actions">
        <a href="/cart" class="cart-btn" :aria-label="`سبد خرید${cartCount > 0 ? ` (${cartCount})` : ''}`">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="9" cy="20" r="1" />
            <circle cx="18" cy="20" r="1" />
            <path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.5L22 7H7" />
          </svg>
          <span v-if="cartCount > 0" class="cart-count">{{ cartCount }}</span>
        </a>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  branding: {
    type: Object,
    default: () => ({ name: '', tagline: '' }),
  },
  cartCount: {
    type: Number,
    default: 0,
  },
  heroVisible: {
    type: Boolean,
    default: false,
  },
  hasHero: {
    type: Boolean,
    default: false,
  },
})

const transparent = computed(() => props.hasHero && props.heroVisible)
</script>

<style scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 200;
  width: 100%;
  transition: background 0.3s ease, box-shadow 0.3s ease, backdrop-filter 0.3s ease;
  direction: rtl;
}

.site-header--transparent {
  background: transparent;
  box-shadow: none;
}

.site-header--solid {
  background: rgb(var(--palette-eggshell-rgb, 251 248 244) / 0.92);
  backdrop-filter: blur(14px) saturate(1.4);
  -webkit-backdrop-filter: blur(14px) saturate(1.4);
  box-shadow: 0 2px 18px 0 rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.10);
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.10);
}

.site-header-inner {
  width: min(1200px, calc(100% - 2.5rem));
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.2rem;
  padding: 0.85rem 0;
  transition: padding 0.3s ease;
}

.site-header--transparent .site-header-inner {
  padding: 1.2rem 0;
}

.site-header-brand {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  text-decoration: none;
  line-height: 1.15;
  transition: color 0.3s;
}

.brand-name {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  transition: color 0.3s;
}

.site-header--solid .brand-name {
  color: var(--palette-deep-sapphire, #6F4A31);
}

.site-header--transparent .brand-name {
  color: #fff;
  text-shadow: 0 2px 12px rgb(0 0 0 / 0.35);
}

.brand-tagline {
  font-size: 0.72rem;
  color: rgb(255 255 255 / 0.75);
  font-weight: 400;
}

.site-header-nav {
  display: flex;
  align-items: center;
  gap: 0.2rem;
}

.nav-link {
  padding: 0.38rem 0.7rem;
  border-radius: 999px;
  font-size: 0.86rem;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.18s, color 0.18s;
}

.site-header--solid .nav-link {
  color: var(--ink-800, #654A38);
}

.site-header--solid .nav-link:hover {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
  color: var(--palette-deep-sapphire, #6F4A31);
}

.site-header--transparent .nav-link {
  color: rgb(255 255 255 / 0.88);
}

.site-header--transparent .nav-link:hover {
  background: rgb(255 255 255 / 0.15);
  color: #fff;
}

.site-header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.cart-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 50%;
  text-decoration: none;
  transition: background 0.18s, color 0.18s;
}

.site-header--solid .cart-btn {
  color: var(--palette-deep-sapphire, #6F4A31);
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
}

.site-header--solid .cart-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.15);
}

.site-header--transparent .cart-btn {
  color: #fff;
  background: rgb(255 255 255 / 0.15);
}

.site-header--transparent .cart-btn:hover {
  background: rgb(255 255 255 / 0.25);
}

.cart-count {
  position: absolute;
  top: -0.2rem;
  left: -0.2rem;
  min-width: 1.1rem;
  height: 1.1rem;
  border-radius: 999px;
  background: var(--palette-deep-saffron, #C98D42);
  color: #fff;
  font-size: 0.62rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.2rem;
  line-height: 1;
}

@media (max-width: 640px) {
  .site-header-nav {
    display: none;
  }
}
</style>
