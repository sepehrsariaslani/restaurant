<template>
  <header class="glass-header" :class="{ 'glass-header--preview': preview }" dir="rtl">
    <div class="glass-header__inner">
      <a href="/" class="glass-brand">
        <div class="glass-brand-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" />
            <path d="M8 12h8M12 8v8" />
          </svg>
        </div>
        <div class="glass-brand-copy">
          <strong>{{ branding.name }}</strong>
          <small>{{ branding.tagline }}</small>
        </div>
      </a>

      <nav class="glass-nav" aria-label="ناوبری">
        <a
          v-for="link in links"
          :key="link.url"
          :href="link.url"
          class="glass-nav-link"
          :class="{ active: isActive(link) }"
        >
          {{ link.label }}
          <span class="glass-count" v-if="link.kind === 'cart' && cartCount > 0">{{ cartCount }}</span>
        </a>
      </nav>

      <div class="glass-actions">
        <a :href="managementLoginUrl" class="glass-mgmt-btn">ورود مدیریت</a>
        <button class="glass-search-btn" type="button" @click="openSearch" aria-label="جستجو">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" width="18" height="18">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </button>
        <a href="/cart" class="glass-cart-btn" aria-label="سبد سفارش">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round">
            <circle cx="8" cy="20" r="1" /><circle cx="18" cy="20" r="1" />
            <path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.5L22 7H7" />
          </svg>
          <span v-if="cartCount > 0">{{ cartCount }}</span>
        </a>
        <button class="glass-hamburger" :class="{ open: mobileOpen }" type="button" @click="mobileOpen = !mobileOpen" aria-label="منو">
          <span></span><span></span><span></span>
        </button>
      </div>
    </div>

    <div class="glass-mobile-overlay" :class="{ visible: mobileOpen }" @click="mobileOpen = false"></div>
    <aside class="glass-sheet" :class="{ open: mobileOpen }" dir="rtl">
      <div class="glass-sheet-head">
        <strong>{{ branding.name }}</strong>
        <button class="glass-sheet-close" type="button" @click="mobileOpen = false">×</button>
      </div>
      <nav class="glass-sheet-links">
        <a v-for="link in links" :key="`m-${link.url}`" :href="link.url" :class="{ active: isActive(link) }" @click="mobileOpen = false">
          <span>{{ link.label }}</span>
          <span class="glass-count" v-if="link.kind === 'cart' && cartCount > 0">{{ cartCount }}</span>
        </a>
      </nav>
      <a class="glass-sheet-mgmt" :href="managementLoginUrl" @click="mobileOpen = false">ورود به مدیریت</a>
    </aside>
  </header>
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
const managementLoginUrl = '/management/login?redirect_to=%2Fmanagement'

const links = computed(() => {
  const base = [
    { key: 'landing', label: 'خانه', url: '/', exact: true },
    { key: 'menu', label: 'منو', url: '/menu', prefix: '/menu' },
    { key: 'about-us', label: 'درباره ما', url: '/about-us' },
    { key: 'faq', label: 'سوالات', url: '/faq' },
    { key: 'cart', label: 'سبد سفارش', url: '/cart', kind: 'cart' },
  ]
  if (props.hasLastOrder && props.lastOrderUrl) {
    base.push({ key: 'order-success', label: 'پیگیری سفارش', url: props.lastOrderUrl })
  }
  return base
})

function isActive(link) {
  if (link.key === 'menu') return props.page === 'menu' || props.page === 'item'
  if (link.key === 'landing') return props.page === 'landing'
  if (link.key === 'cart') return props.page === 'cart'
  if (link.key === 'about-us') return props.page === 'about-us'
  if (link.key === 'faq') return props.page === 'faq'
  return false
}
</script>

<style scoped>
.glass-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 120;
  padding: 0;
  background: rgb(255 255 255 / 0.72);
  backdrop-filter: blur(18px) saturate(1.6);
  -webkit-backdrop-filter: blur(18px) saturate(1.6);
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.12);
  box-shadow: 0 2px 24px rgb(0 0 0 / 0.07);
}

.glass-header--preview {
  position: relative;
  inset: auto;
}

.glass-header__inner {
  max-width: 1180px;
  margin: 0 auto;
  min-height: 68px;
  padding: 0 1.2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.7rem;
}

.glass-brand {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  text-decoration: none;
  min-width: 0;
}

.glass-brand-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--palette-deep-sapphire, #6F4A31), #9b6a47);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.glass-brand-copy strong {
  display: block;
  font-size: 0.93rem;
  color: var(--ink-900, #1c1411);
  font-weight: 800;
  white-space: nowrap;
}

.glass-brand-copy small {
  display: block;
  font-size: 0.72rem;
  color: var(--ink-600, #9a8a80);
}

.glass-nav {
  display: none;
  align-items: center;
  gap: 0.3rem;
}

.glass-nav-link {
  border-radius: 10px;
  padding: 0.44rem 0.78rem;
  font-size: 0.83rem;
  color: var(--ink-700, #5a4a40);
  background: transparent;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.glass-nav-link:hover {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
  color: var(--ink-900, #1c1411);
}

.glass-nav-link.active {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.12);
  color: var(--palette-deep-sapphire, #6F4A31);
  font-weight: 700;
}

.glass-count {
  min-width: 1.05rem;
  height: 1.05rem;
  border-radius: 999px;
  background: var(--palette-deep-sapphire, #6F4A31);
  color: #fff;
  font-size: 0.64rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.22rem;
  font-weight: 700;
}

.glass-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.glass-mgmt-btn {
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.28);
  background: rgb(var(--palette-june-bud-rgb, 201 223 144) / 0.28);
  color: var(--ink-800, #3d2e26);
  font-size: 0.76rem;
  font-weight: 700;
  padding: 0.46rem 0.75rem;
  white-space: nowrap;
  text-decoration: none;
  transition: background 0.15s;
}

.glass-mgmt-btn:hover {
  background: rgb(var(--palette-june-bud-rgb, 201 223 144) / 0.45);
}

.glass-search-btn {
  width: 2.1rem;
  height: 2.1rem;
  border-radius: 10px;
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.18);
  color: var(--text-primary, #3f2a1d);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.glass-search-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.16);
  border-color: var(--accent-green, #6f4a31);
}

.glass-cart-btn {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 12px;
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.18);
  color: var(--ink-800, #3d2e26);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  padding: 0 0.35rem;
  text-decoration: none;
  transition: background 0.15s;
}

.glass-cart-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.14);
}

.glass-cart-btn svg { width: 16px; height: 16px; }

.glass-cart-btn span {
  min-width: 0.9rem;
  height: 0.9rem;
  border-radius: 999px;
  background: var(--accent-green, #4caf50);
  color: #fff;
  font-size: 0.6rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.glass-hamburger {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 12px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.2);
  background: transparent;
  display: grid;
  align-content: center;
  gap: 4px;
  padding: 0 8px;
  cursor: pointer;
}

.glass-hamburger span {
  display: block;
  height: 2px;
  border-radius: 999px;
  background: var(--ink-800, #3d2e26);
  transition: transform 0.2s;
}

.glass-mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 0.25);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s;
  z-index: 119;
}

.glass-mobile-overlay.visible { opacity: 1; pointer-events: auto; }

.glass-sheet {
  position: fixed;
  top: 0;
  right: -320px;
  width: min(300px, 86vw);
  height: 100vh;
  background: rgb(255 255 255 / 0.92);
  backdrop-filter: blur(20px);
  border-left: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.14);
  box-shadow: -12px 0 28px rgb(0 0 0 / 0.1);
  transition: right 0.22s ease;
  padding: 0.9rem 0.8rem;
  z-index: 120;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 0.8rem;
}

.glass-sheet.open { right: 0; }

.glass-sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--ink-900, #1c1411);
}

.glass-sheet-close {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.2);
  background: transparent;
  color: var(--ink-800, #3d2e26);
  font-size: 1.1rem;
  cursor: pointer;
}

.glass-sheet-links {
  display: grid;
  gap: 0.4rem;
  align-content: start;
}

.glass-sheet-links a {
  border-radius: 12px;
  padding: 0.58rem 0.65rem;
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.05);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.12);
  color: var(--ink-800, #3d2e26);
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-decoration: none;
  transition: background 0.15s;
}

.glass-sheet-links a.active {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.12);
  color: var(--palette-deep-sapphire, #6F4A31);
  font-weight: 700;
}

.glass-sheet-mgmt {
  border-radius: 12px;
  padding: 0.62rem 0.65rem;
  text-align: center;
  border: 1px solid rgb(var(--palette-june-bud-rgb, 201 223 144) / 0.5);
  background: rgb(var(--palette-june-bud-rgb, 201 223 144) / 0.22);
  color: var(--ink-800, #3d2e26);
  font-weight: 700;
  text-decoration: none;
  display: block;
}

@media (min-width: 920px) {
  .glass-nav { display: flex; }
  .glass-hamburger { display: none; }
}

@media (max-width: 540px) {
  .glass-mgmt-btn { display: none; }
}
</style>
