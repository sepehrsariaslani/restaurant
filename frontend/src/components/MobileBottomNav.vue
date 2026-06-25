<template>
  <nav class="mobile-bottom-nav" dir="rtl" aria-label="منوی پایین">
    <a href="/customer/dashboard" class="nav-item" :class="{ active: page === 'customer-dashboard' || page === 'landing' }">
      <svg class="nav-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      <small>خانه</small>
    </a>

    <a href="/menu" class="nav-item" :class="{ active: page === 'menu' || page === 'item' }">
      <svg class="nav-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
      <small>منو</small>
    </a>

    <a href="/cart" class="nav-item center" :class="{ active: page === 'cart' }">
      <svg class="nav-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
      <small>سبد</small>
      <i v-if="cartCount > 0">{{ cartCount }}</i>
    </a>

    <a href="/customer/profile" class="nav-item" :class="{ active: page === 'customer-profile' || page === 'customer-addresses' || page === 'customer-branches' }">
      <svg class="nav-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
      <small>حساب</small>
    </a>
  </nav>
</template>

<script setup>
defineProps({
  page: { type: String, default: 'landing' },
  cartCount: { type: Number, default: 0 },
  hasLastOrder: { type: Boolean, default: false },
  lastOrderUrl: { type: String, default: '/menu' },
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
  border: 1px solid rgba(63,42,29,0.12);
  box-shadow: 0 10px 24px rgba(15,23,42,0.1);
  padding: 0.45rem;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.35rem;
  z-index: 115;
}

.nav-item {
  min-height: 52px;
  border-radius: 18px;
  color: var(--text-muted, #846b58);
  display: grid;
  align-content: center;
  justify-items: center;
  gap: 0.1rem;
  position: relative;
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
}

.nav-icon {
  width: 22px;
  height: 22px;
}

.nav-item small {
  font-size: 0.65rem;
  font-weight: 600;
}

.nav-item.active {
  background: rgba(111,74,49,0.09);
  color: var(--accent-green, #6f4a31);
}

.nav-item.center {
  background: var(--accent-green, #6f4a31);
  color: #fff;
}

.nav-item.center.active {
  box-shadow: 0 6px 18px rgba(111,74,49,0.35);
}

.nav-item.center small {
  color: rgba(255,255,255,0.85);
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
  background: #e74c3c;
  color: #fff;
  font-style: normal;
  font-size: 0.6rem;
  font-weight: 700;
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
