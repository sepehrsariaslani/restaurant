<template>
  <aside class="order-flow-sticky-summary" dir="rtl">
    <header>
      <p class="order-flow-eyebrow">مسیر سفارش</p>
      <h3>خلاصه سفارش شما</h3>
      <p>در هر مرحله بدانید سفارش برای کجاست، چه زمانی آماده می‌شود، چقدر هزینه دارد و قدم بعدی چیست.</p>
    </header>

    <div class="order-flow-summary-line">
      <span>سفارش برای کجاست؟</span>
      <strong>{{ destinationText }}</strong>
    </div>
    <div class="order-flow-summary-line">
      <span>چه زمانی؟</span>
      <strong>{{ timeText }}</strong>
    </div>
    <div class="order-flow-summary-line">
      <span>هزینه ارسال</span>
      <strong>{{ deliveryFeeText }}</strong>
    </div>
    <div class="order-flow-summary-line">
      <span>مرحله بعد</span>
      <strong>{{ nextStep }}</strong>
    </div>

    <slot />
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { cartState } from '@/stores/cartStore'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  nextStep: { type: String, default: 'انتخاب آیتم از منو' },
  currency: { type: String, default: 'IRR' },
})

const context = computed(() => cartState.orderContext || {})

const destinationText = computed(() => {
  const ctx = context.value
  if (ctx.order_type === 'dine_in') {
    return [ctx.branch_title || ctx.branch || 'شعبه نامشخص', ctx.table ? `میز ${ctx.table}` : 'بدون میز'].join(' · ')
  }
  if (ctx.order_type === 'pickup') {
    return ctx.branch_title || ctx.branch ? `تحویل از ${ctx.branch_title || ctx.branch}` : 'شعبه انتخاب نشده'
  }
  if (ctx.order_type === 'delivery') {
    const address = ctx.address || {}
    return address.title || address.address_line ? `ارسال به ${address.title || address.address_line}` : 'آدرس انتخاب نشده'
  }
  return 'نوع سفارش انتخاب نشده'
})

const timeText = computed(() => {
  const ctx = context.value
  if (ctx.order_type === 'pickup') {
    if (ctx.pickup_time_type === 'scheduled' && ctx.pickup_time) return `تحویل در ${ctx.pickup_time}`
    return ctx.prep_time_mins ? `آماده‌سازی حدود ${ctx.prep_time_mins} دقیقه` : 'هرچه سریع‌تر'
  }
  if (ctx.order_type === 'delivery') {
    if (ctx.delivery_time_type === 'scheduled' && ctx.delivery_time) return `ارسال در ${ctx.delivery_time}`
    if (ctx.eta_min && ctx.eta_max) return `${ctx.eta_min} تا ${ctx.eta_max} دقیقه`
    return 'زمان تحویل پس از انتخاب آدرس مشخص می‌شود'
  }
  if (ctx.order_type === 'dine_in') {
    return ctx.prep_time_mins ? `آماده سرو حدود ${ctx.prep_time_mins} دقیقه` : 'پس از تایید آشپزخانه'
  }
  return 'نامشخص'
})

const deliveryFeeText = computed(() => {
  const ctx = context.value
  if (ctx.order_type === 'delivery') return ctx.delivery_fee ? formatMoney(ctx.delivery_fee, props.currency) : 'پس از انتخاب آدرس'
  if (ctx.order_type === 'pickup') return 'بدون هزینه ارسال'
  if (ctx.order_type === 'dine_in') return 'بدون هزینه ارسال'
  return '-'
})
</script>
