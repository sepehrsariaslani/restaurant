<template>
  <header class="site-header-minimal" :class="{ 'site-header-minimal--preview': preview }" dir="rtl">
    <div class="shm-inner">
      <a class="shm-brand" href="/">{{ branding.name }}</a>

      <nav class="shm-nav">
        <a href="/" class="shm-link">خانه</a>
        <a href="/menu" class="shm-link">منو</a>
        <a href="/about-us" class="shm-link">درباره ما</a>
      </nav>

      <button class="shm-search" type="button" @click="openSearch" aria-label="جستجو">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
      </button>
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
import { useSearchModal } from '@/composables/useSearchModal'
const { openSearch } = useSearchModal()
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
  background: var(--ds-color-surface-raised);
  border-bottom: 1px solid var(--ds-color-border);
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
  color: var(--ds-color-text-primary);
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
  color: var(--ds-color-text-secondary);
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.shm-link:hover {
  background: var(--ds-color-action-primary-soft);
  color: var(--ds-color-action-primary);
}

.shm-search {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  color: var(--ds-color-action-primary);
  background: var(--ds-color-surface-raised);
  border: 1px solid var(--ds-color-border);
  cursor: pointer;
  transition: background 0.15s;
  flex-shrink: 0;
}

.shm-search:hover {
  background: var(--ds-color-action-primary-soft);
  color: var(--ds-color-action-primary);
}

.shm-cart {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
  background: var(--ds-color-action-accent);
  border: 1px solid var(--ds-color-action-accent);
  text-decoration: none;
  transition: background 0.15s;
  flex-shrink: 0;
}

.shm-cart:hover {
  filter: brightness(0.96);
}

.shm-cart-count {
  position: absolute;
  top: -0.2rem;
  left: -0.2rem;
  min-width: 1.05rem;
  height: 1.05rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--ds-color-text-inverse, #fff) 22%, transparent);
  color: var(--ds-color-action-accent-foreground, var(--ds-color-text-inverse, #fff));
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
