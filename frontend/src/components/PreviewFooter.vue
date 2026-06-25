<template>
  <footer class="preview-footer">
    <div class="footer-price">
      <span class="footer-price-label">قیمت کل</span>
      <span class="footer-price-value">{{ formatPrice(totalPrice) }}</span>
      <span class="footer-price-currency">{{ currency === 'TOMAN' ? 'تومان' : currency }}</span>
    </div>
    <button
      class="footer-cta"
      type="button"
      :disabled="disabled || adding"
      @click="$emit('add-to-cart')"
    >
      <svg v-if="!adding" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
      <span v-else class="cta-spinner"></span>
      <span v-if="!adding">افزودن به سبد</span>
    </button>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  price: { type: Number, required: true },
  currency: { type: String, default: 'TOMAN' },
  quantity: { type: Number, default: 1 },
  adding: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

defineEmits(['add-to-cart'])

const totalPrice = computed(() => props.price * props.quantity)

function formatPrice(value) {
  const num = Number(value || 0)
  return num.toLocaleString('fa-IR')
}
</script>

<style scoped>
.preview-footer {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1.25rem;
  padding-bottom: max(0.85rem, env(safe-area-inset-bottom, 1rem));
  background: rgb(var(--preview-surface-rgb, 255 255 255) / 0.95);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid var(--preview-border);
}

.footer-price {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
  min-width: 0;
  flex-shrink: 0;
}

.footer-price-label {
  font-size: 0.68rem;
  color: var(--preview-muted);
  font-weight: 500;
}

.footer-price-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--preview-primary);
  font-variant-numeric: tabular-nums;
}

.footer-price-currency {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--preview-muted);
}

.footer-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  height: 48px;
  padding: 0 1.5rem;
  border: none;
  border-radius: 999px;
  background: var(--preview-primary);
  color: var(--preview-on-accent);
  font-family: inherit;
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.15s ease, transform 0.15s ease;
  flex-shrink: 0;
}

.footer-cta:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.footer-cta:active:not(:disabled) {
  transform: scale(0.97);
}

.footer-cta:focus-visible {
  outline: 2px solid var(--preview-primary);
  outline-offset: 2px;
}

.footer-cta:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
}

.cta-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgb(255 255 255 / 0.3);
  border-top-color: #fff;
  border-radius: 999px;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 767px) {
  .footer-cta {
    height: 52px;
    flex: 1;
  }
  .footer-price {
    flex: 0 0 auto;
  }
}
</style>
