<template>
  <header class="mobile-header glass-card">
    <div class="header-row">
      <button class="icon-btn" type="button" aria-label="menu">
        <span></span>
        <span></span>
        <span></span>
      </button>

      <div class="title-wrap">
        <small>{{ branding.tagline }}</small>
        <h2>{{ branding.name }}</h2>
      </div>

      <a class="cart-pill" href="/cart" aria-label="cart">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="9" cy="20" r="1" />
          <circle cx="18" cy="20" r="1" />
          <path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.5L22 7H7" />
        </svg>
        <span v-if="cartCount > 0">{{ cartCount }}</span>
      </a>
    </div>

    <div class="search-row">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
        <circle cx="11" cy="11" r="7" />
        <path d="M20 20l-3.2-3.2" />
      </svg>
      <input
        :value="search"
        @input="$emit('update:search', $event.target.value)"
        @keyup.enter="$emit('search')"
        class="search-input"
        placeholder="جستجو در منو"
      />
    </div>
  </header>
</template>

<script setup>
defineProps({
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
  search: {
    type: String,
    default: '',
  },
})

defineEmits(['search', 'update:search'])
</script>

<style scoped>
.mobile-header {
  padding: 0.9rem;
  border-radius: 22px;
  margin-bottom: 0.8rem;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.7rem;
}

.icon-btn {
  width: 2.4rem;
  height: 2.4rem;
  border: 0;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.58);
  display: grid;
  align-content: center;
  gap: 4px;
  padding: 0 9px;
  box-shadow: inset 0 0 0 1px rgba(102, 125, 98, 0.22);
}

.icon-btn span {
  display: block;
  height: 2px;
  border-radius: 99px;
  background: var(--ink-800);
}

.title-wrap {
  flex: 1;
  text-align: center;
}

.title-wrap small {
  display: block;
  color: var(--text-muted);
  font-size: 0.73rem;
}

.title-wrap h2 {
  margin: 0.13rem 0 0;
  font-size: 1.08rem;
}

.cart-pill {
  min-width: 2.4rem;
  height: 2.4rem;
  padding: 0 0.45rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  box-shadow: inset 0 0 0 1px rgba(102, 125, 98, 0.22);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
}

.cart-pill svg {
  width: 18px;
  height: 18px;
}

.cart-pill span {
  min-width: 1rem;
  height: 1rem;
  border-radius: 999px;
  background: var(--accent-green);
  color: #fff;
  font-size: 0.66rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.15rem;
}

.search-row {
  margin-top: 0.72rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-radius: 14px;
  padding: 0.55rem 0.68rem;
  background: rgba(255, 255, 255, 0.48);
  box-shadow: inset 0 0 0 1px rgba(114, 125, 98, 0.18);
}

.search-row svg {
  width: 18px;
  height: 18px;
  color: var(--ink-700);
}

.search-input {
  border: 0;
  background: transparent;
  outline: none;
  width: 100%;
  font-family: inherit;
  color: var(--text-primary);
}
</style>
