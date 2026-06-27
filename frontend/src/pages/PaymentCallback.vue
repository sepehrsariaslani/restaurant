<template>
  <section class="payment-state-page" dir="rtl">
    <article class="payment-state-card">
      <p class="eyebrow">بازگشت از پرداخت</p>
      <h1>{{ isFailed ? 'پرداخت تایید نشد' : 'وضعیت پرداخت مشخص نیست' }}</h1>
      <p>درگاه آنلاین هنوز به‌صورت کامل فعال نیست. اگر سفارش ثبت شده، وضعیت سفارش شما محفوظ است و می‌توانید آن را پیگیری کنید.</p>
      <div class="payment-actions">
        <a class="primary-btn" :href="successUrl">پیگیری سفارش</a>
        <a class="secondary-btn" href="/checkout">بازگشت به تکمیل سفارش</a>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const params = new URLSearchParams(window.location.search || '')
const orderCode = computed(() => params.get('order') || params.get('order_code') || '')
const isFailed = computed(() => ['fail', 'failed', 'cancelled', 'error'].includes(String(params.get('status') || '').toLowerCase()))
const successUrl = computed(() => orderCode.value ? `/order-success/${encodeURIComponent(orderCode.value)}` : '/customer/orders')
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
