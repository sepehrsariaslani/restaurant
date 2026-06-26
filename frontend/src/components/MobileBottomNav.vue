<template>
  <nav class="mobile-bottom-nav" dir="rtl" aria-label="منوی پایین">
    <a href="/customer/dashboard" class="nav-item" :class="{ active: page === 'customer-dashboard' || page === 'landing' }">
      <Home class="nav-icon" :size="20" />
      <small>خانه</small>
    </a>

    <a href="/menu" class="nav-item" :class="{ active: page === 'menu' || page === 'item' }">
      <List class="nav-icon" :size="20" />
      <small>منو</small>
    </a>

    <button class="nav-item nav-search" type="button" @click="openSearch" aria-label="جستجو">
      <span class="search-orb">
        <Search :size="22" />
      </span>
      <small>جستجو</small>
    </button>

    <a href="/cart" class="nav-item" :class="{ active: page === 'cart' }">
      <ShoppingCart class="nav-icon" :size="20" />
      <small>سبد</small>
      <i v-if="cartCount > 0">{{ cartCount }}</i>
    </a>

    <a href="/customer/profile" class="nav-item" :class="{ active: page === 'customer-profile' || page === 'customer-addresses' || page === 'customer-branches' }">
      <UserRound class="nav-icon" :size="20" />
      <small>حساب</small>
    </a>
  </nav>
</template>

<script setup>
import { Home, List, Search, ShoppingCart, UserRound } from 'lucide-vue-next'
import { useSearchModal } from '@/composables/useSearchModal'

defineProps({
  page: { type: String, default: 'landing' },
  cartCount: { type: Number, default: 0 },
  hasLastOrder: { type: Boolean, default: false },
  lastOrderUrl: { type: String, default: '/menu' },
})

const { openSearch } = useSearchModal()
</script>

<style scoped>
.mobile-bottom-nav {
  position: fixed;
  bottom: 0.62rem;
  left: 50%;
  transform: translateX(-50%);
  width: min(520px, calc(100% - 0.8rem));
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
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
  color: var(--text-muted, #846b58);
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
  background: var(--accent-green20, rgba(111,74,49,0.09));
  color: var(--accent-green, #6f4a31);
}

.nav-search {
  color: #fff;
  transform: translateY(-0.36rem);
}

.search-orb {
  width: 44px;
  height: 44px;
  border-radius: 18px;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 20px rgb(var(--palette-deep-sapphire-rgb) / 0.20);
}

.nav-search small {
  color: var(--accent-green, #6f4a31);
  margin-top: -0.1rem;
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
  background: var(--danger, #e74c3c);
  color: #fff;
  font-style: normal;
  font-size: 0.56rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (min-width: 920px) {
  .mobile-bottom-nav {
    display: none;
  }
}
</style>
