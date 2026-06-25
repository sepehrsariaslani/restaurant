<template>
  <div class="hero-head">
    <div class="headline">
      <small class="tagline">{{ branding.tagline }}</small>
      <h1>{{ branding.name }}</h1>
      <p class="subtitle muted">{{ branding.hero_subtitle || 'منو را باز کن، مواد را تنظیم کن، با دقت سفارش بده.' }}</p>
    </div>

    <div class="actions">
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
import { defineProps } from 'vue'

defineProps({
  branding: { type: Object, default: () => ({}) },
  cartCount:{ type: Number, default: 0 },
})
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
  display: flex;
  justify-content: flex-end;
  align-items: center;
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
