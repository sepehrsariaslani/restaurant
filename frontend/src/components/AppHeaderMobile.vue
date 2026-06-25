<template>
  <header class="app-header-mobile" dir="rtl">
    <button
      v-if="showBack"
      class="ahm-back"
      type="button"
      aria-label="بازگشت"
      @click="$emit('back')"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m9 18 6-6-6-6" />
      </svg>
    </button>
    <span v-else class="ahm-spacer"></span>

    <h1 class="ahm-title">{{ title }}</h1>

    <a
      v-if="showCart"
      href="/cart"
      class="ahm-cart"
      aria-label="سبد خرید"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="9" cy="20" r="1" />
        <circle cx="18" cy="20" r="1" />
        <path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.5L22 7H7" />
      </svg>
      <span v-if="cartCount > 0" class="ahm-cart-badge">{{ cartCount > 99 ? '99+' : cartCount }}</span>
    </a>
    <span v-else class="ahm-spacer"></span>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, default: 'منوی آنلاین' },
  cartCount: { type: Number, default: 0 },
  showBack: { type: Boolean, default: true },
  backUrl: { type: String, default: '/customer/dashboard' },
  showCart: { type: Boolean, default: true },
})

defineEmits(['back'])
</script>

<style scoped>
.app-header-mobile {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 120;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0.75rem;
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.10);
  box-shadow: 0 2px 12px rgb(var(--palette-deep-sapphire-rgb) / 0.08);
}

.ahm-spacer {
  min-width: 44px;
  min-height: 44px;
}

.ahm-back {
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--palette-deep-sapphire);
  cursor: pointer;
  border-radius: 10px;
  padding: 0;
  flex-shrink: 0;
}

.ahm-back:hover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
}

.ahm-back:active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.10);
}

.ahm-title {
  flex: 1;
  text-align: center;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0 0.5rem;
}

.ahm-cart {
  position: relative;
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--palette-deep-sapphire);
  text-decoration: none;
  border-radius: 10px;
  flex-shrink: 0;
}

.ahm-cart:hover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
}

.ahm-cart:active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.10);
}

.ahm-cart-badge {
  position: absolute;
  top: 2px;
  left: 2px;
  min-width: 1.1rem;
  height: 1.1rem;
  border-radius: 999px;
  background: var(--accent-green);
  color: #fff;
  font-size: 0.62rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.2rem;
  line-height: 1;
}

@media (max-width: 520px) {
  .app-header-mobile {
    height: 48px;
  }
  .ahm-title {
    font-size: 0.9rem;
  }
}
</style>
