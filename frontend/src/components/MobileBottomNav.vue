<template>
  <nav class="mobile-bottom-nav" dir="rtl" aria-label="منوی پایین">
    <a href="/" class="nav-item" :class="{ active: page === 'landing' || page === 'homev2' }" :aria-current="page === 'landing' || page === 'homev2' ? 'page' : undefined">
      <Home class="nav-icon" :size="20" />
      <small>خانه</small>
    </a>

    <a href="/menu" class="nav-item" :class="{ active: page === 'menu' || page === 'item' }" :aria-current="page === 'menu' || page === 'item' ? 'page' : undefined">
      <List class="nav-icon" :size="20" />
      <small>منو</small>
    </a>

    <a href="/search" class="nav-item nav-search" :class="{ active: page === 'search' }" :aria-current="page === 'search' ? 'page' : undefined" aria-label="جستجو">
      <span class="search-orb">
        <Search :size="22" />
      </span>
      <small>جستجو</small>
    </a>

    <a href="/cart" class="nav-item" :class="{ active: page === 'cart' }" :aria-current="page === 'cart' ? 'page' : undefined" :aria-label="cartCount > 0 ? `سبد سفارش، ${cartCount.toLocaleString('fa-IR')} آیتم` : 'سبد سفارش'">
      <ShoppingCart class="nav-icon" :size="20" />
      <small>سبد</small>
      <i v-if="cartCount > 0" aria-hidden="true">{{ cartCount.toLocaleString('fa-IR') }}</i>
    </a>

    <a href="/customer/dashboard" class="nav-item" :class="{ active: isCustomerAccountActive }" :aria-current="isCustomerAccountActive ? 'page' : undefined">
      <UserRound class="nav-icon" :size="20" />
      <small>حساب</small>
    </a>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { Home, List, Search, ShoppingCart, UserRound } from 'lucide-vue-next'

const props = defineProps({
  page: { type: String, default: 'landing' },
  cartCount: { type: Number, default: 0 },
  hasLastOrder: { type: Boolean, default: false },
  lastOrderUrl: { type: String, default: '/menu' },
})

const customerAccountPages = new Set([
  'customer-dashboard',
  'customer-profile',
  'customer-addresses',
  'customer-branches',
  'customer-orders',
  'customer-order-detail',
  'customer-delivery',
  'customer-table-reservation',
  'customer-table-select',
])

const isCustomerAccountActive = computed(() => customerAccountPages.has(props.page))
</script>

<style scoped>
.mobile-bottom-nav {
  position: fixed;
  bottom: calc(0.62rem + env(safe-area-inset-bottom));
  left: 50%;
  transform: translateX(-50%);
  width: min(520px, calc(100% - 0.8rem));
  border-radius: 24px;
  background: var(--ds-color-surface-raised, #fff);
  background: color-mix(in srgb, var(--ds-color-surface-raised, #fff) 96%, transparent);
  border: 1px solid var(--ds-color-border, rgb(var(--palette-deep-sapphire-rgb) / 0.12));
  box-shadow: 0 10px 24px rgba(15,23,42,0.1);
  padding: 0.34rem;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.24rem;
  z-index: 115;
  backdrop-filter: blur(16px);
}

.nav-item {
  min-height: 48px;
  border: 0;
  border-radius: 16px;
  color: var(--ds-color-text-muted, var(--text-muted, #846b58));
  background: transparent;
  display: grid;
  align-content: center;
  justify-items: center;
  gap: 0.08rem;
  position: relative;
  text-decoration: none;
  transition: background 0.2s, color 0.2s, transform 0.15s;
  font-family: inherit;
  cursor: pointer;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.nav-item small {
  font-size: 0.58rem;
  font-weight: 700;
  line-height: 1.1;
}

.nav-item.active {
  background: var(--ds-color-action-primary-soft, var(--accent-green20, rgba(111,74,49,0.09)));
  color: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
}

.nav-search {
  color: #fff;
  transform: translateY(-0.36rem);
}

.search-orb {
  width: 44px;
  height: 44px;
  border-radius: 18px;
  background: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
  color: var(--ds-color-text-inverse, #fff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--ds-shadow-md, 0 10px 20px rgb(var(--palette-deep-sapphire-rgb) / 0.20));
}

.nav-search small {
  color: var(--ds-color-action-primary, var(--accent-green, #6f4a31));
  margin-top: -0.1rem;
}

.nav-search.active .search-orb {
  background: linear-gradient(135deg, var(--ds-color-action-primary, var(--accent-green)), var(--ds-color-action-accent, var(--accent-gold)));
}

.nav-item i {
  position: absolute;
  top: 3px;
  left: 50%;
  transform: translateX(-50%);
  min-width: 0.95rem;
  height: 0.95rem;
  padding: 0 0.2rem;
  border-radius: 999px;
  background: var(--ds-color-status-danger, var(--danger, #e74c3c));
  color: var(--ds-color-text-inverse, #fff);
  font-style: normal;
  font-size: 0.56rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.mobile-bottom-nav a:focus-visible {
  outline: 3px solid var(--ds-color-focus-ring, var(--ds-color-action-accent));
  outline-offset: 3px;
  position: relative;
  z-index: 1;
}

@media (min-width: 920px) {
  .mobile-bottom-nav {
    display: none;
  }
}
</style>
