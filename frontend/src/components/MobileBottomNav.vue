<template>
  <nav class="mobile-bottom-nav" dir="rtl" aria-label="منوی پایین">
    <a href="/" class="nav-item" :class="{ active: page === 'landing' }">
      <span class="icon">⌂</span>
      <small>خانه</small>
    </a>

    <a href="/menu" class="nav-item" :class="{ active: page === 'menu' || page === 'item' }">
      <span class="icon">☰</span>
      <small>منو</small>
    </a>

    <a href="/cart" class="nav-item center" :class="{ active: page === 'cart' }">
      <span class="icon">🛒</span>
      <small>سبد</small>
      <i v-if="cartCount > 0">{{ cartCount }}</i>
    </a>

    <a :href="hasLastOrder ? lastOrderUrl : '/menu'" class="nav-item" :class="{ active: page === 'order-success' }">
      <span class="icon">◷</span>
      <small>{{ hasLastOrder ? 'پیگیری' : 'سفارش' }}</small>
    </a>
  </nav>
</template>

<script setup>
defineProps({
  page: {
    type: String,
    default: 'landing',
  },
  cartCount: {
    type: Number,
    default: 0,
  },
  hasLastOrder: {
    type: Boolean,
    default: false,
  },
  lastOrderUrl: {
    type: String,
    default: '/menu',
  },
})
</script>

<style scoped>
.mobile-bottom-nav {
  position: fixed;
  bottom: 0.72rem;
  left: 50%;
  transform: translateX(-50%);
  width: min(520px, calc(100% - 1rem));
  border-radius: 28px;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  box-shadow: 0 10px 24px rgb(15 23 42 / 0.1);
  padding: 0.45rem;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.35rem;
  z-index: 115;
}

.nav-item {
  min-height: 52px;
  border-radius: 18px;
  color: var(--text-muted);
  display: grid;
  align-content: center;
  justify-items: center;
  gap: 0.1rem;
  position: relative;
}

.nav-item .icon {
  font-size: 1rem;
  line-height: 1;
}

.nav-item small {
  font-size: 0.68rem;
}

.nav-item.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  color: var(--accent-green);
}

.nav-item.center {
  background: var(--accent-green);
  color: #fff;
}

.nav-item.center.active {
  box-shadow: 0 10px 20px rgb(var(--palette-deep-saffron-rgb) / 0.36);
}

.nav-item i {
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  min-width: 1rem;
  height: 1rem;
  padding: 0 0.2rem;
  border-radius: 999px;
  background: #fff;
  color: var(--text-primary);
  font-style: normal;
  font-size: 0.62rem;
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
