<template>
  <Transition name="cart-feedback">
    <div
      v-if="message"
      class="cart-action-feedback"
      :class="`cart-action-feedback--${placement}`"
      role="status"
      aria-live="polite"
      dir="rtl"
    >
      <CheckCircle2 :size="18" aria-hidden="true" />
      <span>{{ message }}</span>
    </div>
  </Transition>
</template>

<script setup>
import { CheckCircle2 } from 'lucide-vue-next'

defineProps({
  message: { type: String, default: '' },
  placement: { type: String, default: 'bottom' },
})
</script>

<style scoped>
.cart-action-feedback {
  position: fixed;
  z-index: 118;
  left: 50%;
  right: auto;
  bottom: calc(5.2rem + env(safe-area-inset-bottom));
  transform: translateX(-50%);
  width: max-content;
  max-width: min(420px, calc(100vw - 2rem));
  min-height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  padding: 0.65rem 0.95rem;
  border: 1px solid color-mix(in srgb, var(--ds-color-action-primary) 22%, transparent);
  border-radius: 999px;
  background: var(--ds-color-surface-raised);
  color: var(--ds-color-text-primary);
  box-shadow: 0 10px 28px rgb(32 24 16 / 0.16);
  font-size: 0.84rem;
  font-weight: 750;
}

.cart-action-feedback--product {
  bottom: calc(5.2rem + 6.25rem + env(safe-area-inset-bottom));
}

.cart-action-feedback svg {
  flex: 0 0 auto;
  color: var(--ds-color-status-success, var(--ds-color-action-primary));
}

.cart-feedback-enter-active,
.cart-feedback-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.cart-feedback-enter-from,
.cart-feedback-leave-to {
  opacity: 0;
  transform: translate(-50%, 8px);
}

@media (min-width: 920px) {
  .cart-action-feedback {
    bottom: 1.25rem;
  }

  .cart-action-feedback--product {
    bottom: 1.25rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .cart-feedback-enter-active,
  .cart-feedback-leave-active {
    transition: none;
  }
}
</style>
