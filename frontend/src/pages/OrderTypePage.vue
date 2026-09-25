<template>
  <section class="order-flow-page order-type-page">
    <header class="order-flow-hero">
      <div><p class="order-flow-eyebrow">سفارش به سلیقه شما</p><h1 class="order-flow-title">کجا تحویل بگیرید؟</h1><p class="order-flow-subtitle">روش دریافت را انتخاب کنید؛ بعد سراغ غذاهای خوشمزه می‌رویم.</p></div>
      <a class="order-flow-secondary" :href="cartState.lines.length ? '/cart' : '/menu'">{{ cartState.lines.length ? 'بازگشت به سبد' : 'دیدن منو' }}</a>
    </header>
    <div class="receiving-grid">
      <button v-for="choice in choices" :key="choice.id" class="receiving-choice" type="button" @click="choose(choice)">
        <span class="receiving-icon"><component :is="choice.icon" :size="28" aria-hidden="true" /></span>
        <span class="receiving-copy"><strong>{{ choice.title }}</strong><small>{{ choice.description }}</small><span>{{ choice.hint }}</span></span>
        <ChevronLeft :size="20" class="receiving-arrow" aria-hidden="true" />
      </button>
    </div>
    <p class="receiving-note">روش دریافت و جزئیات آن را تا پیش از ثبت سفارش می‌توانید تغییر دهید.</p>
  </section>
</template>
<script setup>
import { Bike, CarFront, ChevronLeft, Store, UtensilsCrossed } from 'lucide-vue-next'
import { cartState, saveOrderContext } from '@/stores/cartStore'
import { resetOrderContextForType } from '@/utils/orderFlow'
import './orderFlow.css'
const choices = [
  { id: 'delivery', type: 'delivery', title: 'درب منزل', description: 'غذای شما را به نشانی دلخواه می‌رسانیم.', hint: 'انتخاب روی نقشه یا آدرس‌های من', icon: Bike, href: '/order/delivery' },
  { id: 'car', type: 'pickup', title: 'درب ماشین', description: 'نزدیک شعبه بمانید؛ سفارش را تا خودرو می‌آوریم.', hint: 'انتخاب شعبه و مشخصات خودرو', icon: CarFront, href: '/order/pickup?method=car' },
  { id: 'walk', type: 'pickup', title: 'تحویل حضوری', description: 'سفارش آماده را از پیشخوان تحویل بگیرید.', hint: 'انتخاب شعبه و زمان تحویل', icon: Store, href: '/order/pickup?method=walk' },
  { id: 'dine_in', type: 'dine_in', title: 'سر میز', description: 'در رستوران هستید یا برای بعد میز می‌خواهید؟', hint: 'انتخاب میز یا رزرو برای بعد', icon: UtensilsCrossed, href: '/order/dine-in' },
]
function choose(choice) {
  // Reopening the current method should not discard a completed address or vehicle.
  if (cartState.orderContext.order_type !== choice.type) resetOrderContextForType(choice.type)
  if (choice.type === 'pickup') saveOrderContext({ pickup_method: choice.id })
  window.location.href = choice.href
}
</script>
<style scoped>
.order-type-page { max-width: 900px; }
.receiving-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.receiving-choice { display: grid; grid-template-columns: 56px minmax(0, 1fr) 20px; align-items: center; gap: 1rem; padding: 1.5rem 1.25rem; min-height: 160px; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); color: var(--ds-color-text-primary); text-align: start; font: inherit; cursor: pointer; transition: border-color var(--ds-motion-fast); }
.receiving-choice:hover { border-color: var(--ds-color-action-primary); }
.receiving-icon { display: grid; place-items: center; width: 56px; height: 56px; border-radius: var(--ds-radius-md); color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.receiving-copy { display: grid; gap: .45rem; }
.receiving-copy strong { font-size: 1.12rem; }
.receiving-copy small { color: var(--ds-color-text-secondary); font-size: .85rem; line-height: 1.8; }
.receiving-copy > span { font-size: .75rem; color: var(--ds-color-text-muted); }
.receiving-arrow { color: var(--ds-color-action-accent); }
.receiving-note { color: var(--ds-color-text-muted); font-size: .85rem; text-align: center; margin: 1.5rem 0; }
@media (max-width: 680px) { .receiving-grid { grid-template-columns: 1fr; gap: .75rem; } .receiving-choice { min-height: 120px; padding: 1.15rem 1rem; gap: .8rem; } }
</style>
