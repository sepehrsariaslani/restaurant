<template>
  <div class="hero-head">
    <div class="headline">
      <small class="tagline">{{ branding.tagline }}</small>
      <h1>{{ branding.name }}</h1>
      <p class="subtitle muted">{{ branding.hero_subtitle || 'منو را باز کن، مواد را تنظیم کن، با دقت سفارش بده.' }}</p>
    </div>

    <div class="actions">
      <label class="search-box">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <circle cx="11" cy="11" r="7" />
          <path d="M20 20l-3.2-3.2" />
        </svg>
        <input
          :value="search"
          @input="$emit('update:search', $event.target.value)"
          @keyup.enter="$emit('search')"
          placeholder="جستجو در منو..."
          class="search-input"
        />
        <span class="search-hint" v-if="!search">↵</span>
      </label>

      <a class="cart-btn" href="/cart" :aria-label="`سبد سفارش — ${cartCount} آیتم`">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="9" cy="20" r="1.2"/><circle cx="18" cy="20" r="1.2"/>
          <path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.5L22 7H7"/>
        </svg>
        <span class="cart-label">سبد سفارش</span>
        <transition name="badge-pop">
          <span class="cart-count" v-if="cartCount > 0">{{ cartCount }}</span>
        </transition>
      </a>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

defineProps({
  branding: { type: Object, default: () => ({}) },
  search:   { type: String, default: '' },
  cartCount:{ type: Number, default: 0 },
})
defineEmits(['search', 'update:search'])
</script>

<style scoped>
.hero-head {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-radius: 32px;
  box-shadow: 0 12px 28px rgb(15 23 42 / 0.08);
  background: #fff;
  padding: 1.1rem 1.1rem 1rem;
  margin-bottom: 0.85rem;
  display: grid;
  gap: 0.9rem;
}

/* ── headline ── */
.tagline {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--accent-green);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 0.2rem;
}

.hero-head h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--ink-900, #141210);
  line-height: 1.15;
}

.subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.83rem;
  color: var(--text-muted, #7a6e64);
  line-height: 1.5;
}

/* ── actions row ── */
.actions {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.6rem;
  align-items: center;
}

/* ── search box ── */
.search-box {
  display: flex;
  align-items: center;
  gap: 0.42rem;
  border-radius: 16px;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  padding: 0.5rem 0.7rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  cursor: text;
}

.search-box:focus-within {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.58);
  box-shadow: 0 0 0 3px rgb(var(--palette-deep-sapphire-rgb) / 0.16);
}

.search-icon {
  width: 16px; height: 16px;
  color: var(--accent-green);
  flex-shrink: 0;
}

.search-input {
  flex: 1; border: 0; background: transparent;
  outline: none; font-family: inherit;
  font-size: 0.87rem; color: var(--ink-900, #141210);
}

.search-input::placeholder { color: var(--ink-400, #7a6e64); }

.search-hint {
  font-size: 0.65rem; color: var(--ink-200, #c4b8ae);
  white-space: nowrap; flex-shrink: 0;
}

/* ── cart button ── */
.cart-btn {
  position: relative;
  border-radius: 16px;
  padding: 0.5rem 0.8rem;
  background: var(--accent-green);
  color: #fff;
  display: inline-flex; align-items: center; gap: 0.45rem;
  text-decoration: none; white-space: nowrap;
  font-size: 0.84rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.34);
  box-shadow: 0 8px 20px rgb(var(--palette-deep-sapphire-rgb) / 0.28);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.cart-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgb(var(--palette-deep-sapphire-rgb) / 0.36);
}

.cart-label { font-size: 0.84rem; }

.cart-count {
  min-width: 1.25rem; height: 1.25rem;
  border-radius: 999px;
  background: #fff;
  color: var(--accent-green);
  font-size: 0.68rem; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
  padding: 0 0.18rem;
}

/* badge pop animation */
.badge-pop-enter-active {
  animation: badgePop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.badge-pop-leave-active {
  animation: badgePop 0.2s ease reverse;
}
@keyframes badgePop {
  from { transform: scale(0); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}
</style>
