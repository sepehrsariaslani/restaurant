<template>
  <section class="order-context-strip" :class="{ 'is-missing': !hasContext }" dir="rtl">
    <div class="strip-icon" aria-hidden="true">
      <component :is="iconComponent" :size="18" />
    </div>
    <div class="strip-copy">
      <strong>{{ title }}</strong>
      <small>{{ subtitle }}</small>
    </div>
    <a class="strip-action" :href="changeUrl">{{ hasContext ? 'تغییر' : 'انتخاب نوع سفارش' }}</a>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Bike, PackageCheck, Utensils, MapPin } from 'lucide-vue-next'
import { cartState } from '@/stores/cartStore'
import { deliveryFeeText, orderContextChangeUrl, orderDestinationText, orderTimeText, orderTypeLabel } from '@/utils/orderFlow'

const props = defineProps({
  currency: { type: String, default: 'IRR' },
})

const context = computed(() => cartState.orderContext || {})
const hasContext = computed(() => Boolean(context.value.order_type))
const title = computed(() => hasContext.value ? orderTypeLabel(context.value) : 'نوع سفارش مشخص نیست')
const subtitle = computed(() => {
  if (!hasContext.value) return 'برای محاسبه شعبه، زمان و هزینه ارسال، ابتدا نوع سفارش را انتخاب کنید.'
  return `${orderDestinationText(context.value)} · ${orderTimeText(context.value)} · ${deliveryFeeText(context.value, props.currency)}`
})
const changeUrl = computed(() => orderContextChangeUrl(context.value))
const iconComponent = computed(() => {
  if (context.value.order_type === 'delivery') return Bike
  if (context.value.order_type === 'pickup') return PackageCheck
  if (context.value.order_type === 'dine_in') return Utensils
  return MapPin
})
</script>

<style scoped>
.order-context-strip {
  width: min(1120px, calc(100% - 1rem));
  margin: 0 auto 0.85rem;
  min-height: 58px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.75rem;
  border-radius: 20px;
  border: 1px solid var(--ds-color-border, rgb(var(--palette-deep-sapphire-rgb) / 0.14));
  background: var(--ds-color-surface, rgb(var(--palette-eggshell-rgb) / 0.94));
  box-shadow: var(--ds-shadow-sm, 0 10px 24px rgb(15 23 42 / 0.06));
  animation: strip-in 180ms ease-out both;
}

.strip-icon {
  width: 38px;
  height: 38px;
  border-radius: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--ds-color-action-accent-soft, rgb(var(--palette-deep-saffron-rgb) / 0.14));
  color: var(--ds-color-action-primary, var(--accent-green));
}

.strip-copy {
  min-width: 0;
  display: grid;
  gap: 0.15rem;
}

.strip-copy strong {
  font-size: 0.9rem;
  line-height: 1.4;
}

.strip-copy small {
  color: var(--ds-color-text-muted, var(--text-muted));
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.5;
}

.strip-action {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0.48rem 0.76rem;
  background: var(--ds-color-surface-raised, #fff);
  color: var(--ds-color-action-primary, var(--accent-green));
  border: 1px solid var(--ds-color-border, rgb(var(--palette-deep-sapphire-rgb) / 0.16));
  font-weight: 800;
  font-size: 0.82rem;
  white-space: nowrap;
}

.strip-action:hover {
  background: var(--ds-color-action-primary-soft, var(--theme-surface-alt));
}

.strip-action:focus-visible {
  outline: 3px solid var(--ds-color-focus-ring, var(--ds-color-action-accent));
  outline-offset: 3px;
}

.order-context-strip.is-missing {
  border-color: color-mix(in srgb, var(--ds-color-status-warning, var(--warning, #c67b2a)) 35%, var(--ds-color-border, transparent));
  background: var(--ds-color-status-warning-soft, rgb(var(--warning-rgb) / 0.08));
}

@keyframes strip-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  .order-context-strip { animation: none; }
}

@media (max-width: 640px) {
  .order-context-strip {
    grid-template-columns: auto minmax(0, 1fr);
    border-radius: 18px;
  }

  .strip-action {
    grid-column: 1 / -1;
    width: 100%;
  }
}
</style>
