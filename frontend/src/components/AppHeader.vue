<template>
  <header class="app-header" :class="{ 'app-header--preview': preview }" dir="rtl">
    <div class="header-surface"></div>
    <div class="webapp-header">
      <button class="webapp-icon-btn webapp-menu-btn" :class="{ open: mobileOpen }" type="button" @click="mobileOpen = !mobileOpen" aria-label="منو">
        <Menu v-if="!mobileOpen" :size="18" />
        <X v-else :size="18" />
      </button>

      <a href="/" class="webapp-brand" :aria-label="branding.name">
        <span>{{ branding.name }}</span>
      </a>

      <div class="webapp-actions">
        <button class="webapp-icon-btn" type="button" aria-label="جستجو در منو" @click="openSearch">
          <Search :size="17" />
        </button>
        <a class="webapp-icon-btn mobile-cart-btn" href="/cart" :aria-label="`سبد سفارش، ${cartCount} آیتم`">
          <ShoppingCart :size="17" />
          <span v-if="cartCount > 0" class="mobile-cart-count">{{ cartCount }}</span>
        </a>
        <a class="webapp-icon-btn" :href="accountHref" aria-label="حساب کاربری">
          <UserRound :size="17" />
        </a>
      </div>
    </div>

    <div class="header-inner">
      <a href="/" class="brand-link">
        <span class="brand-dot">{{ brandInitial }}</span>
        <div class="brand-copy">
          <strong>{{ branding.name }}</strong>
          <small>{{ branding.tagline || 'منوی آنلاین' }}</small>
        </div>
      </a>

      <nav class="desktop-nav" aria-label="ناوبری">
        <a
          v-for="link in desktopLinks"
          :key="link.url"
          :href="link.url"
          class="nav-link"
          :class="{ active: isActive(link) }"
        >
          <component :is="link.icon" :size="15" />
          <span>{{ link.label }}</span>
          <span class="count-pill" v-if="link.kind === 'cart' && cartCount > 0">{{ cartCount }}</span>
        </a>
      </nav>

      <div class="header-actions">
        <a class="action-icon-pill" :href="accountHref" aria-label="حساب کاربری" title="حساب کاربری">
          <UserRound :size="16" />
        </a>
        <button class="search-pill" type="button" @click="openSearch" aria-label="جستجو در منو" title="جستجو در منو">
          <Search :size="16" />
        </button>

        <a href="/cart" class="cart-pill" aria-label="سبد سفارش">
          <ShoppingCart :size="16" />
          <span class="cart-label">سبد</span>
          <span v-if="cartCount > 0" class="cart-count">{{ cartCount }}</span>
        </a>

        <button class="hamburger" :class="{ open: mobileOpen }" type="button" @click="mobileOpen = !mobileOpen" aria-label="منو">
          <Menu v-if="!mobileOpen" :size="18" />
          <X v-else :size="18" />
        </button>
      </div>
    </div>

    <div class="mobile-overlay" :class="{ visible: mobileOpen }" @click="mobileOpen = false"></div>

    <aside class="mobile-sheet" :class="{ open: mobileOpen }" dir="rtl">
      <div class="sheet-head">
        <div class="sheet-brand-card">
          <span class="sheet-brand-mark">{{ brandInitial }}</span>
          <div>
            <strong>{{ branding.name }}</strong>
            <small>{{ branding.tagline || 'منوی آنلاین' }}</small>
          </div>
        </div>
        <button class="sheet-close" type="button" @click="mobileOpen = false" aria-label="بستن"><X :size="17" /></button>
      </div>

      <button class="sheet-search" type="button" @click="openMobileSearch">
        <Search :size="17" />
        <span>جستجو در منو</span>
      </button>

      <nav class="sheet-links">
        <a
          v-for="link in links"
          :key="`m-${link.url}`"
          :href="link.url"
          :class="{ active: isActive(link) }"
          @click="mobileOpen = false"
        >
          <span class="sheet-link-icon">
            <component :is="link.icon" :size="18" />
          </span>
          <span class="sheet-link-copy">
            <strong>{{ link.label }}</strong>
            <small>{{ link.hint }}</small>
          </span>
          <span class="sheet-link-trail">
            <span class="count-pill" v-if="link.kind === 'cart' && cartCount > 0">{{ cartCount }}</span>
            <ChevronLeft v-else :size="16" />
          </span>
        </a>
      </nav>

    </aside>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ChevronLeft, CircleHelp, Home, List, Menu, Search, ShoppingCart, UserRound, X } from 'lucide-vue-next'
import { useSearchModal } from '@/composables/useSearchModal'
import { customerAccountHref } from '@/utils/customerAuth'

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
const accountHref = computed(() => customerAccountHref())

const brandInitial = computed(() => String(props.branding?.name || 'V').trim().charAt(0) || 'V')

function openMobileSearch() {
  mobileOpen.value = false
  openSearch()
}

const currentPath = computed(() => {
  const path = String(window.location.pathname || '/').replace(/\/+$/, '')
  return path || '/'
})

const links = computed(() => {
  const base = [
    { key: 'landing', label: 'خانه', hint: 'شروع سریع', url: '/', prefix: '/', exact: true, icon: Home },
    { key: 'menu', label: 'منو', hint: 'مشاهده محصولات', url: '/menu', prefix: '/menu', icon: List },
    { key: 'product-groups', label: 'دسته‌ها', hint: 'گروه‌های محصول', url: '/product-groups', prefix: '/product-groups', icon: List },
    { key: 'about-us', label: 'درباره ما', hint: 'داستان برند', url: '/about-us', prefix: '/about-us', icon: UserRound },
    { key: 'faq', label: 'سوالات', hint: 'پاسخ‌های پرتکرار', url: '/faq', prefix: '/faq', icon: CircleHelp },
    { key: 'cart', label: 'سبد سفارش', hint: 'تکمیل خرید', url: '/cart', prefix: '/cart', kind: 'cart', icon: ShoppingCart },
  ]

  if (props.hasLastOrder && props.lastOrderUrl) {
    base.push({ key: 'order-success', label: 'پیگیری سفارش', hint: 'آخرین سفارش', url: props.lastOrderUrl, prefix: '/order-success', icon: ShoppingCart })
  }

  return base
})

const desktopLinks = computed(() => links.value.filter((link) => link.kind !== 'cart'))

function isActive(link) {
  if (link.key === 'menu') {
    return props.page === 'menu' || props.page === 'item'
  }
  if (link.key === 'product-groups') {
    return props.page === 'product-groups'
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
  padding: max(0.45rem, env(safe-area-inset-top)) 0.65rem 0;
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
  top: 0.45rem;
  left: 0.9rem;
  right: 0.9rem;
  height: 58px;
  border-radius: 24px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--ds-color-surface-raised) 82%, transparent), transparent);
  pointer-events: none;
}

.webapp-header {
  position: relative;
  width: min(540px, 100%);
  min-height: 46px;
  margin: 0 auto;
  display: none;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.35rem;
  border-radius: 18px;
  background: var(--ds-color-surface-raised, #fff);
  border: 1px solid color-mix(in srgb, var(--ds-color-action-primary) 12%, var(--ds-color-border));
  box-shadow: var(--ds-shadow-sm, 0 10px 24px rgb(52 38 31 / 0.08));
  backdrop-filter: blur(14px);
  color: var(--text-primary);
}

.webapp-brand {
  min-width: 0;
  justify-self: center;
  color: var(--ds-color-text-primary);
  text-decoration: none;
  font-weight: 900;
  font-size: 0.88rem;
  line-height: 1.2;
  max-width: 100%;
}

.webapp-brand span {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.webapp-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.25rem;
}

.webapp-icon-btn {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 15px;
  border: 1px solid var(--ds-color-border);
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-action-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: none;
  text-decoration: none;
  font-family: inherit;
}

.webapp-icon-btn:hover {
  background: var(--ds-color-action-primary-soft);
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 28%, var(--ds-color-border));
}

.webapp-menu-btn {
  justify-self: start;
}

.header-inner {
  position: relative;
  max-width: 1180px;
  margin: 0 auto;
  min-height: 58px;
  padding: 0 0.5rem 0 0.55rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border-radius: 24px;
  background: color-mix(in srgb, var(--ds-color-surface-raised) 96%, transparent);
  border: 1px solid color-mix(in srgb, var(--ds-color-action-primary) 10%, var(--ds-color-border));
  box-shadow: var(--ds-shadow-sm, 0 16px 36px rgb(52 38 31 / 0.075));
  color: var(--text-primary);
  backdrop-filter: blur(20px);
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 155px;
  max-width: 230px;
  text-decoration: none;
  color: inherit;
  padding: 0.25rem 0.3rem;
  border-radius: 17px;
  transition: background 0.16s ease;
}

.brand-link:hover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.04);
}

.brand-dot {
  width: 2rem;
  height: 2rem;
  border-radius: 13px;
  background: linear-gradient(135deg, var(--accent-green), var(--accent-green80, var(--accent-green)));
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 900;
  box-shadow: 0 8px 18px rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  flex-shrink: 0;
}

.brand-copy {
  min-width: 0;
}

.brand-copy strong {
  display: block;
  font-size: 0.86rem;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-copy small {
  display: block;
  color: var(--text-muted);
  font-size: 0.64rem;
  line-height: 1.2;
}

.desktop-nav {
  display: none;
  align-items: center;
  justify-content: center;
  gap: 0.18rem;
  padding: 0.18rem;
  border-radius: 18px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.045);
  flex: 1 1 auto;
  min-width: 0;
}

.nav-link {
  border-radius: 15px;
  padding: 0.42rem 0.58rem;
  font-size: 0.8rem;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  text-decoration: none;
  font-weight: 850;
  white-space: nowrap;
  transition: background 0.16s ease, color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
}

.nav-link.active {
  background: var(--ds-color-action-primary-soft);
  color: var(--ds-color-action-primary);
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 18%, transparent);
  box-shadow: none;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.72);
  color: var(--ds-color-action-primary);
  transform: translateY(-1px);
}

.nav-link svg,
.action-icon-pill svg,
.search-pill svg,
.cart-pill svg {
  flex-shrink: 0;
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
  justify-content: flex-end;
  gap: 0.28rem;
  min-width: max-content;
}

.action-icon-pill {
  height: 2rem;
  border-radius: 12px;
  border: 1px solid var(--ds-color-border);
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  box-shadow: none;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease, transform 0.15s ease;
}

.action-icon-pill {
  width: 44px;
  height: 44px;
  padding: 0;
  cursor: pointer;
}

.action-icon-pill:hover,
.cart-pill:hover,
.search-pill:hover {
  background: var(--accent-green20, rgb(var(--palette-deep-sapphire-rgb) / 0.07));
  border-color: var(--accent-green);
  color: var(--accent-green);
  transform: translateY(-1px);
}

.search-pill {
  min-width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--ds-color-surface-raised);
  border: 1px solid var(--ds-color-border);
  color: var(--ds-color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.35rem;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease, transform 0.15s ease;
  box-shadow: none;
}

.search-pill svg { width: 16px; height: 16px; }



.cart-pill {
  min-width: 5.6rem;
  min-height: 2.75rem;
  border-radius: 15px;
  background: var(--ds-color-action-accent);
  border: 1px solid var(--ds-color-action-accent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.38rem;
  padding: 0 0.72rem;
  text-decoration: none;
  box-shadow: 0 6px 16px rgb(var(--palette-deep-sapphire-rgb) / 0.045);
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease, transform 0.15s ease;
}

.cart-pill svg {
  width: 16px;
  height: 16px;
}

.cart-pill span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 800;
}

.cart-pill:hover,
.cart-pill:focus-visible {
  background: color-mix(in srgb, var(--ds-color-action-accent) 88%, var(--ds-color-text-primary));
  border-color: var(--ds-color-action-accent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
}

.cart-pill .cart-count {
  min-width: 1.2rem;
  height: 1.2rem;
  border-radius: 999px;
  padding-inline: 0.2rem;
  background: color-mix(in srgb, var(--ds-color-text-inverse, #fff) 22%, transparent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
}

.hamburger {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.24);
  background: var(--ds-color-surface-raised);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ds-color-action-primary);
  padding: 0;
}

.mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgb(15 23 42 / 0.34);
  backdrop-filter: blur(5px);
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
  right: -360px;
  width: min(330px, 88vw);
  height: 100vh;
  background: var(--ds-color-surface-raised);
  border-left: 1px solid var(--ds-color-border);
  box-shadow: -18px 0 42px rgb(15 23 42 / 0.18);
  transition: right 0.24s cubic-bezier(0.22, 1, 0.36, 1);
  padding: 0.9rem 0.8rem;
  z-index: 121;
  display: grid;
  grid-template-rows: auto auto 1fr;
  gap: 0.72rem;
  overflow-y: auto;
}

.mobile-sheet.open {
  right: 0;
}

.sheet-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.65rem;
  color: var(--text-primary);
}

.sheet-brand-card {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.62rem;
  padding: 0.62rem;
  border-radius: 18px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.055);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
}

.sheet-brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--accent-green);
  color: #fff;
  font-size: 1rem;
  font-weight: 900;
}

.sheet-brand-card strong,
.sheet-brand-card small {
  display: block;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sheet-brand-card strong {
  font-size: 0.9rem;
  font-weight: 900;
}

.sheet-brand-card small {
  margin-top: 0.12rem;
  color: var(--text-muted);
  font-size: 0.68rem;
}

.sheet-close {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  border: 1px solid var(--ds-color-border);
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-action-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 6px 14px rgb(var(--palette-deep-sapphire-rgb) / 0.06);
}

.sheet-search {
  width: 100%;
  min-height: 48px;
  border: 1px solid var(--ds-color-border);
  border-radius: 15px;
  background: var(--ds-color-surface-raised);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.5rem;
  padding: 0 0.72rem;
  font-family: inherit;
  font-size: 0.78rem;
  font-weight: 800;
  box-shadow: 0 8px 18px rgb(var(--palette-deep-sapphire-rgb) / 0.05);
}

.sheet-links {
  display: grid;
  gap: 0.42rem;
  align-content: start;
}

.sheet-links a {
  border-radius: 17px;
  padding: 0.55rem 0.58rem;
  background: var(--ds-color-surface-raised);
  border: 1px solid var(--ds-color-border);
  color: var(--text-primary);
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.58rem;
  text-decoration: none;
  box-shadow: 0 8px 18px rgb(var(--palette-deep-sapphire-rgb) / 0.045);
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease;
}

.sheet-links a:active {
  transform: scale(0.985);
}

.sheet-link-icon {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--ds-color-action-primary-soft);
  color: var(--ds-color-action-primary);
}

.sheet-link-copy {
  min-width: 0;
  display: grid;
  gap: 0.08rem;
}

.sheet-link-copy strong,
.sheet-link-copy small {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sheet-link-copy strong {
  font-size: 0.82rem;
  font-weight: 900;
}

.sheet-link-copy small {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.sheet-link-trail {
  min-width: 22px;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.sheet-links a.active {
  background: var(--ds-color-action-primary-soft);
  color: var(--ds-color-action-primary);
  border-color: color-mix(in srgb, var(--ds-color-action-primary) 24%, var(--ds-color-border));
  box-shadow: inset 3px 0 0 var(--ds-color-action-primary);
}

.sheet-links a.active .sheet-link-icon {
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-action-accent);
}

.sheet-links a.active .sheet-link-copy small,
.sheet-links a.active .sheet-link-trail {
  color: var(--ds-color-text-secondary);
}

.sheet-links a.active .count-pill {
  background: var(--ds-color-action-accent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
}

@media (min-width: 920px) {
  .header-surface {
    height: 58px;
  }

  .header-inner {
    min-height: 58px;
  }

  .desktop-nav {
    display: flex;
  }

  .hamburger {
    display: none;
  }
}

@media (max-width: 919px) {
  .app-header {
    padding: max(0.35rem, env(safe-area-inset-top)) 0.5rem 0;
  }

  .header-surface,
  .header-inner {
    display: none;
  }

  .webapp-header {
    display: grid;
  }

  .mobile-sheet {
    padding-top: max(0.9rem, calc(env(safe-area-inset-top) + 0.65rem));
  }
}

@media (max-width: 1120px) and (min-width: 920px) {
  .brand-link {
    min-width: 126px;
    max-width: 180px;
  }

  .brand-copy small {
    display: none;
  }

  .desktop-nav {
    gap: 0.12rem;
  }

  .nav-link {
    padding-inline: 0.48rem;
  }

}

@media (max-width: 919px) {
  .header-actions { display: none; }
}

.mobile-cart-count {
  position: absolute;
  inset-block-start: -3px;
  inset-inline-start: -3px;
  min-width: 18px;
  height: 18px;
  padding-inline: 3px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--ds-color-action-accent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
  font-size: 0.62rem;
  font-weight: 800;
}

.app-header :is(button, a):focus-visible {
  outline: 3px solid var(--ds-color-focus-ring, var(--ds-color-action-accent));
  outline-offset: 3px;
}
</style>
