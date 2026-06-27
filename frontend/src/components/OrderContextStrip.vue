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
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  background: rgb(var(--palette-eggshell-rgb) / 0.94);
  box-shadow: 0 10px 24px rgb(15 23 42 / 0.06);
  animation: strip-in 180ms ease-out both;
}

.strip-icon {
  width: 38px;
  height: 38px;
  border-radius: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.14);
  color: var(--accent-green);
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
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.5;
}

.strip-action {
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0.48rem 0.76rem;
  background: #fff;
  color: var(--accent-green);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  font-weight: 800;
  font-size: 0.82rem;
  white-space: nowrap;
}

.order-context-strip.is-missing {
  border-color: rgb(var(--warning-rgb) / 0.28);
  background: rgb(var(--warning-rgb) / 0.08);
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
