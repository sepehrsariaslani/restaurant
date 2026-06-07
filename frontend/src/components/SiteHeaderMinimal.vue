<template>
  <header class="site-header-minimal" :class="{ 'site-header-minimal--preview': preview }" dir="rtl">
    <div class="shm-inner">
      <a class="shm-brand" href="/">{{ branding.name }}</a>

      <nav class="shm-nav">
        <a href="/" class="shm-link">خانه</a>
        <a href="/menu" class="shm-link">منو</a>
        <a href="/about-us" class="shm-link">درباره ما</a>
      </nav>

      <a href="/cart" class="shm-cart" :aria-label="`سبد خرید${cartCount > 0 ? ` (${cartCount})` : ''}`">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="9" cy="20" r="1" />
          <circle cx="18" cy="20" r="1" />
          <path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.5L22 7H7" />
        </svg>
        <span v-if="cartCount > 0" class="shm-cart-count">{{ cartCount }}</span>
      </a>
    </div>
  </header>
</template>

<script setup>
defineProps({
  branding: {
    type: Object,
    default: () => ({ name: '' }),
  },
  cartCount: {
    type: Number,
    default: 0,
  },
  preview: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.site-header-minimal {
  position: sticky;
  top: 0;
  z-index: 200;
  width: 100%;
  background: #1c1411;
  border-bottom: 1px solid rgb(255 255 255 / 0.08);
  direction: rtl;
}

.site-header-minimal--preview {
  position: relative;
  top: auto;
  z-index: 1;
  border-radius: 18px;
  overflow: hidden;
}

.shm-inner {
  width: min(1200px, calc(100% - 2rem));
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.7rem 0;
}

.shm-brand {
  font-size: 1.05rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.01em;
  text-decoration: none;
  white-space: nowrap;
}

.shm-nav {
  display: flex;
  align-items: center;
  gap: 0.1rem;
}

.shm-link {
  padding: 0.3rem 0.65rem;
  border-radius: 999px;
  font-size: 0.84rem;
  color: rgb(255 255 255 / 0.72);
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.shm-link:hover {
  background: rgb(255 255 255 / 0.1);
  color: #fff;
}

.shm-cart {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 50%;
  color: rgb(255 255 255 / 0.8);
  background: rgb(255 255 255 / 0.08);
  text-decoration: none;
  transition: background 0.15s;
  flex-shrink: 0;
}

.shm-cart:hover {
  background: rgb(255 255 255 / 0.16);
  color: #fff;
}

.shm-cart-count {
  position: absolute;
  top: -0.2rem;
  left: -0.2rem;
  min-width: 1.05rem;
  height: 1.05rem;
  border-radius: 999px;
  background: #c98d42;
  color: #fff;
  font-size: 0.6rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.18rem;
  line-height: 1;
}

@media (max-width: 600px) {
  .shm-nav {
    display: none;
  }
}
</style>
