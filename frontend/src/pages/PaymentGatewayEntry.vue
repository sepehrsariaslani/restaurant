<template>
  <section class="payment-state-page" dir="rtl">
    <article class="payment-state-card">
      <p class="eyebrow">پرداخت آنلاین</p>
      <h1>پرداخت آنلاین هنوز فعال نیست</h1>
      <p>برای این سفارش، پرداخت در مرحله تحویل/شعبه/سر میز انجام می‌شود. اگر سفارش را ثبت کرده‌اید، می‌توانید وضعیت آن را پیگیری کنید.</p>
      <div class="payment-actions">
        <a class="primary-btn" :href="orderCode ? `/order-success/${encodeURIComponent(orderCode)}` : '/checkout'">{{ orderCode ? 'پیگیری سفارش' : 'بازگشت به تکمیل سفارش' }}</a>
        <a class="secondary-btn" href="/cart">بازگشت به سبد</a>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  boot: { type: Object, default: () => ({}) },
})

const orderCode = computed(() => {
  const fromBoot = String(props.boot.order_code || '').trim()
  if (fromBoot) return fromBoot
  const parts = window.location.pathname.replace(/^\/+|\/+$/g, '').split('/')
  return parts.length >= 2 && parts[parts.length - 2] === 'payment' ? parts[parts.length - 1] : ''
})
</script>

<style scoped>
.payment-state-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: var(--bg-soft);
}

.payment-state-card {
  width: min(460px, 100%);
  border-radius: 28px;
  background: #fff;
  box-shadow: var(--shadow-deep);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  padding: 1.4rem;
  text-align: right;
}

.eyebrow { color: var(--accent-green); font-weight: 800; margin: 0 0 .35rem; }
h1 { margin: 0; font-size: 1.45rem; }
p { color: var(--text-muted); line-height: 1.9; }
.payment-actions { display: grid; gap: .65rem; margin-top: 1rem; }
.primary-btn,
.secondary-btn {
  min-height: 46px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 850;
}
.primary-btn { background: var(--accent-green); color: #fff; }
.secondary-btn { border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / .16); color: var(--accent-green); }
</style>
