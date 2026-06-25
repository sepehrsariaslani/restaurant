<template>
  <header class="app-header" :class="{ 'app-header--preview': preview }" dir="rtl">
    <div class="header-surface"></div>
    <div class="header-inner">
      <a href="/" class="brand-link">
        <span class="brand-dot"></span>
        <div class="brand-copy">
          <strong>{{ branding.name }}</strong>
          <small>{{ branding.tagline }}</small>
        </div>
      </a>

      <nav class="desktop-nav" aria-label="ناوبری">
        <a
          v-for="link in links"
          :key="link.url"
          :href="link.url"
          class="nav-link"
          :class="{ active: isActive(link) }"
        >
          {{ link.label }}
          <span class="count-pill" v-if="link.kind === 'cart' && cartCount > 0">{{ cartCount }}</span>
        </a>
      </nav>

      <button class="center-search-btn" type="button" @click="openSearch" aria-label="جستجو">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <span class="center-search-label">جستجو</span>
      </button>

      <div class="header-actions">
        <a :href="managementLoginUrl" class="management-login-pill" aria-label="ورود مدیریت">
          ورود مدیریت
        </a>

        <button class="search-pill search-pill--desktop" type="button" @click="openSearch" aria-label="جستجو">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </button>

        <a href="/cart" class="cart-pill" aria-label="سبد سفارش">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round">
            <circle cx="8" cy="20" r="1" />
            <circle cx="18" cy="20" r="1" />
            <path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.5L22 7H7" />
          </svg>
          <span v-if="cartCount > 0">{{ cartCount }}</span>
        </a>

        <button class="hamburger" :class="{ open: mobileOpen }" type="button" @click="mobileOpen = !mobileOpen" aria-label="منو">
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>
    </div>

    <div class="mobile-overlay" :class="{ visible: mobileOpen }" @click="mobileOpen = false"></div>

    <aside class="mobile-sheet" :class="{ open: mobileOpen }" dir="rtl">
      <div class="sheet-head">
        <strong>{{ branding.name }}</strong>
        <button class="sheet-close" type="button" @click="mobileOpen = false">×</button>
      </div>

      <nav class="sheet-links">
        <a
          v-for="link in links"
          :key="`m-${link.url}`"
          :href="link.url"
          :class="{ active: isActive(link) }"
          @click="mobileOpen = false"
        >
          <span>{{ link.label }}</span>
          <span class="count-pill" v-if="link.kind === 'cart' && cartCount > 0">{{ cartCount }}</span>
        </a>
      </nav>

      <a class="sheet-management-btn" :href="managementLoginUrl" @click="mobileOpen = false">
        ورود به مدیریت
      </a>
    </aside>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useSearchModal } from '@/composables/useSearchModal'

const props = defineProps({
  branding: {
    type: Object,
    default: () => ({
      name: 'Veederakht Restaurant',
      tagline: 'منوی آنلاین',
    }),
  },
  cartCount: {
    type: Number,
    default: 0,
  },
  hasLastOrder: {
    type: Boolean,
    default: false,
  },
  page: {
    type: String,
    default: 'landing',
  },
  lastOrderUrl: {
    type: String,
    default: '/menu',
  },
  preview: {
    type: Boolean,
    default: false,
  },
})

const { openSearch } = useSearchModal()
const mobileOpen = ref(false)
const managementLoginUrl = '/management/login?redirect_to=%2Fmanagement'

const currentPath = computed(() => {
  const path = String(window.location.pathname || '/').replace(/\/+$/, '')
  return path || '/'
})

const links = computed(() => {
  const base = [
    { key: 'landing', label: 'خانه', url: '/', prefix: '/', exact: true },
    { key: 'menu', label: 'منو', url: '/menu', prefix: '/menu' },
    { key: 'about-us', label: 'درباره ما', url: '/about-us', prefix: '/about-us' },
    { key: 'faq', label: 'سوالات', url: '/faq', prefix: '/faq' },
    { key: 'cart', label: 'سبد سفارش', url: '/cart', prefix: '/cart', kind: 'cart' },
  ]

  if (props.hasLastOrder && props.lastOrderUrl) {
    base.push({ key: 'order-success', label: 'پیگیری سفارش', url: props.lastOrderUrl, prefix: '/order-success' })
  }

  return base
})

function isActive(link) {
  if (link.key === 'menu') {
    return props.page === 'menu' || props.page === 'item'
  }
  if (link.key === 'landing') {
    return props.page === 'landing'
  }
  if (link.key === 'cart') {
    return props.page === 'cart'
  }
  if (link.key === 'about-us') {
    return props.page === 'about-us'
  }
  if (link.key === 'faq') {
    return props.page === 'faq'
  }
  if (link.key === 'order-success') {
    return props.page === 'order-success'
  }

  const path = currentPath.value
  if (link.exact) {
    return path === link.url
  }
  return path === link.url || path.startsWith(`${link.prefix}/`) || path.startsWith(link.prefix)
}
</script>

<style scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 120;
  padding: 0.75rem 0.7rem 0;
}

.app-header--preview {
  position: relative;
  inset: auto;
  z-index: 1;
  padding: 0;
}

.app-header--preview .header-surface {
  display: none;
}

.header-surface {
  position: absolute;
  top: 0.35rem;
  left: 0.7rem;
  right: 0.7rem;
  height: 64px;
  border-radius: 22px;
  }

.header-inner {
  position: relative;
  max-width: 1180px;
  margin: 0 auto;
  min-height: 64px;
  padding: 0 0.8rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.7rem;
  border-radius: 22px;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  box-shadow: 0 10px 22px rgb(15 23 42 / 0.08);
  color: var(--text-primary);
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
}

.brand-dot {
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 999px;
  background: var(--accent-green);
}

.brand-copy {
  min-width: 0;
}

.brand-copy strong {
  display: block;
  font-size: 0.93rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-copy small {
  display: block;
  color: var(--text-muted);
  font-size: 0.73rem;
}

.desktop-nav {
  display: none;
  align-items: center;
  gap: 0.45rem;
}

.nav-link {
  border-radius: 999px;
  padding: 0.48rem 0.84rem;
  font-size: 0.84rem;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  color: var(--text-primary);
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.nav-link.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: #fff;
  color: var(--accent-green);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.45);
}

.count-pill {
  min-width: 1.1rem;
  height: 1.1rem;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.68rem;
  padding: 0 0.25rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.management-login-pill {
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.3);
  background: rgb(var(--palette-june-bud-rgb) / 0.26);
  color: var(--text-primary);
  font-size: 0.76rem;
  font-weight: 700;
  line-height: 1;
  padding: 0.5rem 0.72rem;
  white-space: nowrap;
}

.search-pill {
  min-width: 2.2rem;
  height: 2.2rem;
  border-radius: 12px;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.24);
  color: var(--text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.35rem;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.search-pill svg { width: 16px; height: 16px; }

.search-pill:hover {
  background: var(--accent-green20, rgba(111,74,49,0.1));
  border-color: var(--accent-green, #6f4a31);
}

.cart-pill {
  min-width: 2.2rem;
  height: 2.2rem;
  border-radius: 12px;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.24);
  color: var(--text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  padding: 0 0.35rem;
}

.cart-pill svg {
  width: 16px;
  height: 16px;
}

.cart-pill span {
  min-width: 0.95rem;
  height: 0.95rem;
  border-radius: 999px;
  background: var(--accent-green);
  color: #fff;
  font-size: 0.62rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.hamburger {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 12px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.24);
  background: #fff;
  display: grid;
  align-content: center;
  gap: 4px;
  padding: 0 8px;
}

.hamburger span {
  display: block;
  height: 2px;
  border-radius: 999px;
  background: var(--text-primary);
  transition: transform 0.2s ease;
}

.mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgb(15 23 42 / 0.28);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease;
}

.mobile-overlay.visible {
  opacity: 1;
  pointer-events: auto;
}

.mobile-sheet {
  position: fixed;
  top: 0;
  right: -320px;
  width: min(300px, 86vw);
  height: 100vh;
  background: #fff;
  border-left: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  box-shadow: -12px 0 24px rgb(15 23 42 / 0.12);
  transition: right 0.2s ease;
  padding: 0.9rem 0.8rem;
  z-index: 121;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 0.8rem;
}

.mobile-sheet.open {
  right: 0;
}

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-primary);
}

.sheet-close {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.3);
  background: #fff;
  color: var(--text-primary);
  font-size: 1.1rem;
}

.sheet-links {
  display: grid;
  gap: 0.45rem;
  align-content: start;
}

.sheet-links a {
  border-radius: 12px;
  padding: 0.58rem 0.65rem;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sheet-links a.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: var(--accent-green);
}

.sheet-management-btn {
  border-radius: 12px;
  padding: 0.62rem 0.65rem;
  text-align: center;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.3);
  background: rgb(var(--palette-june-bud-rgb) / 0.3);
  color: var(--text-primary);
  font-weight: 700;
}

@media (min-width: 920px) {
  .header-surface {
    height: 70px;
  }

  .header-inner {
    min-height: 70px;
  }

  .desktop-nav {
    display: flex;
  }

  .hamburger {
    display: none;
  }
}

/* Centered search button in navbar */
.center-search-btn {
  display: none;
  align-items: center;
  gap: 0.45rem;
  border-radius: 14px;
  padding: 0.45rem 0.95rem;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, transform 0.15s;
  font-family: inherit;
  font-size: 0.84rem;
  font-weight: 600;
  white-space: nowrap;
}

.center-search-btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.center-search-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.4);
  transform: translateY(-1px);
}

.center-search-btn:active {
  transform: translateY(0);
}

/* Desktop (>=920px): show centered button, hide the old search-pill */
@media (min-width: 920px) {
  .center-search-btn {
    display: inline-flex;
  }
  .search-pill--desktop {
    display: none;
  }
}

/* Mobile (<920px): show centered button prominently in navbar, hide old search-pill */
@media (max-width: 919px) {
  .center-search-btn {
    display: inline-flex;
    order: -1;
  }
  .search-pill--desktop {
    display: none;
  }
}

@media (max-width: 540px) {
  .management-login-pill {
    display: none;
  }
}
</style>
